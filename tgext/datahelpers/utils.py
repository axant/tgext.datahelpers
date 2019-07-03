from tg import abort
import re, unicodedata

def object_primary_key(entity):
    if hasattr(entity, '_id'):
        #mongodb object use _id as the primary key
        return '_id'
    else:
        #multiple primary keys are currently not supported
        return entity.__mapper__.primary_key[0].key

def slugify(entity, value):
    entity_id = getattr(entity, object_primary_key(entity))

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)

    return '%s-%s' % (value, entity_id)

class fail_with(object):
    def __init__(self, code):
        self.code = code

    def __call__(self, *args, **kw):
        abort(self.code)

class MarkupString(unicode):
    def __html__(self):
        return self

