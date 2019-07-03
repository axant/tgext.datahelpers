import tg
import inspect
from utils import object_primary_key
from itertools import chain
from hashlib import md5
from tg.decorators import cached_property

try:
    import sqlalchemy.orm.exc as sqla_exc
except ImportError:
    pass

class CacheKey(object):
    """
    Cache Key object, useful to use the entitycached
    decorator when we don't have any real object to pass
    to the cached function
    """
    def __init__(self, cache_key):
        self.cache_key = cache_key

class entitycached(object):
    def __init__(self, key_argument, expire=3600*24*3, cache_type=None, namespace=None, sqla_merge=False):
        self.cache_key_argument = key_argument
        self.cache_expire = expire
        self.cache_type = cache_type
        self.cache_namespace = namespace
        self.sqla_merge = sqla_merge

    def _get_argspec(self, func):
        try:
            im_func = func.im_func
        except AttributeError:
            im_func = func

        spec = inspect.getargspec(im_func)
        argvals = spec[3]
        if argvals is None:
            argvals = []
        return spec[0], spec[1], spec[2], argvals

    def _get_params_with_argspec(self, args, kw):
        argvars, var_args, argkws, argvals = self.argspec
        if argvars and args:
            kw = kw.copy()
            args_len = len(args)
            for i, var in enumerate(argvars):
                if i >= args_len:
                    break
                kw[var] = args[i]
        return kw

    def _object_primary_key(self, model):
        return object_primary_key(model)

    def _determine_namespace(self, func):
        if self.cache_namespace is not None:
            return self.cache_namespace

        try:
            im_func = func.im_func.__name__
            im_class = (func.im_self if func.im_class == type else func.im_class).__name__
            im_module = self.func_module
        except AttributeError:
            im_func = func.__name__
            im_class = ''
            im_module = self.func_module
        return '%s-%s-%s' % (im_module, im_class, im_func)

    def _determine_cachekey(self, args, kw):
        named_params = self._get_params_with_argspec(args, kw)
        cache_pivot = named_params.get(self.cache_key_argument)

        cache_key = getattr(cache_pivot, 'cache_key', None)
        if not cache_key:
            try:
                object_id = getattr(cache_pivot, self._object_primary_key(cache_pivot))
            except:
                raise ValueError('Unable to determine object primary key, please declare a cache_key property in the object')

            try:
                updated_at = getattr(cache_pivot, 'updated_at').strftime('%Y%m%d%H%M%S')
            except:
                raise ValueError('Object missing an updated_at field, please add one ore declare a cache_key property')

            try:
                cache_key = '%s-%s' % (object_id, updated_at)
            except:
                raise ValueError('Unable to determine object cache key')

        return cache_key

    def _merge_sqla_result(self, results):
        DBSession = tg.config['DBSession']
        return [DBSession.merge(o, load=False) for o in results]

    def __call__(self, func):
        #Precalculate argspec
        if not hasattr(func, 'func_name'):
            raise TypeError('decorated object seems not to be a function or method, \
if you are using multiple decorators check that @entitycached is the first.')

        self.argspec = self._get_argspec(func)
        self.func_module = func.__module__

        def wrapped_function(*args, **kw):
            cache_namespace = self._determine_namespace(func)
            cache_key = self._determine_cachekey(args, kw)

            def call_function():
                return func(*args, **kw)

            get_cache_args = {}
            if self.cache_type is not None:
                get_cache_args['type'] = self.cache_type
            cache = tg.cache.get_cache(cache_namespace, **get_cache_args)

            result = cache.get_value(cache_key, createfunc=call_function, expiretime=self.cache_expire)
            if self.sqla_merge:
                result = self._merge_sqla_result(result)
            return result

        #Look like the decorated function
        wrapped_function.__doc__ = func.__doc__
        wrapped_function.__name__ = func.__name__
        wrapped_function.__entitycached__ = self
        return wrapped_function


class cached_query(object):
    def __init__(self, namespace, query, expire=None):
        self._namespace = namespace
        self._query = query
        self._expire = expire

    @cached_property
    def cache_key(self):
        """Given a Query, create a cache key.

        We get the query statement together with its
        parameters and create an md5 out of them which
        is going to be used as the cache key.
        """
        stmt = self._query.with_labels().statement
        compiled = stmt.compile()
        params = compiled.params

        # here we return the key as a long string.
        query_text = " ".join(chain([str(compiled)],
                                    [str(params[k]) for k in sorted(params)]))

        return md5(query_text).hexdigest()

    def _perform_query(self):
        return list(self._query.__iter__())

    def _load_results(self):
        cache = tg.cache.get_cache(self._namespace)
        results = cache.get_value(self.cache_key, expiretime=self._expire,
                                  createfunc=self._perform_query)
        results = self._query.merge_result(results, load=False)
        return results

    def __iter__(self):
        return self._load_results()

    def all(self):
        return list(self)

    def first(self):
        ret = list(self)
        if not ret:
            return None
        return ret[0]

    def one(self):
        ret = list(self)
        l = len(ret)

        if l == 1:
            return ret[0]
        elif l == 0:
            raise sqla_exc.NoResultFound("No row was found for one()")
        else:
            raise sqla_exc.MultipleResultsFound("Multiple rows were found for one()")
