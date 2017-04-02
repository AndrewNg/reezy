from flask import Flask, render_template, request
from flask_sslify import SSLify
import os, json

app = Flask(__name__)
app.debug = True # for autoreload
if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
  sslify = SSLify(app)

@app.route('/')
@app.route('/index')
def index():
  return render_template('index.html')

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/status')
def status():
  return render_template('status.html')

# logic stuff here
@app.route('/process', methods=['GET', 'POST'])
def process():
   return json.dumps({'data':'ayy'});