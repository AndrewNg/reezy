from app import db

class Conversion(db.Model):
  __tablename__ = 'conversions'

  id = db.Column(db.Integer, primary_key = True)
  submission_type = db.Column(db.Integer)
  filename = db.Column(db.String())
  filesize = db.Column(db.Integer)
  sentence_length = db.Column(db.Integer)
  requested_length = db.Column(db.Integer)


  def __init__(self, submission_type, filename, filesize, sentence_length, requested_length):
    self.type = submission_type
    self.filename = filename
    self.filesize = filesize
    self.sentence_length = sentence_length
    self.requested_length = requested_length

  def __repr__(self):
    return '<id {}>'.format(self.id)