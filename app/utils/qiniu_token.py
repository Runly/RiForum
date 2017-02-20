# coding=UTF-8

from qiniu.auth import Auth

access_key = 'aVFgJ_iyuASK2OyHl3H8EFgohRtUobxaKVJN5q-_'
secret_key = 'O0I9aTRPYPRtQ4jmRMGpmLKUVMSpKKWe0zkRHAXU'
bucket_name = 'ranly'

q = Auth(access_key, secret_key)


def get_qiniu_token(key):
    return q.upload_token(bucket_name, key)
