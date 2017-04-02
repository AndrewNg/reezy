from flask import Flask, render_template, request, flash, redirect
from flask_sslify import SSLify
from werkzeug.utils import secure_filename
import os, json

app = Flask(__name__)
app.debug = True # for autoreload
app.secret_key = 'not very secret' # not actually important, just for flash to work
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
  # check if the post request has the file part
  if 'file' not in request.files:
      flash('No file part')
      return json.dumps({'data':'no file dumbass'});
  file = request.files['file']
  # if user does not select file, browser also
  # submit a empty part without filename
  if file.filename == '':
    flash('No selected file')
    return json.dumps({'data':'no file name dumbass'});
  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
  else:
    filename = 'u didnt upload a pdf u liar'

  return json.dumps({'data':'the server thinks the file is: ' + filename});

# helper methods
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in set(['pdf'])