import re


mappings = []


def given(pattern):
    def decorated(fn):
        mappings.append((re.compile(r'^{}$'.format(pattern)), fn))
        return fn
    return decorated


def then(pattern):
    def decorated(fn):
        mappings.append((re.compile(r'^{}$'.format(pattern)), fn))
        return fn
    return decorated
