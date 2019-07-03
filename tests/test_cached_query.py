from tgext.datahelpers.caching import cached_query
from .sqla_base import setup_database as sqla_setup_database, clear_database as sqla_clear_database,\
    DBSession as SqlaDBSession, ThingWithDate as SqlaThingWithDate, Thing as SqlaThing
import tg
import beaker
from nose.tools import raises
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

class TestCachedQuery(object):
    def __init__(self):
        class FakeCache(object):
            def __init__(self):
                self._cache = {}
            def get_cache(self, *args, **kw):
                return self
            def get_value(self, key, createfunc, *args, **kw):
                if key not in self._cache:
                    self._cache[key] = createfunc()
                return self._cache[key]
            def clear(self):
                self._cache = {}
        self.cache = FakeCache()

    def setup(self):
        self._tg_cache = tg.cache
        tg.cache = self.cache
        self.cache.get_cache('samplequery').clear()
        sqla_setup_database()
        sqla_clear_database()
        tg.config['DBSession'] = SqlaDBSession

    def teardown(self):
        tg.cache = self._tg_cache
        sqla_clear_database()

    def test_cache_all(self):
        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).all()

        assert len(q) == 1
        assert q[0].name == mo.name
        cached_result = q[0]

        #run query again to check it is has actually been cached
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).all()

        assert len(q) == 1
        assert q[0] is cached_result

    def test_cache_avoid_messing_other_queries(self):
        # This test is to prevent a regression in cached_query._perform_query.
        # In the past it did expunge the just loaded results which would then
        # be merged back by _load_results. The side-effect was that it would
        # also expunge results shared with other queries in the same session
        # making them unusable in the other query.
        mo = SqlaThingWithDate(name=u'something')
        mo.related_thing = SqlaThing(name=u'related')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        other_query = SqlaDBSession.query(SqlaThingWithDate).all()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).all()

        # Check that after the execution of the cached_query the plain
        # query continues to work
        assert other_query[0].related_thing.name == 'related'

        assert len(q) == 1
        assert q[0].name == mo.name
        cached_result = q[0]

        #run query again to check it is has actually been cached
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).all()

        assert len(q) == 1
        assert q[0] is cached_result


    def test_cache_iter(self):
        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate))

        for e in q:
            assert e.name == mo.name
            break

    def test_cache_first(self):
        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).first()

        assert q is not None
        assert q.name == mo.name
        cached_result = q

        #run query again to check it is has actually been cached
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).first()

        assert q is not None
        assert q is cached_result

    def test_cache_first_noresult(self):
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).first()
        assert q is None

        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        #run query again to check it is has actually been cached
        q2 = cached_query('samplequery',
                          SqlaDBSession.query(SqlaThingWithDate)).first()
        assert q2 is None

    def test_cache_one(self):
        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).one()

        assert q is not None
        assert q.name == mo.name
        cached_result = q

        #run query again to check it is has actually been cached
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).one()

        assert q is not None
        assert q is cached_result

    @raises(NoResultFound)
    def test_cache_one_noresult(self):
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).first()
        assert q is None

        mo = SqlaThingWithDate(name=u'something')
        SqlaDBSession.add(mo)
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        #run query again to check it is has actually been cached
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).one()

    @raises(MultipleResultsFound)
    def test_cache_one_multiple_results(self):
        SqlaDBSession.add(SqlaThingWithDate(name=u'something'))
        SqlaDBSession.add(SqlaThingWithDate(name=u'something2'))
        SqlaDBSession.flush()
        SqlaDBSession.commit()

        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).all()
        assert len(q) == 2

        #run query again to check it is has actually been cached and one is used
        q = cached_query('samplequery',
                         SqlaDBSession.query(SqlaThingWithDate)).one()


class TestFileCachedQuery(TestCachedQuery):
    """
    This is to check it works as expected on cache backends that pickle
    the query data
    """
    def __init__(self):
        class FileCache(object):
            def get_cache(self, *args, **kw):
                return beaker.cache.Cache(type='file', data_dir='.', *args, **kw)
        self.cache = FileCache()
