from flask import Flask, render_template
import pandas as pd
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import seaborn as sns

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
db_path = os.path.join(BASE_DIR, 'instance', 'database.db')


def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            Role_ID TEXT, Industry TEXT,
            Human_Labor_Cost_hr REAL, Tokens_per_Human_Hour REAL,
            Inference_Cost_2026 REAL, Agent_Labor_Equivalent_Cost REAL,
            Substitution_Elasticity REAL, AI_Augmentation_Factor REAL,
            Automation_Risk_Index REAL, Hardware_CapEx_Sensitivity REAL,
            Regulatory_Moat REAL, Substitution_Year_Est INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insertar_datos():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registros")
    if cursor.fetchone()[0] == 0:
        df = pd.read_csv(os.path.join(BASE_DIR, 'data', 'labor_substitution.csv'))
        df.to_sql('registros', conn, if_exists='append', index=False)
    conn.close()

def obtener_df():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()
    df['Industry'] = df['Industry'].astype(str).str.strip().str.lower()
    industrias = ['government', 'healthcare', 'mlops', 'education', 'legal', 'finance']
    return df[df['Industry'].isin(industrias)]


def generar_graficos():
    df = obtener_df()
    if df.empty:
        return

    plt.figure()
    scatter = plt.scatter(
        df['Human_Labor_Cost_hr'],
        df['Agent_Labor_Equivalent_Cost'],
        s=df['Automation_Risk_Index'] * 1,
        c=df['Automation_Risk_Index'], 
        cmap='RdYlGn_r',
        alpha=0.7
    )
    plt.colorbar(scatter)
    plt.title("Costo humano vs IA")
    plt.savefig(os.path.join(STATIC_DIR, 'plots', 'g1.png'))
    plt.close()

    low  = df[df["Regulatory_Moat"] == "Low"]["AI_Augmentation_Factor"].values
    med  = df[df["Regulatory_Moat"] == "Med"]["AI_Augmentation_Factor"].values
    high = df[df["Regulatory_Moat"] == "High"]["AI_Augmentation_Factor"].values
 
    pivot_df = df.groupby(['Industry', 'Regulatory_Moat']).size().unstack(fill_value=0)
    pivot_df['Total'] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values(by='Total', ascending=False).drop(columns='Total')
    pivot_df = pivot_df[['Low', 'Med', 'High']]
    plt.figure(figsize=(14, 8))
    pivot_df.plot(kind='bar', stacked=True, color= sns.color_palette("magma"), ax=plt.gca(), edgecolor='white', linewidth=0.5)
    plt.xticks(rotation=45, ha='right')
    plt.show()
    plt.savefig(os.path.join(STATIC_DIR, 'plots', 'g2.png'))
    plt.close()

    
    ind_summary = (df.groupby('Industry')['Hardware_CapEx_Sensitivity'].mean().sort_values(ascending=True))
    
    plt.figure(figsize=(9, 6))
    bars = plt.barh(ind_summary.index, ind_summary.values, color= sns.color_palette("magma"),
                    edgecolor='white', linewidth=0.5)
    plt.xlabel('CapEx Sensitivity promedio')
    plt.title('Sensibilidad al CapEx de hardware por industria')
    for bar, val in zip(bars, ind_summary.values):
        plt.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
                 f'{val:.3f}', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, 'plots', 'g3.png'),bbox_inches= 'tight')
    plt.close()
    
    plt.figure(figsize=(10,6))
    plt.gca().set_axisbelow(True)

    df_violin = df.dropna(subset=['Substitution_Year_Est', 'Industry'])

    sns.violinplot(
        data=df_violin,
        x='Industry',
        y='Substitution_Year_Est',
        palette="magma",
        inner="quartile"
    )

    plt.title("Distribución de años de sustitución por industria")
    plt.xlabel("Industria")
    plt.ylabel("Año estimado de sustitución")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='-', alpha=0.5)
    plt.savefig(os.path.join(STATIC_DIR, 'plots', 'g4.png'), bbox_inches='tight')
    plt.close()

    industry_impact = df.groupby('Industry')['AI_Augmentation_Factor'].mean().sort_values(ascending=False).reset_index()

    plt.figure(figsize=(12, 7))
    sns.set_theme(style="whitegrid")

    barplot = sns.barplot(
        data=industry_impact, 
        x='AI_Augmentation_Factor', 
        y='Industry', 
        palette='magma'     
    )

    for index, value in enumerate(industry_impact['AI_Augmentation_Factor']):
        plt.text(value + 0.01, index, f'{value:.2f}', va='center', fontweight='bold')

    plt.title('Ranking de Impacto: Potencial de IA promedio por Industria', fontsize=15, fontweight='bold')
    plt.xlabel('Factor de Aumentación Promedio (0 a 1)', fontsize=12)
    plt.ylabel('Industria', fontsize=12)
    plt.xlim(0, 1.1)

    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, 'plots', 'g5.png'), bbox_inches='tight')
    plt.close()
    
    

    

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analisis')
def analisis():
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM registros", conn)
        conn.close()

        stats = {
            'promedio_costo_humano': round(df['Human_Labor_Cost_hr'].mean(), 2),
            'maximo_riesgo': round(df['Automation_Risk_Index'].max(), 2),
            'minimo_riesgo': round(df['Automation_Risk_Index'].min(), 2),
            'promedio_riesgo': round(df['Automation_Risk_Index'].mean(), 2),
        }

        return render_template('analisis.html', stats=stats)

    except Exception as e:
        return f"Error en analisis: {e}"


@app.route('/costos')
def costos():
    return render_template('costos.html')


@app.route('/riesgo')
def riesgo():
    return render_template('riesgo.html')


if __name__ == '__main__':
    init_db()
    insertar_datos()
    generar_graficos()
    app.run(debug=True)