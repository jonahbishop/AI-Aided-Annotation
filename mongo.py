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

*(see MongoDB documentation for database vs. collection vs. document). 

The purpose of this is to create persistent storage for 

Is this overengineered? Is this underengineered? I have no idea. Too bad!

https://pymongo.readthedocs.io/en/stable/api/index.html
https://www.mongodb.com/docs/manual/introduction/
https://www.mongodb.com/docs/manual/reference/operator/update/
"""

_client = pymongo.MongoClient()

#In our database "AAA", we have a collection "sessions", and "chapters"
_db = _client.AAA #AI-Aided-Annotation

"""I got paranoid about limited storage resources taking down our app so 
I gave everything a TTL(TimeToLive). Most likely, if this project is extended, a TTL
is undesirable. Enough storage is probably the better answer or a better 
eviction process."""
SESSION_TTL=3600*24 # 1 Day to live
TEXT_TTL=3600*24*3 #3 Days to live

_last_modified = lambda mapping={}: {"lastAccessDate" : datetime.now(), **mapping}

#This part's definitely way overengineered. I just never want to have to type an update operator more than once
#These are used in update calls to update lastAccessDate and stave off the TTL reapers
_touch_update = {"$currentDate": {"lastAccessDate": True}}
def _touch(collection, id):
  collection.find_one_and_update({"_id" : id}, _touch_update)
_touch_session = lambda s_id : _touch(_db.sessions, s_id)
_touch_text = lambda t_id : _touch(_db.texts, t_id)
_touch_chapter_text = lambda s_id, c_num : _touch_text(_db.sessions.find_one({"_id": s_id})["chapters"][c_num]["full_text"])

def _text_insert(text):
  """If the text already exists in the texts collection, just retrieve that object id and touch it. 
  Otherwise add it to the texts collection
  Returns an ObjectId that can be used to retrieve text from the db.texts collection"""
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
  """Returns len of chapters list"""
  return len(_db.sessions.find_one({"_id":ObjectId(session_id)})["chapters"])
  

def session_add_chapter(session_id, chap_data):
  """Adds the data in chap_data to the chapters collection Chapters are 0-indexed by
  insertion order per-session. i.e. the first chapter added to a session will be 
  accessed with a 0 in other functions.
  
  session_id: The str session_id returned by session_init()
  chap_data: A dictionary whose contents should be BSON-encodable (see link). Must have a "full_text"
             key.
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
  assert("full_text" in chap_data)
  session_oid = ObjectId(session_id)
  text_oid = _text_insert(chap_data["full_text"])
  update = {**chap_data, "full_text":text_oid}
  assert(_db.sessions.update_one({"_id" : session_oid}, {"$set" : {f"chapters.{chap_num}": update}, **_touch_update}) is not None)
  

def session_put(session_id, field, val):
  """Store some session data
  session_id: id provided by session_init
  field: The key to find the val with later
  val: The value to be stored"""
  assert(field not in ("lastAccessDate", "chapters")) #Former's private, latter has specific functions to access
  assert(not field.startswith("chapters"))
  session_oid = ObjectId(session_id)
  return _db.sessions.update_one({"_id":session_oid}, {"$set" : {field : val}, **_touch_update}) is not None


def session_get(session_id, field):
  """Retrieves session data inserted with session_put
  session_id: id provided by session_init
  field: The key used to store the value in session_put
  """
  assert(field not in ("lastAccessDate", "chapters")) #Former's private, latter has specific functions to access
  assert(not field.startswith("chapters"))
  session_oid = ObjectId(session_id)
  return _db.sessions.find_one_and_update({"_id": session_oid}, _touch_update)[field]

def chap_put(session_id, chap_num, field, val):
  """Store some chapter data
  session_id: id provided by session_init
  chap_num: The int specifying the 0-indexed chapter
  field: The key to find the val with later
  val: The value to be stored"""
  assert(field != "lastAccessDate")
  assert(chap_num < session_num_chapters(session_id))
  session_oid = ObjectId(session_id)
  result = _db.sessions.update_one({"_id": session_oid}, {"$set": {f"chapters.{chap_num}.{field}" :val}, **_touch_update})
  assert(result is not None)

def chap_get(session_id, chap_num, field):
  """Retrieve some chapter data
  session_id: id provided by session_init
  chap_num: The int specifying the 0-indexed chapter
  field: The key used previously to store the value in chap_put"""
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
  """A private function that drops the indices. This is required to change the TTLs. 
  I believe that it can be slow if the database is currently large, because it will
  require you to rebuild indices"""
  _db.texts.drop_indexes()
  _db.sessions.drop_indexes()
  
def setup_mongo(reindex = False, session_ttl=SESSION_TTL, text_ttl=TEXT_TTL):
  """ This is the call made to ensure that everything's in order. 
  reindex: If True, makes a call to _reset_indices. This is required if you want 
           the TTLs to be changed
  session_ttl: If reindex is True, then this will be the new TTL for session documents
  text_ttl: If reindex is True, then this will be the new TTL for text documents
  """
  if reindex:
    _reset_indices()
  index_names = lambda coll : map(lambda s: s["name"], coll.list_indexes())
  if "sessionReaper" not in index_names(_db.sessions):
    _db.sessions.create_index("lastAccessDate", name="sessionReaper", sparse=True, expireAfterSeconds=session_ttl)
  if "textReaper" not in index_names(_db.texts):
    _db.texts.create_index([("lastAccessDate", pymongo.ASCENDING)], name="textReaper", sparse=True, expireAfterSeconds=text_ttl)
    _db.texts.create_index("full_text", unique=True, sparse=True)

def hard_reset():
  """Drops the collections. Effectively resetting everything"""
  _db.drop_collection("texts")
  _db.drop_collection("sessions")

setup_mongo() #This can be out here because it's safe and if it's unnecessary, then it finishes quickly