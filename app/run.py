# coding=UTF-8

import json
import time
from utils.md5 import to_md5
from flask import Flask, request
from database.db import User, init_db, DbSession, Response, Entries
from utils.text_util import str_is_empty
from utils.qiniu_token import get_qiniu_token
from utils.constant import QINIU_BASE_URL

app = Flask(__name__)
app.config.from_object('config')

db_session = None


@app.before_request
def before_request(exception=None):
    global db_session
    init_db()
    db_session = DbSession()


@app.teardown_request
def teardown_request(exception=None):
    if db_session is not None:
        db_session.close()


@app.route('/user/sign_in', methods=['POST'])
def sign_in():
    error = None
    if request.method == 'POST':
        email = None
        phone = None
        password = None
        uname = None
        json_data = json.loads(request.get_data())
        if 'email' in json_data.keys():
            email = json_data['email']
        if 'phone' in json_data.keys():
            phone = json_data['phone']
        if 'password' in json_data.keys():
            password = json_data['password']
        if 'name' in json_data.keys():
            uname = json_data['name']

        if str_is_empty(email) and str_is_empty(phone):
            error = '邮箱或手机号不能为空'
        elif str_is_empty(password) or str_is_empty(uname):
            error = '密码和昵称不能为空'
        else:
            user = User(password=password, name=uname, time=long(time.time()))
            if email is not None:
                if db_session.query(User.email).filter(User.email == email).scalar() is not None:
                    response = Response(code='0', message='邮箱已经被注册',
                                        dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.email = email
            else:
                if db_session.query(User.phone).filter(User.phone == phone).scalar() is not None:
                    response = Response(code='0', message='手机号已经被注册',
                                        dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.phone = phone

            db_session.add(user)
            db_session.commit()
            response = Response(data=user.to_json(), message='登陆成功', code='1',
                                dateline=long(time.time()))
            return json.dumps(response, default=lambda o: o.__dict__)

    response = Response(message=error, code='0', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/login', methods=['POST'])
def login():
    error = None
    if request.method == 'POST':
        email = None
        phone = None
        password = None
        json_data = json.loads(request.get_data())
        if 'email' in json_data.keys():
            email = json_data['email']
        if 'phone' in json_data.keys():
            phone = json_data['phone']
        if 'password' in json_data.keys():
            password = json_data['password']

        if email is None and phone is None:
            error = '账号不能为空'
        elif password is None:
            error = '密码不能为空'
        else:
            if email is not None:
                if db_session.query(User).filter(User.email == email).scalar() is not None:
                    user = db_session.query(User).filter(User.email == email).one()
                    token = to_md5(user.password + str(long(time.time())))
                    user.token = token
                    db_session.commit()
                    response = Response(data={'uid': user.id, 'token': token}, code='1',
                                        message='登陆成功', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = '用户不存在'
            else:
                if db_session.query(User).filter(User.phone == phone).scalar() is not None:
                    user = db_session.query(User).filter(User.phone == phone).one()
                    token = to_md5(user.password + str(long(time.time())))
                    user.token = token
                    db_session.commit()
                    response = Response(data=user.to_json(), code='1',
                                        message='登陆成功', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = '用户不存在'

    response = Response(message=error, code='0', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/release', methods=['POST'])
def release():
    error = None
    if request.method == 'POST':
        token = None
        uid = None
        title = None
        content = None
        image = None
        plate = None
        sort = None
        json_data = json.loads(request.get_data(), strict=False)
        if 'token' in json_data.keys():
            token = json_data['token']
        else:
            error = 'token is necessary'
        if 'uid' in json_data.keys():
            uid = json_data['uid']
        else:
            error = 'uid is necessary'
        if 'title' in json_data.keys():
            title = json_data['title']
        else:
            error = 'title is necessary'
        if 'content' in json_data.keys():
            content = json_data['content']
        else:
            error = 'content is necessary'
        if 'plate' in json_data.keys():
            plate = json_data['plate']
        else:
            error = 'plate is necessary'
        if 'sort' in json_data.keys():
            sort = json_data['plate']
        else:
            error = 'sort is necessary'

        if 'image' in json_data.keys():
            image = json_data['image']
            if str_is_empty(image):
                image = '[]'
        else:
            image = '[]'

        if title is None or content is None or uid is None or plate is None or token is None:
            response = Response(message=error, code='0', dateline=long(time.time()))
            return json.dumps(response, default=lambda o: o.__dict__)
        else:
            if db_session.query(User).filter(User.id == uid).scalar() is not None:
                user = db_session.query(User).filter(User.id == uid).one()
                if token != user.token:
                    response = Response(message='没有登录', code='0', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    entry = Entries(title=title, content=content, image=image, time=long(time.time()),
                                    uid=uid, plate=plate, sort=sort, user=user)
                    db_session.add(entry)
                    db_session.commit()
                    response = Response(data=entry.to_json(), message='发布成功',
                                        code='1', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
            else:
                response = Response(message='用户不存在', code='0', dateline=long(time.time()))
                return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/recommend', methods=['GET', 'POST'])
def recommend():
    entry_list = []
    r = db_session.query(Entries).filter(Entries.id > 0).count()
    _sum = 0

    for i in range(20):
        if r == 0 or _sum >= r:
            break
        entry = db_session.query(Entries).filter(Entries.id == i+1).one()
        entry.read_num += 1
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        entry_list.append(entry.to_json())
        db_session.commit()
        _sum += 1
    entry_list.reverse()
    response = Response(data=entry_list, message='successful', code='1', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/qiniu/token', methods=['POST'])
def qiniu_token():
    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
        key = uid + '_' + str(time.time()) + '.jpg'
        data = {'token': get_qiniu_token(key), 'key': key, 'base_url': QINIU_BASE_URL}
        response = Response(data=data, message='successful',
                            code='1', dateline=long(time.time()))
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        error = 'uid is necessary'
        response = Response(message=error, code='0', dateline=long(time.time()))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/comment')
def comment():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7732)

