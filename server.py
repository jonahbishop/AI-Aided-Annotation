#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, render_template, jsonify
from flask_restful import Resource, Api
import test
import re
import time
import pandas as pd
import mmr



# Support for gomix's 'front-end' and 'back-end' UI. 
app = Flask(__name__, static_folder='public', template_folder='views')
# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')



# SESSIONS maps a unique ID to all the saved information for a document,
# i.e. the parsed sentences, and whatever else we might need and don't
# want to recalculate.
SESSIONS = {}
# Here's an example of what SESSIONS might look like:
'''
SESSIONS = {
  "session_id1": {
     "raw_document": "TEXT_BLOB",
     "sentences": ["first sentence!", "second sentence.", ...],
     "keywords": [("keyword1", 143), ("keyword2", 391), ...],  # NOTE: I don't really know what this should look like
  },
}

rank = {
  "session_id1": {
     "sentence": {
       "ID": "12"
       "novelty_scr": "0.45"
       "sim_scr": "0.38"
     }
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
    # TODO: use index.html when we're done testing the API.
    # return render_template('api_test.html')
    return render_template('index.html')

    
@app.route("/home")
def home():
  return render_template('index.html')
    
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
  
  # document_id can be used as a session_ID too
  # document_id = request.json['doc_name'] + time.time()
  sessionID = int(time.time()) #what are we doing with the sessionID again?
  # input_file_path = '/public/data/'+document_id+'.json'
  # input_path = 'public/data/COVIDVaccine_article.txt'

  keyw_r, sentences = mmr.keyword_generator(input_data)
  print('keywords: ', keyw_r['word'], keyw_r['score'])
  # print(sentences)
  # Output fields can go in "res"
  res = {
    "session_id": sessionID,
    "sentences": sentences,
    "keywords": list(keyw_r.apply(lambda x: (x["word"],x["score"]), axis = 1)), # done - maybe only limit to the top n keywords
    "paragraph_breaks": "TODO",
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
  document = request.json['rawdocument']
  
  # do stuff!
    
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
  curr_session = SESSION
  res = {}
  summary = []
  mmr_scores = mmr_class.summary_generator(input_file_path, keywords, lambda_value, summary)
  # sent, mmr score, LH score, RH score
  print(mmr_scores['sent'], mmr_scores['score'], mmr_scores['lscore'], mmr_scores['rscore'])
  if not all(arg in request.json for arg in ('session_id', 'keywords', 'summary')):
    print("Malformed reuqest to '/rank' endpoint:", request.json)
    return jsonify({})
  
  # TODO: populate res with the scores for each sentence (excluding the summary sentences)
  
  return jsonify(res)
  

if __name__ == '__main__':
    app.run()