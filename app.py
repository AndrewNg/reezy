from flask import Flask, render_template, request, redirect, make_response
from flask_sslify import SSLify
from werkzeug.utils import secure_filename
import os, json, glob, io
import pytesseract
from wand.image import Image
from PIL import Image as PImage
from gtts import gTTS
from tempfile import TemporaryFile
import boto3
# import pusher

app = Flask(__name__)
app.config.update(
  PROPAGATE_EXCEPTIONS = True,
  MAX_CONTENT_LENGTH = 32 * 1024 * 1024,
  UPLOAD_FOLDER = './files'
)

if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
  sslify = SSLify(app)

# initialize pusher
# pusher_client = pusher.Pusher(
#   app_id=os.environ['PUSHER_APP_ID'],
#   key=os.environ['PUSHER_KEY'],
#   secret=os.environ['PUSHER_SECRET'],
#   ssl=True
# )

# initialize S3
session = boto3.Session(
    aws_access_key_id=os.environ['S3_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET']
)
client = session.client('s3')
s3 = session.resource('s3')
bucket = s3.Bucket('reezy')

@app.route('/')
@app.route('/index')
def index():
  return render_template('index.html')
  # return render_template('index.html', pusher_key=os.environ['PUSHER_KEY'])

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/status')
def status():
  return render_template('status.html')

# logic stuff here
# we now want to store in S3, not local files
@app.route('/process', methods=['GET', 'POST'])
def process():
  # pusher_client.trigger('my-channel', 'my-event', {'message': 'hello world'})
  # check if the post request has the file part
  if 'file' not in request.files:
    return json.dumps({'data':'no file dumbass'});
  # receiving file
  file = request.files['file']
  # if user does not select file, browser also
  # submit a empty part without filename
  if file.filename == '':
    return json.dumps({'data':'no file name dumbass'});
  if file and allowed_file(file.filename):
    fname = secure_filename(file.filename)
    fname_without_extension = fname.split('.')[0]
    # reading pdf
    blob = file.read()

    # converting
    req_image = []
    response_string = ""
    with Image(blob=blob, resolution=300) as img:
      with img.convert('png') as converted:
        for single_img in converted.sequence:
          img_page = Image(image=img)
          req_image.append(img_page.make_blob('png'))
        for final_img in req_image:
          response_string = response_string + pytesseract.image_to_string(PImage.open(io.BytesIO(final_img)))

  else:
    response_string = 'u didnt upload a pdf u liar'

  # text to speech
  tts = gTTS(text=response_string, lang='en')
  f = TemporaryFile()
  tts.write_to_fp(f)
  f.seek(0)
  bucket.put_object(Key='reezy.mp3', Body=f)

  # let the user download it, expires after 20 minutes
  url = client.generate_presigned_url('get_object', Params={'Bucket': 'reezy', 'Key': 'reezy.mp3'}, ExpiresIn=1200)

  return json.dumps({'data':response_string, 'url':url});

# helper methods
def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in set(['pdf'])

def store_file(file):
    s3 = boto3.resource('s3')
    # Upload a new file
    fname = secure_filename(file.filename)
    s3.Bucket('reezy').put_object(Key=fname, Body=file)

    return