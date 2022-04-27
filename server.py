#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TODO: Split into Http-facing server and core methods files
import os
import string

from flask import Flask, request, render_template, jsonify, session, url_for, redirect, send_file, session
from flask.json import dumps
# from flask.ext.mongo_sessions import Mon
import time
import mmr
import secrets
import pymongo
import bcrypt
import random
import mongo as db

# Support for gomix's 'front-end' and 'back-end' UI. 
app = Flask(__name__, static_folder='public', template_folder='views')
# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')
secret = secrets.token_urlsafe(32)
app.secret_key = secret

#Use json_request(s) instead of request.json[s]. If you really need request.json, use json_request().
json_request = lambda s="" : request.json[s] if s else request.json


# SESSIONS maps a unique ID to all the saved information for a document,
# i.e. the parsed sentences, and whatever else we might need and don't
# want to recalculate.
# SESSIONS = {}
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
  return render_template('intro.html')


@app.route("/home")
def home():
  return render_template('index.html')

@app.route('/test')
def apitest():
  """Displays a page to test the API"""
  return render_template('api_test.html')

@app.post('/upload')
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
  if 'full_text' not in json_request():
    print("malformed '/upload' request!")
    return jsonify({})
  sessionID = db.session_init()
  input_data = json_request('full_text')
  sentences = mmr.tokenize_sentences(input_data)
  keyw_r = mmr.keyword_generator(sentences)
  # print('keywords: ', keyw_r['word'], keyw_r['score'])
  bad_sentences =[(sentences[i], i) for i in range(0, len(sentences))] #This seems like a bad way of doing this. Please change it, future me
  chap_data = {
    "full_text": input_data,
    "sentences": sentences,
    "keywords": keyw_r
  }
  res = {**chap_data, "session_id": sessionID} 
  res["sentences"] = bad_sentences
  #consider saving IDF?
  #save the processFile results?
  
  db.session_add_chapter(sessionID, chap_data)
  
  #Full chapter capabilities would send back {**chap_data, "session_id"}
  #I send this back for compatibility with single-chapter front-end
  # chap_data["raw_document"] = chap_data["full_text"]
  # del chap_data["full_text"]
  

  # print("number of sessions: ", len(SESSIONS)) #No longer keeps track of this
  # print('keyword res:', res)

  return jsonify(res) #weird we send the whole document back and forth. Presumably, the front end already has it.


@app.post("/phase_two")
def phase_two(): #TODO Rename to something more descriptive
  #TODO: Redo documentation to reflect current state of the function
  """
    This is a wrapper for _testable_phase_two. _testable_phase_two has parameters and return values that are easier to
    test server-side  .
    + Expects requests.json['session_id'] to be session_id as usual.
    + Expects requests.json['top_sentences'] to be a list of IDs for the top sentences.
        (IDs are the same as in the rank method)
    Return: A jsonified dictionary whose keys are the top_sentence's IDs and whose values are the cloud sentences'.
  """
  sim_sentences, keywords = _testable_phase_two(json_request('session_id'), json_request('top_sentences'), json_request('num_similar_sentences'))
  return jsonify({"similar_sentences": sim_sentences, "keywords" : keywords})


def _testable_phase_two(sessionID, top_sentence_IDs, n=mmr.N_SIM_SENTENCES):
  #TODO: Fix documentation
  """
  :param sessionID: The integer sessionID
  :type sessionID: int
  :param top_sentence_IDs: The IDs for the sentences around which to generate the cloud_sentences
  :type top_sentence_IDs: list of int
  :param n: The number of cloud sentences to generate for each top_sentence. If you want this to be user-controlled,
            you can set that up in the shim. If you just want to change how many are generated without giving the user
            control, just change N_SIM_SENTENCES in mmr.py
  :type n: int
  :return: A dict mapping the strings of the top_sentences to the cloud strings
  :rtype: dict[str, list[str]]
  """
  curr_sentences = db.chap_get(sessionID, 0, "sentences")
  all_sent_objs = mmr.process_file(sessionID, curr_sentences)
  top_sentences = [all_sent_objs[x] for x in top_sentence_IDs]
  other_sentences = [all_sent_objs[x] for x in range(len(all_sent_objs)) if x not in top_sentence_IDs]
  sim_sentences = mmr.n_sim_sentences(top_sentences, other_sentences, all_sent_objs , n=n)
  print("Sim_sentences {str:[str]}:\n", sim_sentences)
  IDify = lambda sent : all_sent_objs.index(sent) if isinstance(sent, str) else list(map(IDify, sent)) #This works even though it's a str-sentence comparison because I
  #overrode sentence's __eq__
  keywords = mmr.keyword_generator(sim_sentences)
  sim_sentences = {IDify(key) : IDify(val) for key, val in sim_sentences.items()} #O(n) calls to O(n) IDify, could be
  #reduced to nlogn with an ID lookup table
  print("\nSim_sentences {int:[int]}:\n", sim_sentences)
  return sim_sentences, keywords


@app.post('/rank')
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
  sessionID = json_request('session_id')
  keywords = json_request('keywords')
  summaryIDs = json_request('summary')
  curr_sentences = db.chap_get(sessionID, 0, "sentences")
  for i, s in enumerate(curr_sentences):
    if i in summaryIDs:
      summary.append(s)
    else:
      sentences.append(s)
  print('summary', summary, summaryIDs)
  mmr_scores = mmr.summary_generator(sessionID, sentences, keywords, summary)
  for index, out in mmr_scores.iterrows():
    for sent_id, sent in enumerate(curr_sentences):
      if out['sent'] == sent:
        mmr_scores.at[index, 'sentID'] = sent_id
  res = mmr_scores.to_json(orient ='index')
  print('pes', res)
  if not all(arg in json_request() for arg in ('session_id', 'keywords', 'summary')):
    print("Malformed request to '/rank' endpoint:", json_request())
    return jsonify({})
  return res


@app.route("/generate_json", methods=["POST"])
def generate_json():
  """
  session_id: as usual
  full_summmary: {summary_sentences : [cloud_sentences, ...], ...}
  keywords: [keywordA, ...]
  jeopardy: [jeopardy_questions, ...]
  """
  sessionID = json_request("session_id")
  full_sum = json_request("full_summary")
  keywords = json_request("keywords")
  jeop = json_request("jeopardy")
  # if sessionID not in session_to_file_handle:
  #   session_to_file_handle[sessionID] = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
  # handle = session_to_file_handle[sessionID]
  return jsonify({"handle": _generate_json(handle, full_sum, jeop, keywords)})
  # return {"handle": _generate_json(handle, full_sum, jeop, keywords)}


def _generate_json(full_sum, jeopardy, keywords):
  return dumps({"summary" : full_sum, "keywords" : keywords, "questionsAndAnswers" : jeopardy}, ensure_ascii=False)


@app.get("/download/<handle>")
def export(handle):
  return send_file(f"./exports/{handle}.json", as_attachment=True)


if __name__ == '__main__':
  print("main")
  db.hard_reset()
  db.setup_mongo(True)
  app.run(debug=True)