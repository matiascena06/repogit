from flask import Flask, render_template
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, 'instance', 'database.db')

INDUSTRIAS = ['Government', 'Healthcare', 'Finance', 'MLOps', 'Education', 'Legal']

columnas_numericas = [
        'Human_Labor_Cost_hr', 'Tokens_per_Human_Hour', 'Inference_Cost_2026',
        'Agent_Labor_Equivalent_Cost', 'Substitution_Elasticity', 'AI_Augmentation_Factor',
        'Automation_Risk_Index', 'Hardware_CapEx_Sensitivity', 'Substitution_Year_Est'
    ]


def init_db():
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            Role_ID TEXT,
            Industry TEXT,
            Human_Labor_Cost_hr REAL,
            Tokens_per_Human_Hour REAL
        )
    ''')

    conn.commit()
    conn.close()

def promedios_numericos():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_promedios = df.groupby('Industry')[columnas_numericas].mean().round(2)

    return df_promedios

def cargar_datos():
    conn = sqlite3.connect(DB)

    df = pd.read_csv('data/labor_substitution.csv')
    df = df[['Role_ID', 'Industry', 'Human_Labor_Cost_hr', 'Tokens_per_Human_Hour', 'Inference_Cost_2026' , 'Agent_Labor_Equivalent_Cost', 'Substitution_Elasticity', 'AI_Augmentation_Factor', 'Automation_Risk_Index', 'Hardware_CapEx_Sensitivity', 'Regulatory_Moat', 'Substitution_Year_Est']]
    df = df[df['Industry'].isin(INDUSTRIAS)]

    df.to_sql('registros', conn, if_exists='replace', index=False)
    conn.close()

def grafico_mayor_costo_horario():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()
    
    df_top = df.sort_values(by='Human_Labor_Cost_hr', ascending=False).head(10)

    plt.figure(figsize=(10,5))
    plt.bar(df_top['Role_ID'], df_top['Human_Labor_Cost_hr'])
    plt.xticks(rotation=45, ha='right')
    plt.title("Top 10 trabajos con mayor costo laboral")

    os.makedirs('static', exist_ok=True)
    plt.savefig('static/grafico1.png', bbox_inches='tight')
    plt.close()

def costo_promedio_horario_por_industria():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    df_group = df.groupby('Industry')['Human_Labor_Cost_hr'].mean().sort_values(ascending=False)

    plt.figure(figsize=(10,5))
    df_group.plot(kind='bar')
    plt.title("Costo promedio por industria")

    plt.savefig('static/grafico2.png', bbox_inches='tight')
    plt.close()

def grafico_reemplazo_tiempo():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    df = df.dropna(subset=['Substitution_Year_Est', 'Industry'])

    plt.figure(figsize=(10,6))
    plt.gca().set_axisbelow(True)
    sns.violinplot(data=df, x='Industry', y='Substitution_Year_Est', palette = "coolwarm", inner = "quartile")
    plt.title("Distribución de años de sustitución por industria")
    plt.xlabel("Industria")
    plt.ylabel("Año estimado de sustitución")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='-', alpha=0.5)

    plt.savefig('static/grafico3.png', bbox_inches='tight')
    plt.close()

def generar_grafico_costo_comparacion():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    df_sample = df.head(10)

    x = range(len(df_sample))

    plt.figure(figsize=(10,5))
    plt.bar(x, df_sample['Human_Labor_Cost_hr'], width=0.4, label='Humano')
    plt.bar([i + 0.4 for i in x], df_sample['Agent_Labor_Equivalent_Cost'], width=0.4, label='IA')

    plt.xticks([i + 0.2 for i in x], df_sample['Role_ID'], rotation=45, ha='right')
    plt.legend()
    plt.title("Costo humano vs IA")

    plt.savefig('static/grafico4.png', bbox_inches='tight')
    plt.close()

def obtener_datos_index():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    promedios = promedios_numericos()

    tabla = promedios.to_html(classes='tabla')
    promedio_general = round(promedios['Human_Labor_Cost_hr'].mean(), 2)
    maximo = round(promedios['Human_Labor_Cost_hr'].max(), 2)
    minimo = round(promedios['Human_Labor_Cost_hr'].min(), 2)

    return tabla, promedio_general, maximo, minimo


@app.route('/')
def index():
    tabla, promedio, maximo, minimo = obtener_datos_index()
    return render_template(
        'index.html',
        tabla=tabla,
        promedio=promedio,
        maximo=maximo,
        minimo=minimo
    )
    
    
if __name__ == '__main__':
    init_db()
    cargar_datos()
    grafico_mayor_costo_horario()
    costo_promedio_horario_por_industria()
    grafico_reemplazo_tiempo()
    generar_grafico_costo_comparacion()
    app.run(debug=True)
    