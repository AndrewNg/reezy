from flask import Flask, render_template
from flask_sslify import SSLify
import os

app = Flask(__name__)
if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)

@app.route('/')
@app.route('/index')
def index():
  return render_template('index.html')

@app.route('/status')
def status():
  return render_template('status.html')