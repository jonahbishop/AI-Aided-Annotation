#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import string

from flask import Flask, request, render_template, jsonify, session, url_for, redirect, send_file
from flask.json import dump
import time
import mmr
import secrets
import pymongo
import bcrypt
import random

# Support for gomix's 'front-end' and 'back-end' UI. 
app = Flask(__name__, static_folder='public', template_folder='views')
# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')
secret = secrets.token_urlsafe(32)
app.secret_key = secret


session_to_file_handle = {}

#connect to your Mongo DB database
client = pymongo.MongoClient()

#get the database name
db = client.get_database('total_records')
#get the particular collection that contains the data
records = db.register

#Use json_request(s) instead of request.json[s]. If you really need request.json, use json_request().
json_request = lambda s="" : request.json[s] if s else request.json

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
  """
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
  """
  # TODO: Make sure the following line is commented out (or delete these two lines)
  # return jsonify({"session_id": "session1", "sentences": ["blahp", "blorp"]})

  # !!!!!!
  # This is the input: it's just a string that represents the document
  # !!!!!!
  input_data = json_request('rawdocument')
  sessionID = int(time.time())
  sentences = mmr.tokenize_sentences(input_data)
  keyw_r = mmr.keyword_generator(sentences)
  # print('keywords: ', keyw_r['word'], keyw_r['score'])
  bad_sentences =[(sentences[i], i) for i in range(0, len(sentences))]#This seems like a bad way of doing this. Please change it, future Isaac
  # Output fields can go in "res"
  res = {
    "raw_document": input_data,
    "session_id": sessionID,
    "sentences": bad_sentences,
    "keywords": keyw_r,#list(keyw_r.apply(lambda x: (x["word"],x["score"]), axis = 1)), # done - maybe only limit to the top n keywords
  }

  if 'rawdocument' not in json_request():
    print("malformed '/upload' request!")
    return jsonify({})


  SESSIONS[sessionID] = {
    "raw_document": input_data,
    "sentences": bad_sentences,
    "keywords": keyw_r,
    #consider saving IDF?
    #save the processFile results?
  }
  print("number of sessions: ", len(SESSIONS))
  # print('keyword res:', res)

  return jsonify(res) #weird we send the document back and forth. Presumably, the front end already has it.


@app.route("/phase_two", methods=['POST'])
def phase_two():
  """
    This is a wrapper for _testable_phase_two. _testable_phase_two has parameters and return values that are easier to
    test server-side  .
    + Expects requests.json['session_id'] to be session_id as usual.
    + Expects requests.json['top_sentences'] to be a list of IDs for the top sentences.
        (IDs are the same as in the rank method)
    Return: A jsonified dictionary whose keys are the top_sentence's strings (Not their IDs) and whose values
       are the cloud sentences.
    Isaac's note: If you want the front-end to also receive the top_sentences similarity scores, that can be added
                  easily. Additionally, if we find that sending the full sentences is too much, I can convert them back
                  into sentence IDs before sending the packet.
  """
  return jsonify({"similar_sentences": _testable_phase_two(int(json_request('session_id')), json_request('top_sentences'))})


def _testable_phase_two(sessionID, top_sentence_IDs, n=mmr.N_SIM_SENTENCES):
  """
  :param sessionID: The integer sessionID
  :type sessionID: int
  :param top_sentence_IDs: The IDs for the sentences around which to generate the cloud_sentences
  :type top_sentence_IDs: [int]
  :param n: The number of cloud sentences to generate for each top_sentence. If you want this to be user-controlled,
            you can set that up in the shim. If you just want to change how many are generated without giving the user
            control, just change N_SIM_SENTENCES in mmr.py
  :type n: int
  :return: A dict mapping the strings of the top_sentences to the cloud strings
  :rtype: {str:[str]}
  """
  curr_session = SESSIONS[sessionID]
  all_sent_objs = mmr.processFile(sessionID, [pair[0] for pair in curr_session['sentences']])
  top_sentences = [all_sent_objs[x] for x in top_sentence_IDs]
  other_sentences = [all_sent_objs[x] for x in range(len(all_sent_objs)) if x not in top_sentence_IDs]
  sim_sentences = mmr.n_sim_sentences(top_sentences, other_sentences, all_sent_objs , n=n)
  print("Sim_sentences {str:[str]}:\n", sim_sentences)
  IDify = lambda sent : all_sent_objs.index(sent) if isinstance(sent, str) else list(map(IDify, sent)) #This works even though it's a str-sentence comparison because I
  #overrode sentence's __eq__
  sim_sentences = {IDify(key) : IDify(val) for key, val in sim_sentences.items()} #O(n) calls to O(n) IDify, could be
  #reduced to nlogn with an ID lookup table
  print("\nSim_sentences {int:[int]}:\n", sim_sentences)
  return sim_sentences


@app.route('/rank', methods=['POST'])
def rank():
  """
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
  """

  res = {}
  summary = []
  sentences = []
  sessionID = int(json_request('session_id'))
  keywords = json_request('keywords')
  summaryIDs = json_request('summary')
  curr_session = SESSIONS[sessionID]
  for i,j in curr_session["sentences"]:
    if j in summaryIDs:
      summary.append(i)
    else:
      sentences.append(i)
  print('summary', summary, summaryIDs)
  mmr_scores = mmr.summary_generator(sessionID, sentences, keywords, summary)
  # sent, mmr score, LH score, RH score

  for index, out in mmr_scores.iterrows():
    for se, s_id in curr_session["sentences"]:

      if out['sent'] == se:
        mmr_scores.at[index, 'sentID'] = int(s_id)

  # res = mmr_scores.loc[:, ["sentID", 'lscore', 'rscore', 'sent']];
  # res.set_index("sentID", inplace = True);
  # res.columns =  [ "LSimScr", "RSimScr", "sentence"];
  # res = res.to_dict()
  res = mmr_scores.to_json(orient ='index')
  print('pes', res)
  if not all(arg in json_request() for arg in ('session_id', 'keywords', 'summary')):
    print("Malformed request to '/rank' endpoint:", json_request())
    return jsonify({})

  # TODO: populate res with the scores for each sentence (excluding the summary sentences)
  return res
  # return jsonify(res)

@app.route("/generate_json", methods=["POST"])
def generate_json():
  """
  session_id: as usual
  cloud: {summary_sentences : [cloud_sentences, ...], ...}
  keywords: [keywordA, ...]
  jeopardy: [jeopardy_questions, ...]
  """
  sessionID = int(json_request("session_id"))
  full_sum = json_request("full_summary")
  keywords = json_request("keywords")
  jeop = json_request("jeopardy")
  if sessionID not in session_to_file_handle:
    session_to_file_handle[sessionID] = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
  handle = session_to_file_handle[sessionID]
  return jsonify({"handle": _generate_json(handle, full_sum, jeop, keywords)})
  # return {"handle": _generate_json(handle, full_sum, jeop, keywords)}


def _generate_json(handle, full_sum, jeopardy, keywords):
  filename = f"./exports/{handle}.json"
  dump({"Full Summary" : full_sum, "Jeopardy Questions" : jeopardy, "Keywords" : keywords}, open(filename, "w", encoding="utf-8"), ensure_ascii=False)
  return handle


@app.get("/download/<handle>")
def export(handle):
  return send_file(handle, as_attachment=True)


if __name__ == '__main__':
  app.run(debug=True)