from flask import Flask, render_template
import pandas as pd
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import os
matplotlib.use("Agg")

app = Flask(__name__)
db_path = 'instance/database.db'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            Role_ID TEXT,
            Industry TEXT,
            Human_Labor_Cost_hr REAL,
        )
    ''')
    conn.commit()
    conn.close()

def insertar_datos():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registros")
   
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/datos')
def datos():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()
    return df.to_json(orient='records') 


if __name__ == '__main__':
    init_db()
    insertar_datos()
    app.run(debug=True)
    
