import sys
import time
sys.path.append("database/")
from db import Response


def str_is_empty(a_str):
    if a_str is None:
        return True
    elif len(a_str) == 0:
        return True
    else:
        return False


def required_verify(keys, json_data):
    result = []
    for key in keys:
        if key not in json_data.keys():
            result.append(False)
            result.append(Response({}, '0', key + ' is required.', long(time.time() * 1000)))
            return result

        if str_is_empty(json_data[key]):
            result.append(False)
            result.append(Response({}, '0', key + ' can not be empty.', long(time.time()*1000)))
            return result

    return [True, {}]
