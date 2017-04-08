from flask import Flask, render_template, request, redirect
from flask_sslify import SSLify
from werkzeug.utils import secure_filename
import os, json
import pytesseract
from wand.image import Image
from PIL import Image as PImage
from gtts import gTTS

app = Flask(__name__)
app.config.update(
  PROPAGATE_EXCEPTIONS = True,
  MAX_CONTENT_LENGTH = 32 * 1024 * 1024,
  UPLOAD_FOLDER = './files'
)
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
    return json.dumps({'data':'no file dumbass'});
  file = request.files['file']
  # if user does not select file, browser also
  # submit a empty part without filename
  if file.filename == '':
    return json.dumps({'data':'no file name dumbass'});
  if file and allowed_file(file.filename):
    fname = secure_filename(file.filename)
    fname_without_extension = fname.split('.')[0]
    path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    file.save(path_to_file)

    with Image(filename=path_to_file, resolution=300) as img:
      with img.convert('png') as converted:
        converted.save(filename=fname_without_extension + '.png')

    png = PImage.open(fname_without_extension + '.png')
    png.load()
    response_string = pytesseract.image_to_string(png)

  else:
    response_string = 'u didnt upload a pdf u liar'

  tts = gTTS(text=response_string, lang='en')
  tts.save('reezy.mp3')

  return json.dumps({'data':'the server thinks the file is: ' + response_string});

# helper methods
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in set(['pdf'])