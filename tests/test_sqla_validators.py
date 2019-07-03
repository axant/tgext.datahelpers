from formencode import Invalid
from nose.tools import raises
from .sqla_base import setup_database, clear_database, DBSession, Thing
from tgext.datahelpers.validators import SQLAEntityConverter

def setup():
    setup_database()

class TestSQLAEntityConverter(object):
    def __init__(self):
        self.validator = SQLAEntityConverter(Thing, DBSession)
        self.slug_validator = SQLAEntityConverter(Thing, DBSession, slugified=True)

    def setup(self):
        clear_database()

    def test_found_entity(self):
        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.validator.to_python(1)
        assert x
        assert x.name == u'Bar'

    @raises(Invalid)
    def test_notfound_entity(self):
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.validator.to_python(5)

    @raises(Invalid)
    def test_missing_entity(self):
        self.validator.to_python(None)

    def test_string_id(self):
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.validator.to_python('1')
        assert x
        assert x.name == u'Bar'

    @raises(Invalid)
    def test_not_an_id(self):
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.validator.to_python('asd')

    def test_found_with_slug(self):
        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.slug_validator.to_python('foo-1')
        assert x
        assert x.name == u'Bar'

    def test_found_slugified_without_slug(self):
        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.slug_validator.to_python('1')
        assert x
        assert x.name == u'Bar'

    def test_found_slugified_on_int(self):
        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

        x = self.slug_validator.to_python(1)
        assert x
        assert x.name == u'Bar'

    def test_reversible(self):
        t2 = Thing(uid=1, name=u'Bar')
        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(t2)
        DBSession.flush()

        oid = self.validator.from_python(self.validator.to_python(1))
        assert oid == t2.uid

        x = self.validator.to_python(oid)
        assert x
        assert x.name == 'Bar'
