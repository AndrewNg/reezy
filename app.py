# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, make_response, session
from flask_sslify import SSLify
from werkzeug.utils import secure_filename
import os, json, glob, io, uuid, sys, string, operator
import pytesseract
from wand.image import Image
from PIL import Image as PImage
from gtts import gTTS
from tempfile import TemporaryFile
import boto3
import pusher
import nltk
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)
app.config.update(
  PROPAGATE_EXCEPTIONS = True,
  MAX_CONTENT_LENGTH = 32 * 1024 * 1024,
  UPLOAD_FOLDER = './files'
)

if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
  sslify = SSLify(app)

# initialize pusher
pusher_client = pusher.Pusher(
  app_id=os.environ['PUSHER_APP_ID'],
  key=os.environ['PUSHER_KEY'],
  secret=os.environ['PUSHER_SECRET'],
  ssl=True
)

# initialize S3
session = boto3.Session(
    aws_access_key_id=os.environ['S3_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET']
)
client = session.client('s3')
s3 = session.resource('s3')
bucket = s3.Bucket('reezy')

session['id'] = 'null'

@app.route('/')
@app.route('/index')
def index():
  # channel for pusher
  session['id'] = str(uuid.uuid4())
  return render_template('index.html', pusher_key=os.environ['PUSHER_KEY'], session['id']=session['id'])

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
  # check if the post request has the file part
  if 'file' not in request.files:
    return json.dumps({'data':'sorry, no file'});
  # receiving file
  file = request.files['file']
  length = int(request.form['length'])//10

  # if user does not select file, browser also
  # submit a empty part without filename
  if file.filename == '':
    return json.dumps({'data':'name'});
  if file and allowed_file(file.filename):
    fname = secure_filename(file.filename)
    fname_without_extension = fname.split('.')[0]
    # reading pdf
    pusher_client.trigger(session['id'], 'my-event', {'message': 'uploading file', 'progress': 10})
    blob = file.read()

    pusher_client.trigger(session['id'], 'my-event', {'message': 'converting file', 'progress': 20})
    # converting
    req_image = []
    response_string = ""
    with Image(blob=blob, resolution=300) as img:
      with img.convert('png') as converted:
        pusher_client.trigger(session['id'], 'my-event', {'message': 'processing pdf', 'progress': 40})
        for single_img in converted.sequence:
          img_page = Image(image=single_img)
          req_image.append(img_page.make_blob('png'))
        pusher_client.trigger(session['id'], 'my-event', {'message': 'performing OCR', 'progress': 50})
        for final_img in req_image:
          response_string = response_string + pytesseract.image_to_string(PImage.open(io.BytesIO(final_img)).convert('RGB'))

  else:
    response_string = 'please only upload a pdf'

  # summarization
  pusher_client.trigger(session['id'], 'my-event', {'message': 'summarizing', 'progress': 60})
  response_string = summarize(response_string.replace('\n', ' '), length)

  # text to speech
  pusher_client.trigger(session['id'], 'my-event', {'message': 'converting to mp3', 'progress': 70})
  if len(response_string) != 0:
    tts = gTTS(text=response_string, lang='en')
    f = TemporaryFile()
    tts.write_to_fp(f)
    f.seek(0)
    # unique key to save
    unique_key = str(uuid.uuid4()) + '.mp3'
    bucket.put_object(Key=unique_key, Body=f)
  else:
    return json.dumps({'data':'', 'unique_url':'empty'});

  # let the user download it, expires after 20 minutes
  url = client.generate_presigned_url('get_object', Params={'Bucket': 'reezy', 'Key': unique_key, 'ResponseContentDisposition': 'attachment; filename=' + file.filename[:-4] + '.mp3'}, ExpiresIn=1200)

  pusher_client.trigger(session['id'], 'my-event', {'message': 'done!', 'progress': 100})

  return json.dumps({'data':response_string, 'unique_url':url});

# helper methods
def summarize(text, n):
  # process the text
  lower = text.lower()
  remover = str.maketrans('','',string.punctuation)
  words = lower.translate(remover)

  if len(words) == 0:
    return ""

  itertokens = {}
  itertokens['test'] = words

  # create tfidf vectorizer
  tfidf = TfidfVectorizer(tokenizer = tokenize, stop_words = nltk.corpus.stopwords.words('english'))
  weights = tfidf.fit_transform(itertokens.values())
  names = tfidf.get_feature_names()
  tfidfs = {}
  for item in weights.nonzero()[1]:
    tfidfs[names[item]] = weights[0,item]

  # split text into sentences
  sentences = nltk.tokenize.sent_tokenize(text)
  scores = {}
  for i in range(0,len(sentences)):
    scores[i] = get_score(sentences[i], tfidfs)
  sorts = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

  # select top n sentences (from user input)
  indices = []
  for i in range(0,n):
    indices.append(sorts[i][0]) # to protect from threading issues

  # output corresponding sentences
  output = ''
  sort_indices = sorted(indices)
  for index in sort_indices:
    output = output + sentences[index] + ' '

  return output

def stem(tokens, stemmer):
  stems = []
  for t in tokens:
    stems.append(stemmer.stem(t))
  return stems

def tokenize(text):
  stemmer = nltk.stem.snowball.SnowballStemmer("english") #, ignore_stopwords=True) # uses nltk stopwords
  tokens = nltk.word_tokenize(text.lower())
  stemmed = stem(tokens, stemmer)
  return stemmed

def get_score(sentence, tfidfs):
  remover = str.maketrans('','',string.punctuation)
  searchable = tokenize(sentence.translate(remover))
  filtered = [w for w in searchable if not w in nltk.corpus.stopwords.words('english')]
  sent_len = len(filtered)
  if sent_len != 0:
    score = 0.
    for word in filtered:
      if word not in tfidfs:
        print(word)
      else:
        score = score + tfidfs[word]
    return score/sent_len
  else:
    return 0

def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in set(['pdf'])

def store_file(file):
    s3 = boto3.resource('s3')
    # Upload a new file
    fname = secure_filename(file.filename)
    s3.Bucket('reezy').put_object(Key=fname, Body=file)

    return