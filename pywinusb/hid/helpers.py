from ctypes import c_char
from UserList import UserList

class HIDError(Exception):
    "Main HID error exception class type"
    pass

def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied."""
    def new_decorator(f):
        g = decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

#
# Sample Use:
#
@simple_decorator
def logging_decorator(func):
    def you_will_never_see_this_name(*args, **kwargs):
        print 'calling %s ...' % func.__name__
        result = func(*args, **kwargs)
        print 'completed: %s' % func.__name__
        return result
    return you_will_never_see_this_name

def synchronized(lock):
    """ Synchronization decorator. """
    @simple_decorator
    def wrap(f):
        def new_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return new_function
    return wrap

class ReadOnlyList(UserList):
    "Read only sequence wrapper"
    def __init__(self, any_list):
        UserList.__init__(self, any_list)
    def __setitem__(self, index, value):
        raise ValueError("Object is read-only")
