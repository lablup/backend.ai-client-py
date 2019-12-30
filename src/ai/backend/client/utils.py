class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Undefined(metaclass=Singleton):
    '''
    A special type to represent an undefined value.
    '''
    pass


undefined = Undefined()
