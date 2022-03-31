 #!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, render_template, jsonify, session, url_for, redirect
import time
import mmr
import secrets
import pymongo
import bcrypt

# Support for gomix's 'front-end' and 'back-end' UI. 
app = Flask(__name__, static_folder='public', template_folder='views')
# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')
secret = secrets.token_urlsafe(32)
app.secret_key = secret

#connect to your Mongo DB database
client = pymongo.MongoClient()
 
#get the database name
db = client.get_database('total_records')
#get the particular collection that contains the data
records = db.register

# SESSIONS maps a unique ID to all the saved information for a document,
# i.e. the parsed sentences, and whatever else we might need and don't
# want to recalculate.
SESSIONS = {}
# Here's an example of what SESSIONS might look like:
'''   
SESSIONS = {
  "session_id1": {
     "raw_document": "TEXT_BLOB", 
     "sentences": [("first sentence!", 0), ("second sentence.",1), ...], # (sentence, ID)
     "keywords": [("keyword1", 143), ("keyword2", 391), ...],  # NOTE: I don't really know what this should look like
  }, 
}

rank = {
     "sentence1_index": {
       "ID": "12"
       "text": "blah...."
       "lsim": "0.45"  
       "rsim": "0.38"
     },
}
'''
 
@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #check if email exists in database
        email_found = records.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            #encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('home'))
            else:
                if "email" in session:
                    return redirect(url_for("home"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)
 
#assign URLs to have a particular route 
@app.route("/register", methods=['post', 'get'])
def register():
    message = ''
    #if method post in index
    if "email" in session:
      return redirect(url_for("home"))
    if request.method == "POST":
      user = request.form.get("fullname")
      email = request.form.get("email")
      password1 = request.form.get("password1")
      password2 = request.form.get("password2")
      #if found in database showcase that it's found 
      user_found = records.find_one({"name": user})
      email_found = records.find_one({"email": email})
      if user_found:
          message = 'There already is a user by that name'
          return render_template('register.html', message=message)
      if email_found:
          message = 'This email already exists in database'
          return render_template('register.html', message=message)
      if password1 != password2:
          message = 'Passwords should match!'
          return render_template('register.html', message=message)
      else:
          #hash the password and encode it
          hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
          #assing them in a dictionary in key value pairs
          user_input = {'name': user, 'email': email, 'password': hashed}
          #insert it in the record collection
          records.insert_one(user_input)
          
          #find the new created account and its email
          user_data = records.find_one({"email": email})
          new_email = user_data['email']
          #if registered redirect to logged in as the registered user
          return render_template('index.html')
    return render_template('register.html')

@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('index.html', email=email)
    else:
        return redirect(url_for("login"))
 
@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('register.html')

@app.after_request
def apply_kr_hello(response):
    """Adds some headers to all responses."""

    # Let's see if this solves the cache issue...
    # Update: Maybe it did? If you change this file, I think
    # it resets the cache...
    # response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


  
@app.route('/')
def homepage():
    """Displays the homepage."""
    # TODO: use intro.html when we're done testing the API.
    # return render_template('api_test.html')
    # return render_template('index.html')
    return render_template('intro.html')

    
@app.route("/home")
def home(): 
  if "email" in session:
    email = session["email"]
    return render_template('index.html', email=email)
  else:
    return redirect(url_for("login"))
    
@app.route('/test')
def apitest():
  """Displays a page to test the API"""
  return render_template('api_test.html')

@app.route('/upload', methods=['POST'])
def upload():
  '''   
  Start a new session with a new document.
  
  Input:
    request.json['rawdocument']: contains the document's raw text
    
  Output JSON fields:
    session_id: A unique ID that should be used in subsequent "rank"
                requests, so that we can refer to sentences by their IDs
                instead of their full contents.
    sentences:  A mapping from a sentence ID to the complete sentence, including
                punctuation, but not including trailing spaces. IDs should be in order,
                like {0: 'sentence one.', 1: 'sentence two.'}. This could be a
                list or a dictionary
    keywords:   A list of (keyword, score) tuples extracted from the document.
                Score can be raw frequency, or whatever else, so long as it can
                be used to rank the keywords.
    paragraph_breaks: 
                OPTIONAL: if it's easy to do, it'd be great to have a list of
                all the sentence IDs that should have a paragraph break afterwards,
                i.e. the IDs of the last sentence of each paragraph.  
  '''
  # TODO: Make sure the following line is commented out (or delete these two lines)
  # return jsonify({"session_id": "session1", "sentences": ["blahp", "blorp"]})
  
  res = {}
  
  # !!!!!!
  # This is the input: it's just a string that represents the document
  # !!!!!!
  input_data = request.json['rawdocument']
  sessionID = int(time.time()) 
  keyw_r, sentences = mmr.keyword_generator(input_data)
  # print('keywords: ', keyw_r['word'], keyw_r['score'])

  # Output fields can go in "res"
  res = {
    "raw_document": input_data,
    "session_id": sessionID,
    "sentences": sentences,
    "keywords": list(keyw_r.apply(lambda x: (x["word"],x["score"]), axis = 1)), # done - maybe only limit to the top n keywords
  }
  
  if 'rawdocument' not in request.json:
    print("malformed '/upload' request!")
    return jsonify({})
  
  
  SESSIONS[sessionID] = {
     "raw_document": input_data,
     "sentences": sentences,
     "keywords": keyw_r,  
  }
  print("number of sessions: ", len(SESSIONS))
  # print('keyword res:', res)
    
  return jsonify(res)




@app.route('/rank', methods=['POST'])
def rank():
  '''
  Rank sentences from an existing session.
  
  Inputs from request.json:
    'session_id': The session_id to get the right sentence mapping.
    'keywords':   A list of the keywords to use in ranking.
    'summary':    A list of IDs of the sentences currently in the summary.
  
  Outputs JSON fields:
    'scores': A mapping from sentence ID to "Score" (see below)
  
  Ideally, it'd be great to have the following information in "Score":
    - The score from the left-hand side of the MMR equation (i.e. query relevance)
      - The individual contributions of each keyword to the above score.
    - The score from the right-hand side of the MMR equation (i.e. difference from summary)
      - The ID of the argmax summary sentence
      - The individual keyword contributions
      
  If it's too much of a pain to get the keyword contributions, we can
  just return:  
    - The LH score (i.e. query relevance)
    - The RH score (i.e. summary difference)
  
  Of course, we can also take lambda as an argument, and then just
  return the raw score for each sentence. But: this limits what we can
  visualize on the front-end.
  '''
  
  res = {}
  summary = []
  sentences = []
  sessionID = int(request.json['session_id'])
  keywords = request.json['keywords']
  summaryIDs = request.json['summary']
  curr_session = SESSIONS[sessionID]
  for i,j in curr_session["sentences"]:
    if j in summaryIDs:
      summary.append(i)
    else:
      sentences.append(i)
  print('summary', summary, summaryIDs)
  mmr_scores = mmr.summy_generator(sessionID, sentences, keywords, summary)
  # sent, mmr score, LH score, RH score
  
  for index, out in mmr_scores.iterrows():
    for se, id in curr_session["sentences"]:
      
      if out['sent'] == se:
        mmr_scores.at[index, 'sentID'] = int(id)
  
  # res = mmr_scores.loc[:, ["sentID", 'lscore', 'rscore', 'sent']];
  # res.set_index("sentID", inplace = True);
  # res.columns =  [ "LSimScr", "RSimScr", "sentence"];
  # res = res.to_dict()
  res = mmr_scores.to_json(orient ='index')
  print('pes', res)
  if not all(arg in request.json for arg in ('session_id', 'keywords', 'summary')):
    print("Malformed reuqest to '/rank' endpoint:", request.json)
    return jsonify({})
  
  # TODO: populate res with the scores for each sentence (excluding the summary sentences)
  return res
  # return jsonify(res)