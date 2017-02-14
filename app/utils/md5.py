import hashlib


def to_md5(str_):
    m = hashlib.md5()
    m.update(str_)
    return m.hexdigest()
