from flask import Flask, render_template
import pandas as pd
import sqlite3

app = Flask(__name__)
db_path = 'database.db'

@app.route('/')
def index():
    return render_template('index.html')
