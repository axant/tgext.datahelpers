import ming
from ming.datastore import create_datastore
from ming import Session
from ming import schema as s
from ming.odm import ThreadLocalORMSession, FieldProperty, Mapper
from ming.odm.declarative import MappedClass
from datetime import datetime

mainsession = Session()
DBSession = ThreadLocalORMSession(mainsession)

database_setup = False
bind = None

def setup_database():
    global bind, database_setup
    if not database_setup:
        bind = create_datastore('mim:///test')
        mainsession.bind = bind
        ming.odm.Mapper.compile_all()
        database_setup = True

def clear_database():
    global engine, database_setup
    if not database_setup:
        setup_database()

class Thing(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'thing'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String)

class ThingWithDate(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'thing'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String)
    updated_at = FieldProperty(s.DateTime, if_missing=datetime.now)
