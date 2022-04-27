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

Is this overengineered? Is this underengineered? I have no idea. Too bad!

https://pymongo.readthedocs.io/en/stable/api/index.html
https://www.mongodb.com/docs/manual/introduction/
https://www.mongodb.com/docs/manual/reference/operator/update/
"""

_client = pymongo.MongoClient()

#In our database "AAA", we have a collection "sessions", and "chapters"
_db = _client.AAA #AI-Aided-Annotation

"""I got paranoid about limited storage resources taking down our app so 
I gave everything a TTL. Most likely, if this project is extended, such a
short TTL is undesirable. You're gonna want to just get enough storage."""
SESSION_TTL=300
CHAP_TTL=3600

_last_modified = lambda mapping={}: {"lastAccessDate" : datetime.now(), **mapping}

#This part's definitely way overengineered. I just never want to have to type an update operator more than once
_touch_update = {"$currentDate": {"lastAccessDate": True}}
def _touch(collection, id):
  collection.find_one_and_update({"_id" : id}, _touch_update)
_touch_session = lambda s_id : _touch(_db.sessions, s_id)
_touch_chapter = lambda c_id : _touch(_db.chapters, c_id)


def session_init():
  """Creates a session document for you and returns a str ID to access it later"""
  return str(_db.sessions.insert_one(_last_modified({"chapters": []})).inserted_id)


def session_add_chapter(session_id, chap_data):
  """Adds the data in chap_data to the chapters collection. Adds a reference to that chapter 
  to the "chapters" field of the session specified by session_id. If the full_text of a 
  chapter is the same as a chapter already in the chapters collection, it will instead add a
  reference to that chapter. Chapters are 0-indexed by insertion to a session. i.e. the first 
  chapter added to a session will be accessed with a 0 in other functions.
  session_id: 
  """
  session_oid = ObjectId(session_id)
  chap_oid = _chap_insert(chap_data)
  print(f"s_id {session_id}\nchap_oid: {chap_oid}")
  val = _db.sessions.find_one_and_update({"_id" : session_oid}, {"$push": {"chapters": chap_oid}, **_touch_update})
  assert(val is not None)

def session_num_chapters(session_id):
  return len(_db.sessions.find_one({"_id":ObjectId(session_id)})["chapters"])
  
    
def session_set_chapter(session_id, chap_num, chap_data):
  """Overwrites a session's chapter with the new chapter in chap_data"""
  chap_oid = _chap_insert(chap_data)
  session_oid = ObjectId(session_id)
  l = len(_db.sessions.find_one({"_id" : session_oid})["chapters"])
  if chap_num == l:
    print(f"You can't use session_set_chap to set chapter #{chap_num} when there are only {l} chapters. Try adding")
  elif chap_num > l:
    print(f"You can't use session_set_chap to set chapter #{chap_num} when there are only {l} chapters")
  # Instead of the **touch_update, would be more readable as touch_session call followed by just the set
  # But I'm paranoid about database accesses being possibly expensive at-scale. 
  assert(_db.sessions.find_one_and_update({"_id" : session_oid}, {"$set" : {f"chapters.{chap_num}": chap_oid}, **_touch_update}) is not None)
  
def _chap_insert(chapter):
  """The invariant that db.chapters contains unique full_texts means that all data placed in the TODO"""
  assert("full_text" in chapter)
  check_chap = _db.chapters.find_one({"full_text" : chapter["full_text"]})
  if check_chap is not None:
    _touch_chapter(check_chap["_id"])
    return check_chap["_id"]
  else:
    return _db.chapters.insert_one(_last_modified(chapter)).inserted_id

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
  """The invariant that full_text be unique means that all the data in a chapter document
  must be unambiguously derived from the full_text. The data in a chapter's document should be write-once"""
  assert(field != "lastAccessDate")
  session_oid = ObjectId(session_id)
  chap_oid = _db.sessions.find_one_and_update({"_id": session_oid}, _touch_update)["chapters"][chap_num]
  assert(field not in _db.chapters.find_one({"_id":chap_oid})) #This is the write-once check
  assert(_db.chapters.find_one_and_update({"_id": chap_oid}, {"$set": {field:val}, **_touch_update}))

def chap_get(session_id, chap_num, field):
  assert(field != "lastAccessDate")
  session_oid = ObjectId(session_id)
  chap_oid = _db.sessions.find_one_and_update({"_id": session_oid}, _touch_update)["chapters"][chap_num]
  record = _db.chapters.find_one_and_update({"_id": chap_oid}, _touch_update)
  assert(record is not None)
  assert(field in record)
  value = record[field]
  return value
    
def setup_mongo(reindex = False, session_ttl=SESSION_TTL, chap_ttl=CHAP_TTL):
  if reindex:
    reset_indices()
  if "sessionReaper" not in _db.sessions.list_indexes():
    _db.sessions.create_index("lastAccessDate", name="sessionReaper", sparse=True, expireAfterSeconds=session_ttl)
  if "chapReaper" not in _db.chapters.list_indexes():
    # This sort order should enable efficient deletion by oldness if eventually want to get rid of the TTL 
    # and instead delete when drive fills up
    _db.chapters.create_index([("lastAccessDate", pymongo.ASCENDING)], name="chapReaper", sparse=True, expireAfterSeconds=chap_ttl)
    # db.chapters.create_index([("full_text", pymongo.HASHED)], sparse=True)
    _db.chapters.create_index("full_text", unique=True, sparse=True)

def reset_indices():
  # db.exports.drop_indexes()
  _db.sessions.drop_indexes()
  _db.chapters.drop_indexes()

def hard_reset():
  # db.drop_collection("exports")
  _db.drop_collection("sessions")
  _db.drop_collection("chapters")

setup_mongo() #This can be out here because it's safe and if it's unnecessary, then it does nothing quickly