from nose.tools import raises
from tgext.datahelpers.caching import entitycached, CacheKey
from .ming_base import setup_database as  ming_setup_database, clear_database as ming_clear_database,\
    Thing as MingThing, ThingWithDate as MingThingWithDate
from .sqla_base import setup_database as sqla_setup_database, clear_database as sqla_clear_database,\
    Thing as SqlaThing, ThingWithDate as SqlaThingWithDate, DBSession as SqlaDBSession
from datetime import datetime
import tg
from sqlalchemy.orm.exc import DetachedInstanceError

class TestNameSpaceGeneration(object):
    def test_namespace_for_function(self):
        @entitycached('entity')
        def function(entity):
            return 'HI'
        namespace = function.__entitycached__._determine_namespace(function)
        assert namespace == 'tests.test_entitycached--function', namespace

    def test_namespace_for_method(self):
        class Object(object):
            @entitycached('entity')
            def method(self, entity):
                return 'HI'
        o = Object()
        namespace = o.method.__entitycached__._determine_namespace(o.method)
        assert namespace == 'tests.test_entitycached-Object-method', namespace

    def test_namespace_for_staticmethod(self):
        class Object(object):
            @staticmethod
            @entitycached('entity')
            def method(entity):
                return 'HI'
        o = Object()
        namespace = o.method.__entitycached__._determine_namespace(o.method)
        assert namespace == 'tests.test_entitycached--method', namespace

    def test_namespace_for_classmethod(self):
        class Object(object):
            @classmethod
            @entitycached('entity')
            def method(cls, entity):
                return 'HI'
        o = Object()
        namespace = o.method.__entitycached__._determine_namespace(o.method)
        assert namespace == 'tests.test_entitycached-Object-method', namespace

    def test_namespace_forced(self):
        class Object(object):
            @classmethod
            @entitycached('entity', namespace='something')
            def method(cls, entity):
                return 'HI'
        o = Object()
        assert o.method.__entitycached__._determine_namespace(o.method) == 'something'

    #@raises(TypeError)
    # now it works too in inversed order.
    # anyway it's not clear if the decorator should be the first or the last, as the docstring said it must be the first
    def test_namespace_for_inverse_classmethod(self):
        class Object(object):
            @entitycached('entity')
            @classmethod
            def method(cls, entity):
                return 'HI'
        o = Object()
        assert o.method.__entitycached__._determine_namespace(o.method) == 'tests.test_entitycached-Object-method'

class TestCacheKey(object):
    def __init__(self):
        @entitycached('entity')
        def function(entity, other):
            return 'HI'
        self.function = function

    def test_cache_key_by_position(self):
        assert self.function.__entitycached__._determine_cachekey([CacheKey(cache_key='HI')], {}) == 'HI'

    def test_cache_key_by_name(self):
        assert self.function.__entitycached__._determine_cachekey([], {'entity':CacheKey(cache_key='HI')}) == 'HI'

    def test_cache_key_varargs(self):
        assert self.function.__entitycached__._determine_cachekey([CacheKey(cache_key='HI')], {}) == 'HI'

    @raises(ValueError)
    def test_cache_key_fail_noid(self):
        class Object(object):
            pass
        self.function.__entitycached__._determine_cachekey([Object()], {})

    @raises(ValueError)
    def test_cache_key_fail_invalidkey(self):
        class Object(object):
            def __init__(self):
                self.updated_at = datetime.now()
                self._id = self
            def __str__(self):
                return None
        self.function.__entitycached__._determine_cachekey([Object()], {})

    def test_cache_key_ming_without_date(self):
        ming_setup_database()
        mo = MingThing(name='something')

        passed = False
        try:
            self.function.__entitycached__._determine_cachekey([mo], {})
        except ValueError:
            passed = True

        ming_clear_database()
        assert passed

    def test_cache_key_ming(self):
        ming_setup_database()
        mo = MingThingWithDate(name='something')

        expected_key = '%s-%s' % (mo._id, mo.updated_at.strftime('%Y%m%d%H%M%S'))
        try:
            assert self.function.__entitycached__._determine_cachekey([mo], {}) == expected_key
        finally:
            ming_clear_database()

    def test_cache_key_sqla(self):
        sqla_setup_database()
        sqla_clear_database()

        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()

        expected_key = '%s-%s' % (mo.uid, mo.updated_at.strftime('%Y%m%d%H%M%S'))
        try:
            assert self.function.__entitycached__._determine_cachekey([mo], {}) == expected_key
        finally:
            sqla_clear_database()

class TestCacheWorking(object):
    def __init__(self):
        class Counter(object):
            def __init__(self):
                self.count = 0
            @entitycached('entity')
            def inc(self, entity):
                self.count += 1
                return self.count
        self.counter = Counter()

        class FakeCache(object):
            def __init__(self):
                self._cache = {}
            def get_cache(self, *args, **kw):
                self.cache_options = kw
                return self
            def get_value(self, key, createfunc, *args, **kw):
                if key not in self._cache:
                    self._cache[key] = createfunc()
                return self._cache[key]
        self.cache = FakeCache()

    def setup(self):
        self._tg_cache = tg.cache
        tg.cache = self.cache
        self.cache.cache_options = {}

    def teardown(self):
        tg.cache = self._tg_cache

    def test_cache_works(self):
        key = CacheKey(cache_key='HI')
        assert self.counter.inc(key) == 1
        assert self.counter.inc(key) == 1
        assert self.counter.inc(key) == 1

    def test_cache_key_sqlamerge(self):
        sqla_setup_database()
        sqla_clear_database()

        tg.config['DBSession'] = SqlaDBSession

        o = SqlaThing(name=u'foobar')
        SqlaDBSession.add(o)
        mo = SqlaThingWithDate(name=u'something', related_thing=o)
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        @entitycached('arg', sqla_merge=True)
        def with_sqla_merge_func(arg):
            return SqlaDBSession.query(SqlaThingWithDate).all()

        @entitycached('arg', sqla_merge=False)
        def without_sqla_merge_func(arg):
            return SqlaDBSession.query(SqlaThingWithDate).all()

        #Fetch results to cache them
        results = with_sqla_merge_func(CacheKey(cache_key='HI'))
        results = without_sqla_merge_func(CacheKey(cache_key='HI'))

        #remove session
        SqlaDBSession.remove()

        #Check that cached results fail to work when not merged back
        try:
            results = without_sqla_merge_func(CacheKey(cache_key='HI'))
            bool(results[0].related_thing.name==u'foobar')
            raise RuntimeError('This should have failed')
        except DetachedInstanceError:
            pass

        #Check that cached results are correctly merged back into session
        results = with_sqla_merge_func(CacheKey(cache_key='HI'))
        assert results[0].related_thing.name==u'foobar'

    def test_cache_type(self):
        @entitycached('arg', cache_type='dbm')
        def prova(arg):
            return 5

        prova(CacheKey(cache_key='HI'))

        assert self.cache.cache_options == {'type':'dbm'}
