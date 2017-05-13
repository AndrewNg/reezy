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
from tasks import make_celery
import base64
import pickle
import time

app = Flask(__name__)
app.config.update(
  PROPAGATE_EXCEPTIONS = True,
  MAX_CONTENT_LENGTH = 32 * 1024 * 1024,
  UPLOAD_FOLDER = './files',
  SECRET_KEY = 'oh so secret',
  CELERY_BROKER_URL=os.environ['REDIS_URL'],
  CELERY_RESULT_BACKEND=os.environ['REDIS_URL'],
  CELERY_TASK_SERIALIZER = 'pickle',
  CELERY_RESULT_SERIALIZER = 'json',
  CELERY_ACCEPT_CONTENT = ['json', 'pickle']
)

celery = make_celery(app)

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
aws_session = boto3.Session(
    aws_access_key_id=os.environ['S3_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET']
)
client = aws_session.client('s3')
s3 = aws_session.resource('s3')
bucket = s3.Bucket('reezy')

@app.route('/')
@app.route('/index')
def index():
  # channel for pusher
  session['id'] = str(uuid.uuid4())
  return render_template('index.html', pusher_key=os.environ['PUSHER_KEY'], session_id=session['id'])

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/status')
def status():
  return render_template('status.html')

# logic stuff here
# we now want to store in S3, not local files
@app.route('/process', methods=['GET', 'POST'])
def call_celery():
  # start
  text = request.form['text']
  session_id = session['id']
  files = request.files
  # check if the post request has the file part
  if len(text) != 0:
    form = request.form
    r = process.delay(text.encode(), None, form, session_id)
  if 'file' not in files:
      return json.dumps({'data':'empty'});


  file = files['file']
  filename = file.filename

  # if user does not select file, browser also
  # submit a empty part without filename
  if filename == '':
    return json.dumps({'data':'name'});

  file.stream.seek(0)
  file_contents = base64.b64encode(file.read())
  # file_contents = str(file.read())
  form = request.form
  r = process.delay(file_contents, filename, form, session_id)
  # while not r.ready():
  #   time.sleep(1)
  return 'success'

@celery.task()
def process(file, filename, form, session_id):
  length = int(form['length'])//8
  if filename != None:
    # receiving file
    f = base64.b64decode(file)

    if file and allowed_file(filename):
      fname = secure_filename(filename)
      fname_without_extension = fname.split('.')[0]
      # reading pdf
      pusher_client.trigger(session_id, 'my-event', {'message': 'uploading file', 'progress': 10})
      blob = f

      pusher_client.trigger(session_id, 'my-event', {'message': 'converting file', 'progress': 20})
      # converting
      req_image = []
      response_string = ""
      with Image(blob=blob, resolution=300) as img:
        with img.convert('png') as converted:
          pusher_client.trigger(session_id, 'my-event', {'message': 'processing pdf', 'progress': 40})
          for single_img in converted.sequence:
            img_page = Image(image=single_img)
            req_image.append(img_page.make_blob('png'))
            # if it's really big
            if len(req_image) > 20:
              pusher_client.trigger(session_id, 'done', {'data': 'big'})
              return
          pusher_client.trigger(session_id, 'my-event', {'message': 'performing OCR', 'progress': 50})
          for final_img in req_image:
            response_string = response_string + pytesseract.image_to_string(PImage.open(io.BytesIO(final_img)).convert('RGB'))

    else:
      response_string = 'please only upload a pdf'
  else:
    response_string = file

  # summarization
  pusher_client.trigger(session_id, 'my-event', {'message': 'summarizing', 'progress': 60})
  response_string = summarize(response_string.decode().replace('\n', ' '), length)

  # text to speech and regular text file storage
  pusher_client.trigger(session_id, 'my-event', {'message': 'converting to mp3', 'progress': 70})
  if len(response_string) != 0:
    f_text = TemporaryFile()
    f_text.write(response_string.encode())
    f_text.seek(0)
    tts = gTTS(text=response_string, lang='en')
    f_mp3 = TemporaryFile()
    tts.write_to_fp(f_mp3)
    f_mp3.seek(0)
    # unique key to save
    unique_key = str(uuid.uuid4())
    unique_mp3 = unique_key + '.mp3'
    unique_text = unique_key + '.txt'
    bucket.put_object(Key=unique_mp3, Body=f_mp3)
    cron_clear.apply_async(args=[unique_mp3], countdown=1800)
    bucket.put_object(Key=unique_text, Body=f_text)
    cron_clear.apply_async(args=[unique_text], countdown=1800)
    f_mp3.close()
    f_text.close()
  else:
    pusher_client.trigger(session_id, 'done', {'data':'', 'unique_url':'empty'})
    return

  # let the user download it, expires after 20 minutes
  if filename == None:
    filename = "summary"
  mp3_url = client.generate_presigned_url('get_object', Params={'Bucket': 'reezy', 'Key': unique_mp3, 'ResponseContentDisposition': 'attachment; filename=' + filename[:-4] + '.mp3'}, ExpiresIn=1200)
  text_url = client.generate_presigned_url('get_object', Params={'Bucket': 'reezy', 'Key': unique_text,'ResponseContentDisposition': 'attachment; filename=' + filename[:-4] + '.txt'}, ExpiresIn=1200)

  pusher_client.trigger(session_id, 'my-event', {'message': 'done!', 'progress': 100})

  pusher_client.trigger(session_id, 'done', {'data': 'done', 'mp3_url':mp3_url, 'text_url':text_url})

  return

# cron to clear out S3
@celery.task()
def cron_clear(key):
  client.delete_object(Bucket='reezy', Key=key)
  return

# helper methods for summarization
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
  stokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
  extra_abbrevs = ['ca','e.g','et al','etc','i.e','p.a','p.s','ps','r.i.p','hon','rev','assn','dept','est','fig','hrs','mt','no','oz','sq','abbr','adj','adv','obj','pl','poss','b.a','b.sc','m.a','m.d','b.c','r.s.v.p','a.s.a.p','e.t.a','b.y.o.b','d.i.y','blvd','rd','sgt','cl','capt','cf','comm','conf','conj','www','apr','deriv','eccl','esq','esp','freq','publ']
  stokenizer._params.abbrev_types.update(extra_abbrevs)
  sentences = stokenizer.tokenize(text)
  scores = {}
  for i in range(0,len(sentences)):
    if len(sentences[i].split(' ')) <= 5:
      scores[i] = 0
    else:
      scores[i] = get_score(sentences[i], tfidfs)
  sorts = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

  # handle edge case where requested n > actual n
  if(n > len(sentences)):
    return text

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