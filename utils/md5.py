import hashlib


def md5(str_):
    m = hashlib.md5()
    m.update(str_)
    return m.hexdigest()
