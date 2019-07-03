# -*- coding: utf-8 -*-
from tg.exceptions import HTTPNotFound
from nose.tools import raises
from .sqla_base import setup_database, clear_database, DBSession, Thing

def setup():
    setup_database()

from tgext.datahelpers.utils import slugify, fail_with

class TestSlugify(object):
    def setup(self):
        clear_database()

        DBSession.add(Thing(uid=2, name=u'Foo'))
        DBSession.add(Thing(uid=1, name=u'Bar'))
        DBSession.flush()

    def test_slugify(self):
        thing = DBSession.query(Thing).get(1)
        slug = slugify(thing, thing.name)
        assert slug == 'bar-1', slug

    def test_slugify_unicode(self):
        thing = DBSession.query(Thing).get(2)
        slug = slugify(thing, u'This is a very long àèìòù phrase ')
        assert slug == 'this-is-a-very-long-aeiou-phrase-2', slug

    def test_slugify_unicode_ignore(self):
        thing = DBSession.query(Thing).get(2)
        slug = slugify(thing, u'This is a very long ’”««¡≠€∂ß phrase ')
        assert slug == 'this-is-a-very-long-phrase-2', slug

class TestFailWith(object):
    @raises(HTTPNotFound)
    def test_fail_with(self):
        fail_with(404)()

    @raises(HTTPNotFound)
    def test_fail_with_args(self):
        fail_with(404)(1,2,3, x=5)
