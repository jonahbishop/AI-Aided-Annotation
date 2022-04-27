import pymongo
from datetime import datetime
from bson.timestamp import Timestamp
from bson.objectid import ObjectId

"""
# Basic:
import mongo as db
sessionID = db.session_init()
chapData = <dict containing types that can be BSON encoded> #One key must be "full_text"
db.session_add_chapter(sessionID, chapData)

# Later you want to get back the value you had in chapData["sentences"] for the first chapData you added:
sentence_data = db.chap_get(sessionID, 0, "sentences")

Warning: The chapters collection is designed to reduce storage redundancy by merging identical 
texts from different users and sessions into a single document.* This is done with the indices 
initialized in setup_mongo() and with some asserts on the chapter data. This means that anything
user-specific like different chosen top sentences belongs in session
users
sh

*(see MongoDB documentation for database vs. collection vs. document). 



Is this overengineered? Is this underengineered? I have no idea. Too bad!

https://pymongo.readthedocs.io/en/stable/api/index.html
https://www.mongodb.com/docs/manual/introduction/
https://www.mongodb.com/docs/manual/reference/operator/update/
"""

_client = pymongo.MongoClient()

#In our database "AAA", we have a collection "sessions", and "chapters"
_db = _client.AAA #AI-Aided-Annotation

"""I got paranoid about limited storage resources taking down our app so 
I gave everything a TTL. Most likely, if this project is extended, a TTL
is undesirable. You're gonna want to just get enough storage."""
SESSION_TTL=3600*24 # 1 Day to live
TEXT_TTL=3600*24*3 #3 Days to live

_last_modified = lambda mapping={}: {"lastAccessDate" : datetime.now(), **mapping}

#This part's definitely way overengineered. I just never want to have to type an update operator more than once
_touch_update = {"$currentDate": {"lastAccessDate": True}}
def _touch(collection, id):
  collection.find_one_and_update({"_id" : id}, _touch_update)
_touch_session = lambda s_id : _touch(_db.sessions, s_id)
_touch_text = lambda t_id : _touch(_db.texts, t_id)
_touch_chapter_text = lambda s_id, c_num : _touch_text(_db.sessions.find_one({"_id": s_id})["chapters"][c_num]["full_text"])

def _text_insert(text):
  text_found = _db.texts.find_one({"full_text":text})
  if text_found is not None:
    _touch_text(text_found["_id"])
    return text_found["_id"]
  else:
    return _db.texts.insert_one(_last_modified({"full_text": text})).inserted_id

def session_init():
  """Creates a session document for you and returns a str ID to access it later
  return: A session_id for use in later functions"""
  return str(_db.sessions.insert_one(_last_modified({"chapters": []})).inserted_id)


def session_num_chapters(session_id):
  return len(_db.sessions.find_one({"_id":ObjectId(session_id)})["chapters"])
  

def session_add_chapter(session_id, chap_data):
  """Adds the data in chap_data to the chapters collection. Adds a reference to that chapter 
  to the "chapters" field of the session specified by session_id. If the full_text of a 
  chapter is the same as a chapter already in the chapters collection, it will instead add a
  reference to that chapter. Chapters are 0-indexed by insertion to a session. i.e. the first 
  chapter added to a session will be accessed with a 0 in other functions.
  
  session_id: The str session_id returned by session_init()
  chap_data: A dictionary whose contents should be BSON-encodable (see link). Must have a "full_text"
             key and all other contents must be exclusively dependent on full_text. See the warning 
             in the file header.
  *https://pymongo.readthedocs.io/en/stable/api/bson/index.html#bytes
  """
  session_oid = ObjectId(session_id)
  assert "full_text" in chap_data
  text_oid = _text_insert(chap_data["full_text"])
  embedded_chapter = {**chap_data, "full_text" : text_oid}
  print(f"s_id {session_id}\ntext_oid: {text_oid}")
  val = _db.sessions.find_one_and_update({"_id" : session_oid}, {"$push": {"chapters": embedded_chapter}, **_touch_update})
  assert(val is not None)

    
def session_set_chapter(session_id, chap_num, chap_data):
  """Overwrites a session's chapter with the new chapter in chap_data"""
  assert(chap_num < session_num_chapters(session_id))
  session_oid = ObjectId(session_id)
  if "full_text" in chap_data:
    text_oid = _text_insert(chap_data["full_text"])
    update = {**chap_data, "full_text":text_oid}
  else:
    update = chap_data
    _touch_chapter_text(session_oid, chap_num)
  assert(_db.sessions.find_one_and_update({"_id" : session_oid}, {"$set" : {f"chapters.{chap_num}": update}, **_touch_update}) is not None)
  

def session_put(session_id, field, val):
  assert(field not in ("lastAccessDate", "chapters")) #Former's private, latter has specific functions to access
  assert(not field.startswith("chapters"))
  session_oid = ObjectId(session_id)
  return _db.sessions.find_one_and_update({"_id":session_oid}, {"$set" : {field : val}, **_touch_update}) is not None


def session_get(session_id, field):
  assert(field not in ("lastAccessDate", "chapters")) #Former's private, latter has specific functions to access
  assert(not field.startswith("chapters"))
  session_oid = ObjectId(session_id)
  return _db.sessions.find_one_and_update({"_id": session_oid}, _touch_update)[field]

def chap_put(session_id, chap_num, field, val):
  assert(field != "lastAccessDate")
  assert(chap_num < session_num_chapters(session_id))
  session_oid = ObjectId(session_id)
  result = _db.sessions.update_one({"_id": session_oid}, {"$set": {f"chapters.{chap_num}.{field}" :val}, **_touch_update})
  assert(result is not None)

def chap_get(session_id, chap_num, field):
  assert(field != "lastAccessDate")
  assert(chap_num < session_num_chapters(session_id))
  session_oid = ObjectId(session_id)
  chapter = _db.sessions.find_one_and_update({"_id": session_oid}, _touch_update)["chapters"][chap_num]
  assert(field in chapter)
  value = chapter[field]
  if field == "full_text":
    value = _db.texts.find_one_and_update({"_id": value}, _touch_update)[field]
  return value
    
def _reset_indices():
  _db.texts.drop_indexes()
  _db.sessions.drop_indexes()
  
def setup_mongo(reindex = False, session_ttl=SESSION_TTL, text_ttl=TEXT_TTL):
  if reindex:
    _reset_indices()
  index_names = lambda coll : map(lambda s: s["name"], coll.list_indexes())
  if "sessionReaper" not in index_names(_db.sessions):
    _db.sessions.create_index("lastAccessDate", name="sessionReaper", sparse=True, expireAfterSeconds=session_ttl)
  if "textReaper" not in index_names(_db.texts):
    _db.texts.create_index([("lastAccessDate", pymongo.ASCENDING)], name="textReaper", sparse=True, expireAfterSeconds=text_ttl)
    _db.texts.create_index("full_text", unique=True, sparse=True)

def hard_reset():
  _db.drop_collection("texts")
  _db.drop_collection("sessions")
  _db.drop_collection("chapters")

setup_mongo() #This can be out here because it's safe and if it's unnecessary, then it does nothing quickly