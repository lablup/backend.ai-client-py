from .exceptions import *  # noqa
from .session import *  # noqa

__all__ = [
    exceptions.__all__,  # noqa
    session.__all__,  # noqa
]

__version__ = '19.03.0b2'


def get_user_agent():
    return 'Backend.AI Client for Python {0}'.format(__version__)
