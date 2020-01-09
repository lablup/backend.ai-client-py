import functools

__all__ = (
    'APIFunctionMeta',
    'BaseFunction',
    'api_function',
)


def _wrap_method(cls, orig_name, meth):

    @functools.wraps(meth)
    def _method(*args, **kwargs):
        assert cls.session is not None, \
               'You must use API wrapper functions via a Session object.'
        # We need to keep the original attributes so that they could be correctly
        # bound to the class/instance at runtime.
        func = getattr(cls, orig_name)
        coro = func(*args, **kwargs)
        if hasattr(cls.session, 'worker_thread'):
            return cls.session.worker_thread.execute(coro)
        else:
            return coro

    return _method


def api_function(meth):
    '''
    Mark the wrapped method as the API function method.
    '''
    setattr(meth, '_backend_api', True)
    return meth


class APIFunctionMeta(type):
    '''
    Converts all methods marked with :func:`api_function` into
    session-aware methods that are either plain Python functions
    or coroutines.
    '''
    _async = True

    def __init__(cls, name, bases, attrs, **kwargs):
        assert 'session' in attrs, \
               'An API function class must define the session attribute.'
        super().__init__(name, bases, attrs)
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, '_backend_api'):
                orig_name = '_orig_' + attr_name
                setattr(cls, orig_name, attr_value)
                wrapped = _wrap_method(cls, orig_name, attr_value)
                setattr(cls, attr_name, wrapped)


class BaseFunction(metaclass=APIFunctionMeta):
    '''
    The class used to build API functions proxies bound to specific session
    instances.
    '''
    session = None
