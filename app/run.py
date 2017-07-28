# coding=UTF-8

import time

from flask import Flask, request

from database.db import *
from utils.constant import *
from utils.md5 import to_md5
from utils.qiniu_token import get_qiniu_token
from utils.text_util import str_is_empty, required_verify

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
    keys = ['password', 'name']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    email = None
    phone = None
    if 'email' in json_data.keys():
        email = json_data['email']
    if 'phone' in json_data.keys():
        phone = json_data['phone']
    if str_is_empty(email) and str_is_empty(phone):
        error = '邮箱或手机号不能为空'
        response = Response(message=error, code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = User(password=json_data['password'], name=json_data['name'],
                time=long(time.time() * 1000))
    if email is not None:
        if db_session.query(User.email).filter(User.email == email).scalar() is not None:
            response = Response(code='0', message='邮箱已经被注册',
                                dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)
        user.email = email
    else:
        if db_session.query(User.phone).filter(User.phone == phone).scalar() is not None:
            response = Response(code='0', message='手机号已经被注册',
                                dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)
        user.phone = phone

    db_session.add(user)
    db_session.commit()
    response = Response(data=user.to_json(), message='注册成功', code='1',
                        dateline=long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/login', methods=['POST'])
def login():
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

        if str_is_empty(email) and str_is_empty(phone):
            error = '账号不能为空'
            response = Response(message=error, code='0', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        if str_is_empty(password):
            error = '密码不能为空'
            response = Response(message=error, code='0', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        user = None
        if email is not None and db_session.query(User).filter(User.email == email).scalar() is not None:
            user = db_session.query(User).filter(User.email == email).one()
        elif phone is not None and db_session.query(User).filter(User.phone == phone).scalar() is not None:
            user = db_session.query(User).filter(User.phone == phone).one()
        else:
            error = '用户不存在'
            response = Response(message=error, code='0', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        if password != user.password:
            response = Response(code='0', message='密码错误', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        token = to_md5(user.password + str(long(time.time() * 1000)))
        user.token = token
        db_session.commit()
        response = Response(data=user.to_json(), code='1',
                            message='登陆成功', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/logout', methods=['POST'])
def logout():
    uid = None
    token = None
    if request.method != 'POST':
        response = Response(message='use POST method', code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
    else:
        error = 'uid is necessary'
    if 'token' in json_data.keys():
        token = json_data['token']
    else:
        error = 'token is necessary'

    if uid is None or token is None:
        response = Response(message=error, code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == uid).scalar() is not None:
        user = db_session.query(User).filter(User.id == uid).one()
        if token != user.token:
            response = Response(message='登录信息失效', code='0', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        token = to_md5(user.password + str(long(time.time() * 1000)))
        user.token = token
        db_session.commit()
        response = Response(code='1', message='登出成功', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response(code='0', message='用户不存在', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/modify_info', methods=['POST'])
def modify_info():
    keys = ['uid', 'name', 'gender']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        response = Response({}, '0', '用户不存在', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    user.name = json_data['name']
    user.gender = json_data['gender']
    db_session.commit()
    response = Response(user.to_json(), '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/modify_avatar', methods=['POST'])
def modify_avatar():
    keys = ['uid', 'avatar']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        response = Response({}, '0', '用户不存在', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    user.avatar = json_data['avatar']
    db_session.commit()
    response = Response(user.to_json(), "1", "successfully", long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/modify_password', methods=['POST'])
def modify_password():
    keys = ['uid', 'old_password', 'new_password']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if user.password != json_data['old_password']:
        response = Response({}, '0', '原密码错误', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user.password = json_data['new_password']
    db_session.commit()
    response = Response({}, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/release', methods=['POST'])
def release():
    keys = ['uid', 'token', 'title', 'content', 'plate_id', 'sort']
    json_data = json.loads(request.get_data(), strict=False)
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    image = '[]'
    if 'image' in json_data.keys():
        if str_is_empty(json_data['image']):
            image = '[]'
        else:
            image = json_data['image']

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        response = Response(message='用户不存在', code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if json_data['token'] != user.token:
        response = Response(message='没有登录', code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(Plate).filter(Plate.id == json_data['plate_id']).scalar() is None:
        response = Response(message='不存在该板块或已被删除', code='0',
                            dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    _plate = db_session.query(Plate).filter(Plate.id == json_data['plate_id']).one()
    entry = Entries(title=json_data['title'], content=json_data['content'], uid=json_data['uid'],
                    plate_id=json_data['plate_id'], sort=json_data['sort'], image=image,
                    time=long(time.time() * 1000), user=user, plate=_plate)
    db_session.add(entry)
    user.entry_number += 1
    db_session.commit()
    response = Response(data=entry.to_json(), message='发布成功',
                        code='1', dateline=long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/delete', methods=['POST'])
def delete():
    keys = ['uid', 'entry_id']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    entry = db_session.query(Entries).filter(Entries.id == json_data['entry_id']).one()
    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if entry.uid != user.id:
        response = Response({}, '0', 'uid and entry_id do not match', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    db_session.query(Comment).filter(Comment.entry_id == json_data['entry_id']).delete()
    db_session.delete(entry)
    user.entry_number -= 1
    db_session.commit()
    response = Response({}, '1', 'delete successfully.', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/recommend', methods=['POST'])
def recommend():
    page = None
    json_data = json.loads(request.get_data())
    if 'page' in json_data.keys():
        page = json_data['page']

    if page is None:
        response = Response([], '0', 'page is necessary', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    entry_list = db_session.query(Entries).filter(Entries.time < page).order_by(-Entries.time).limit(20).all()
    if len(entry_list) == 0:
        code = '1'
        message = 'end'
        response = Response(entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        entry.read_num += 1
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)
    db_session.commit()

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = Response(entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/plate', methods=['GET'])
def plate():
    # 从"板块表"中查询到所有的板块信息
    plate_list = db_session.query(Plate).all()
    if len(plate_list) > 0:
        json_list = []
        # 将"板块列表"序列化为JSON格式
        for p in plate_list:
            json_list.append(p.to_json())

        response = Response(data=json_list, code='1', message='successfully', dateline=long(time.time() * 1000))
        # 将序列化后的结果返回给客户端
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response(data=[], code='1', message='table empty', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/user_release', methods=['POST'])
def user_release():
    keys = ['uid', 'page']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        response = Response([], '0', '用户不存在', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    entry_list = db_session.query(Entries).filter(Entries.uid == json_data['uid']). \
        filter(Entries.time < json_data['page']).order_by(-Entries.time).limit(20).all()
    if len(entry_list) == 0:
        code = '1'
        message = 'end'
        response = Response(entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        entry.read_num += 1
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)
    db_session.commit()

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = Response(entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/all_plate_entries', methods=['GET'])
def all_plate_entries():
    funny_list = db_session.query(Entries).filter(Entries.plate_id == FUNNY).order_by(-Entries.time).limit(4).all()
    media_list = db_session.query(Entries).filter(Entries.plate_id == MEDIA).order_by(-Entries.time).limit(4).all()
    travel_list = db_session.query(Entries).filter(Entries.plate_id == TRAVEL).order_by(-Entries.time).limit(4).all()
    game_list = db_session.query(Entries).filter(Entries.plate_id == GAME).order_by(-Entries.time).limit(4).all()
    daily_list = db_session.query(Entries).filter(Entries.plate_id == DAILY_LIFE).order_by(-Entries.time).limit(4).all()
    food_list = db_session.query(Entries).filter(Entries.plate_id == FOOD).order_by(-Entries.time).limit(4).all()
    carton_list = db_session.query(Entries).filter(Entries.plate_id == CARTON).order_by(-Entries.time).limit(4).all()
    entry_list = funny_list + media_list + travel_list + game_list + daily_list + food_list + carton_list
    if len(entry_list) == 0:
        code = '1'
        message = 'end'
        response = Response(entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        entry.read_num += 1
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)
    db_session.commit()

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = Response(entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/plate_entries', methods=['POST'])
def plate_entries():
    keys = ['plate_id', 'page']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(Plate).filter(Plate.id == json_data['plate_id']).scalar() is None:
        error = '该板块不存在'
        response = PlateEntriesResponse(0, [], '0', error, long(time.time() * 1000))
        return json.dumps(response, lambda o: o.__dict__)

    entry_number = db_session.query(Entries).filter(Entries.plate_id == json_data['plate_id']).count()

    entry_list = db_session.query(Entries).filter(Entries.plate_id == json_data['plate_id']) \
        .filter(Entries.time < json_data['page']).order_by(-Entries.time).limit(20).all()

    if len(entry_list) == 0:
        code = '1'
        message = 'end'
        response = PlateEntriesResponse(entry_number, entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        entry.read_num += 1
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)

    db_session.commit()

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = PlateEntriesResponse(entry_number, entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/search', methods=['POST'])
def search():
    content = None
    json_data = json.loads(request.get_data())
    if 'content' in json_data.keys():
        content = json_data['content']
    else:
        response = Response(message='content is necessary', code='0', dateline=long(time.time()*1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if str_is_empty(content):
        response = Response(data=[], message='successfully', code='1', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user_list = db_session.query(User).filter(User.name.like("%" + content + "%")).all()
    for i in range(len(user_list)):
        user_list[i] = user_list[i].to_json()

    entry_list = db_session.query(Entries).filter(Entries.title.like("%" + content + "%")).limit(30).all()
    for entry in entry_list:
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = SearchResponse(user_list=user_list, entry_list=entry_list, code='1',
                              message='successfully', dateline=long(time.time()*1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/banner_entries', methods=['GET'])
def banner_entries():
    entry_list = db_session.query(Entries).filter(Entries.comment_num > 10)\
        .order_by(-Entries.comment_num).limit(5).all()

    if len(entry_list) == 0:
        code = '1'
        message = 'no banner'
        response = Response(entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = Response(entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/search_recommend', methods=['GET'])
def search_recommend():
    entry_list = db_session.query(Entries).filter(Entries.comment_num >= 1).limit(11).all()

    if len(entry_list) == 0:
        code = '1'
        message = 'no banner'
        response = Response(entry_list, code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for entry in entry_list:
        if db_session.query(User).filter(User.id == entry.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == entry.uid).one()
            entry.set_user(user=user)
        if db_session.query(Plate).filter(Plate.id == entry.plate_id).scalar() is not None:
            _plate = db_session.query(Plate).filter(Plate.id == entry.plate_id).one()
            entry.set_plate(plate=_plate)

    for i in range(len(entry_list)):
        entry_list[i] = entry_list[i].to_json()

    response = Response(entry_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/comment/comment', methods=['POST'])
def comment():
    keys = ['content', 'plate_id', 'entry_id', 'uid', 'comment_id', 'token']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        response = Response(message='用户不存在', code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if user.token != json_data['token']:
        error = '登录信息过期，请重新登录'
        response = Response({}, '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(Entries).filter(Entries.id == json_data['entry_id']).scalar() is None:
        error = '此条主题不存在'
        response = Response({}, '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    _comment = Comment(json_data['content'], json_data['plate_id'], json_data['entry_id'],
                       json_data['comment_id'], json_data['uid'], long(time.time() * 1000))
    _comment.set_user(user)

    if json_data['comment_id'] != '-1':
        if db_session.query(Comment).filter(Comment.id == json_data['comment_id']).scalar() is not None:
            commented = db_session.query(Comment).filter(Comment.id == json_data['comment_id']).one()
            if db_session.query(User).filter(User.id == commented.uid).scalar() is not None:
                user = db_session.query(User).filter(User.id == commented.uid).one()
                commented.set_user(user)
            _comment.set_commented(commented)
        else:
            error = '这条评论已不存在'
            response = Response({}, '0', error, long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

    db_session.add(_comment)
    entry = db_session.query(Entries).filter(Entries.id == json_data['entry_id']).one()
    entry.comment_num += 1
    db_session.commit()
    response = Response(_comment.to_json(), '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/comment/comment_list', methods=['POST'])
def comment_list():
    keys = ['page', 'entry_id']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    _comment_list = db_session.query(Comment).filter(Comment.entry_id == json_data['entry_id']) \
        .filter(Comment.time > json_data['page']).order_by(Comment.time).limit(20).all()

    if len(_comment_list) == 0:
        response = Response(_comment_list, '1', 'end', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    for _comment in _comment_list:
        if db_session.query(User).filter(User.id == _comment.uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == _comment.uid).one()
            _comment.set_user(user=user)
        if _comment.comment_id != -1:
            if db_session.query(Comment).filter(Comment.id == _comment.comment_id).scalar() is not None:
                commented = db_session.query(Comment).filter(Comment.id == _comment.comment_id).one()
                if db_session.query(User).filter(User.id == commented.uid).scalar() is not None:
                    user = db_session.query(User).filter(User.id == commented.uid).one()
                    commented.set_user(user)
                _comment.set_commented(commented)
    db_session.commit()

    for i in range(len(_comment_list)):
        _comment_list[i] = _comment_list[i].to_json()

    response = Response(_comment_list, '1', 'successfully', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/qiniu/token', methods=['POST'])
def qiniu_token():
    keys = ['uid', 'token']
    json_data = json.loads(request.get_data())
    verify_result = required_verify(keys, json_data)
    if not verify_result[0]:
        return json.dumps(verify_result[1], default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == json_data['uid']).scalar() is None:
        error = '用户不存在'
        response = Response(message=error, code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if user.token != json_data['token']:
        error = '登录信息过期，请重新登录'
        response = Response(message=error, code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    key = str(json_data['uid']) + '_' + str(long(time.time() * 1000)) + '.jpg'
    data = {'token': get_qiniu_token(key), 'key': key, 'base_url': QINIU_BASE_URL}
    response = Response(data=data, message='successful',
                        code='1', dateline=long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7732)
