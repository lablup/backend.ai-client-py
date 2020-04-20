import random
import string


def random_string_with_digits(length=6):
    allowed_choices = string.ascii_letters + string.digits
    return ''.join(random.choice(allowed_choices) for i in range(length))
