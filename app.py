from flask import Flask, render_template
import pandas as pd
import sqlalchemy

app = Flask(__name__)
db_path = 'database.db'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)