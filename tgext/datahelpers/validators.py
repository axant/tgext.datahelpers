import tg
from formencode import Invalid, FancyValidator
from tgext.datahelpers.utils import object_primary_key

try:
    #Here for compatibility between TG2.1.5 and TG2.2
    from crank.util import get_params_with_argspec, remove_argspec_params_from_params
    def tg_get_params_with_argspec(controller, *args, **kw):
        return get_params_with_argspec(*args, **kw)
    def tg_remove_argspec_params_from_params(controller, *args, **kw):
        return remove_argspec_params_from_params(*args, **kw)
except ImportError:
    def tg_get_params_with_argspec(controller, *args, **kw):
        return controller._get_params_with_argspec(*args, **kw)
    def tg_remove_argspec_params_from_params(controller, *args, **kw):
        return controller._remove_argspec_params_from_params(*args, **kw)

def validated_handler(func_, **kw):
    def _validated_handler(controller, *remainder, **params_):
        params = dict(kw)
        params.update(params_)

        #This is necessary to make possible error handling cascading
        def func(*args, **kw):
            return func_(*args, **kw)
        func.decoration = func_.decoration
        func.im_func = func_
        func.im_self = controller

        validate_params = tg_get_params_with_argspec(controller, func, params, remainder)

        try:
            params = controller._perform_validate(func, validate_params)
        except Exception as inv:
            error_handler, output = controller._handle_validation_errors(func, remainder, params, inv)
            return output

        params, remainder = tg_remove_argspec_params_from_params(controller, func, params, remainder)
        return func(controller, *remainder, **params)

    #use the same decoration to keep around hooks
    _validated_handler.decoration = func_.decoration
    return _validated_handler



try:
    import sqlalchemy

    class SQLAEntityConverter(FancyValidator):
        def __init__(self, klass, session=None, slugified=False):
            super(FancyValidator, self).__init__(not_empty=True)
            self.klass = klass
            self.session = session
            self.slugified = slugified

        def _to_python(self, value, state):
            if self.session is None:
                self.session = tg.config['DBSession']

            if self.slugified:
                try:
                    value = value.rsplit('-', 1)[-1]
                except:
                    value = value

            return self.session.query(self.klass).get(value)

        def _from_python(self, value, state):
            return getattr(value, object_primary_key(value))

        def validate_python(self, value, state):
            if not value:
                raise Invalid('object not found', value, state)

except ImportError: #pragma: no cover
    pass


try:
    import ming
    from bson import ObjectId

    class MingEntityConverter(FancyValidator):
        def __init__(self, klass, slugified=False):
            super(FancyValidator, self).__init__(not_empty=True)
            self.klass = klass
            self.slugified = slugified

        def _to_python(self, value, state):
            if self.slugified:
                try:
                    value = value.rsplit('-', 1)[-1]
                except:
                    value = value

            try:
                obj_id = ObjectId(value)
            except:
                raise Invalid('object not found', value, state)
            
            return self.klass.query.get(_id=obj_id)

        def _from_python(self, value, state):
            return getattr(value, object_primary_key(value))

        def validate_python(self, value, state):
            if not value:
                raise Invalid('object not found', value, state)

except ImportError: #pragma: no cover
    pass
