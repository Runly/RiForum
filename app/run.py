# coding=UTF-8

import time

from flask import Flask, request

from database.db import *
from utils.constant import *
from utils.md5 import to_md5
from utils.qiniu_token import get_qiniu_token
from utils.text_util import str_is_empty

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
            user = User(password=password, name=uname, time=long(time.time() * 1000))
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
            response = Response(data=user.to_json(), message='登陆成功', code='1',
                                dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)

    response = Response(message=error, code='0', dateline=long(time.time() * 1000))
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
                    if password != user.password:
                        response = Response(data={}, code='0',
                                            message='密码错误', dateline=long(time.time() * 1000))
                        return json.dumps(response, default=lambda o: o.__dict__)

                    token = to_md5(user.password + str(long(time.time() * 1000)))
                    user.token = token
                    db_session.commit()
                    response = Response(data=user.to_json(), code='1',
                                        message='登陆成功', dateline=long(time.time() * 1000))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = '用户不存在'
            else:
                if db_session.query(User).filter(User.phone == phone).scalar() is not None:
                    user = db_session.query(User).filter(User.phone == phone).one()
                    if password != user.password:
                        response = Response(data={}, code='0',
                                            message='密码错误', dateline=long(time.time() * 1000))
                        return json.dumps(response, default=lambda o: o.__dict__)

                    token = to_md5(user.password + str(long(time.time() * 1000)))
                    user.token = token
                    db_session.commit()
                    response = Response(data=user.to_json(), code='1',
                                        message='登陆成功', dateline=long(time.time() * 1000))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = '用户不存在'

    response = Response(message=error, code='0', dateline=long(time.time() * 1000))
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
    uid = None
    name = None
    gender = None
    error = None
    code = '1'
    message = 'successfully'
    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
    else:
        error = 'uid is necessary'
    if 'name' in json_data.keys():
        name = json_data['name']
    else:
        error = 'name is necessary'
    if 'gender' in json_data.keys():
        gender = json_data['gender']
    else:
        error = 'gender is necessary'

    if uid is None or name is None or gender is None:
        response = Response({}, '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == uid).scalar() is not None:
        user = db_session.query(User).filter(User.id == uid).one()
        user.name = name
        user.gender = gender
        db_session.commit()
        response = Response(user.to_json(), code, message, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response({}, '0', '用户不存在', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/user/modify_avatar', methods=['POST'])
def modify_avatar():
    uid = None
    avatar = None
    error = None
    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
    else:
        error = 'uid is necessary'
    if 'avatar' in json_data.keys():
        avatar = json_data['avatar']
    else:
        error = 'avatar is necessary'

    if uid is None or avatar is None:
        response = Response({}, '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == uid).scalar() is not None:
        user = db_session.query(User).filter(User.id == uid).one()
        user.avatar = avatar
        db_session.commit()
        response = Response(user.to_json(), "1", "successfully", long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response({}, '0', '用户不存在', long(time.time() * 1000))
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
        plate_id = None
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
        if 'plate_id' in json_data.keys():
            plate_id = json_data['plate_id']
        else:
            error = 'plate is necessary'
        if 'sort' in json_data.keys():
            sort = json_data['sort']
        else:
            error = 'sort is necessary'

        if 'image' in json_data.keys():
            image = json_data['image']
            if str_is_empty(image):
                image = '[]'
        else:
            image = '[]'

        if title is None or content is None or uid is None or plate_id is None or token is None:
            response = Response(message=error, code='0', dateline=long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)
        else:
            if db_session.query(User).filter(User.id == uid).scalar() is not None:
                user = db_session.query(User).filter(User.id == uid).one()
                if token != user.token:
                    response = Response(message='没有登录', code='0', dateline=long(time.time() * 1000))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    if db_session.query(Plate).filter(Plate.id == plate_id).scalar() is not None:
                        _plate = db_session.query(Plate).filter(Plate.id == plate_id).one()
                    entry = Entries(title=title, content=content, image=image, time=long(time.time() * 1000),
                                    uid=uid, plate_id=plate_id, sort=sort, user=user, plate=_plate)
                    db_session.add(entry)
                    user.entry_number += 1
                    db_session.commit()
                    response = Response(data=entry.to_json(), message='发布成功',
                                        code='1', dateline=long(time.time() * 1000))
                    return json.dumps(response, default=lambda o: o.__dict__)
            else:
                response = Response(message='用户不存在', code='0', dateline=long(time.time() * 1000))
                return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/delete', methods=['POST'])
def delete():
    keys = ['uid', 'entry_id']
    json_data = json.loads(request.get_data())
    for key in keys:
        if key not in json_data.keys():
            response = Response({}, '0', key + ' is necessary.', long(time.time()*1000))
            return json.dumps(response, default=lambda o: o.__dict__)

        if json_data[key] is None:
            response = Response({}, '0', key + ' can not be None.', long(time.time()*1000))
            return json.dumps(response, default=lambda o: o.__dict__)

    entry = db_session.query(Entries).filter(Entries.id == json_data['entry_id']).one()
    user = db_session.query(User).filter(User.id == json_data['uid']).one()
    if entry.uid != user.id:
        response = Response({}, '0', 'uid and entry_id do not match', long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    db_session.query(Comment).filter(Comment.entry_id == json_data['entry_id']).delete()
    db_session.delete(entry)
    db_session.commit()
    response = Response({}, '1', 'delete successfully.', long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/recommend', methods=['POST'])
def recommend():
    page = None
    error = None
    code = '1'
    message = 'successfully'
    json_data = json.loads(request.get_data())
    if 'page' in json_data.keys():
        page = json_data['page']
    else:
        error = 'page is necessary'

    if page is None:
        code = '0'
        message = error
        response = Response([], code, message, long(time.time() * 1000))
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

    response = Response(entry_list, code, message, long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/plate', methods=['GET'])
def plate():
    plate_list = db_session.query(Plate).all()
    if len(plate_list) > 0:
        json_list = []
        for p in plate_list:
            json_list.append(p.to_json())

        response = Response(data=json_list, code='1',
                            message='successfully', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response(data=[], code='1', message='table empty', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/user_release', methods=['POST'])
def user_release():
    uid = None
    page = None
    error = None
    code = '1'
    message = 'successfully'
    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
    else:
        error = 'uid不能为空'
    if 'page' in json_data.keys():
        page = json_data['page']
    else:
        error = 'page不能为空'

    if uid is None or page is None:
        response = Response([], '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    if db_session.query(User).filter(User.id == uid).scalar() is None:
        error = '用户不存在'
        response = Response([], '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    entry_list = db_session.query(Entries).filter(Entries.uid == uid). \
        filter(Entries.time < page).order_by(-Entries.time).limit(20).all()
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

    response = Response(entry_list, code, message, long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/all_plate_entries', methods=['GET'])
def all_plate_entries():
    code = '1'
    message = 'successfully'
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

    response = Response(entry_list, code, message, long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/entry/plate_entries', methods=['POST'])
def plate_entries():
    plate_id = None
    page = None
    error = None
    json_data = json.loads(request.get_data())
    if 'plate_id' in json_data.keys():
        plate_id = json_data['plate_id']
    else:
        error = 'plate_id is necessary'
    if 'page' in json_data.keys():
        page = json_data['page']
    else:
        error = 'page is necessary'

    if plate_id is None or page is None:
        response = PlateEntriesResponse(0, [], '0', error, long(time.time() * 1000))
        return json.dumps(response, lambda o: o.__dict__)

    if db_session.query(Plate).filter(Plate.id == plate_id).scalar() is None:
        error = '该板块不存在'
        response = PlateEntriesResponse(0, [], '0', error, long(time.time() * 1000))
        return json.dumps(response, lambda o: o.__dict__)

    entry_number = db_session.query(Entries).filter(Entries.plate_id == plate_id).count()

    entry_list = db_session.query(Entries).filter(Entries.plate_id == plate_id) \
        .filter(Entries.time < page).order_by(-Entries.time).limit(20).all()

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

    response = SearchResponse(user_list=user_list, entry_list=entry_list, code='1', message='successfully', dateline=long(time.time()*1000))
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
    content = None
    plate_id = None
    entry_id = None
    uid = None
    comment_id = None
    token = None
    error = None
    json_data = json.loads(request.get_data())
    if 'content' in json_data.keys():
        content = json_data['content']
    else:
        error = 'content is necessary'

    if 'plate_id' in json_data.keys():
        plate_id = json_data['plate_id']
    else:
        error = 'plate_id is necessary'

    if 'entry_id' in json_data.keys():
        entry_id = json_data['entry_id']
    else:
        error = 'entry_id is necessary'

    if 'uid' in json_data.keys():
        uid = json_data['uid']
    else:
        error = 'uid is necessary'

    if 'comment_id' in json_data.keys():
        comment_id = json_data['comment_id']
    else:
        error = 'comment_id is necessary'

    if 'token' in json_data.keys():
        token = json_data['token']
    else:
        error = 'token is necessary'

    if content is not None and plate_id is not None and entry_id is not None \
            and uid is not None and comment_id is not None and token is not None:
        if db_session.query(User).filter(User.id == uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == uid).one()
            if user.token != token:
                error = '登录信息过期，请重新登录'
                response = Response({}, '0', error, long(time.time() * 1000))
                return json.dumps(response, default=lambda o: o.__dict__)

            if db_session.query(Entries).filter(Entries.id == entry_id).scalar() is None:
                error = '此条主题不存在'
                response = Response({}, '0', error, long(time.time() * 1000))
                return json.dumps(response, default=lambda o: o.__dict__)

            _comment = Comment(content, plate_id, entry_id, comment_id, uid, long(time.time() * 1000))
            _comment.set_user(user)

            if comment_id != -1:
                if db_session.query(Comment).filter(Comment.id == comment_id).scalar() is not None:
                    commented = db_session.query(Comment).filter(Comment.id == comment_id).one()
                    if db_session.query(User).filter(User.id == commented.uid).scalar() is not None:
                        user = db_session.query(User).filter(User.id == commented.uid).one()
                        commented.set_user(user)
                    _comment.set_commented(commented)
                else:
                    error = '这条评论已不存在'
                    response = Response({}, '0', error, long(time.time() * 1000))
                    return json.dumps(response, default=lambda o: o.__dict__)

            db_session.add(_comment)
            entry = db_session.query(Entries).filter(Entries.id == entry_id).one()
            entry.comment_num += 1
            db_session.commit()
            response = Response(_comment.to_json(), '1', 'successfully', long(time.time() * 1000))
            return json.dumps(response, default=lambda o: o.__dict__)
    else:
        response = Response({}, '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/comment/comment_list', methods=['POST'])
def comment_list():
    page = None
    entry_id = None
    error = None
    code = '1'
    message = 'successfully'
    json_data = json.loads(request.get_data())
    if 'page' in json_data.keys():
        page = json_data['page']
    else:
        error = 'page is necessary'

    if 'entry_id' in json_data.keys():
        entry_id = json_data['entry_id']
    else:
        error = 'entry_id is necessary'

    if page is None or entry_id is None:
        response = Response([], '0', error, long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)

    _comment_list = db_session.query(Comment).filter(Comment.entry_id == entry_id) \
        .filter(Comment.time > page).order_by(Comment.time).limit(20).all()

    if len(_comment_list) == 0:
        code = '1'
        message = 'end'
        response = Response(_comment_list, code, message, long(time.time() * 1000))
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

    response = Response(_comment_list, code, message, long(time.time() * 1000))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/qiniu/token', methods=['POST'])
def qiniu_token():
    uid = None
    token = None
    json_data = json.loads(request.get_data())
    if 'uid' in json_data.keys():
        uid = json_data['uid']
    if 'token' in json_data.keys():
        token = json_data['token']

    if uid is not None and token is not None:
        if db_session.query(User).filter(User.id == uid).scalar() is not None:
            user = db_session.query(User).filter(User.id == uid).one()
            if user.token == token:
                key = str(uid) + '_' + str(long(time.time())) + '.jpg'
                data = {'token': get_qiniu_token(key), 'key': key, 'base_url': QINIU_BASE_URL}
                response = Response(data=data, message='successful',
                                    code='1', dateline=long(time.time() * 1000))
                return json.dumps(response, default=lambda o: o.__dict__)
            else:
                error = '登录信息过期，请重新登录'
                response = Response(message=error, code='0', dateline=long(time.time() * 1000))
                return json.dumps(response, default=lambda o: o.__dict__)
    else:
        error = '用户id和token不能为空'
        response = Response(message=error, code='0', dateline=long(time.time() * 1000))
        return json.dumps(response, default=lambda o: o.__dict__)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7732)
