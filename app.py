from flask import Flask, render_template
import pandas as pd
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

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
    plt.scatter(df['Human_Labor_Cost_hr'], df['Agent_Labor_Equivalent_Cost'])
    plt.title("Costo humano vs IA")
    plt.xlabel("Costo humano/hr")
    plt.ylabel("Costo IA")
    plt.savefig(os.path.join(STATIC_DIR, 'g1.png'))
    plt.close()

    plt.figure()
    df.groupby('Industry')['Automation_Risk_Index'].mean().plot(kind='bar')
    plt.title("Riesgo por industria")
    plt.savefig(os.path.join(STATIC_DIR, 'g2.png'))
    plt.close()

    plt.figure()
    df.groupby('Substitution_Year_Est')['Automation_Risk_Index'].mean().plot()
    plt.title("Reemplazo en el tiempo")
    plt.savefig(os.path.join(STATIC_DIR, 'g3.png'))
    plt.close()

    plt.figure()
    df['Industry'].value_counts().plot(kind='pie')
    plt.title("Distribución por industria")
    plt.ylabel("")
    plt.savefig(os.path.join(STATIC_DIR, 'g4.png'))
    plt.close()

    plt.figure()



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graficos')
def graficos():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM registros LIMIT 10", conn)
    conn.close()
    stats = {
        'promedio_costo_humano': round(df['Human_Labor_Cost_hr'].mean(), 2),
        'maximo_riesgo': round(df['Automation_Risk_Index'].max(), 2),
        'minimo_riesgo': round(df['Automation_Risk_Index'].min(), 2),
        'promedio_riesgo': round(df['Automation_Risk_Index'].mean(), 2),
    }

    return render_template('graficos.html', stats=stats)

if __name__ == '__main__':
    init_db()
    insertar_datos()
    generar_graficos()
    app.run(debug=True)