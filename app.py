from flask import Flask, render_template
import pandas as pd
import sqlite3

app = Flask(__name__)
db_path = 'repos.db'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)