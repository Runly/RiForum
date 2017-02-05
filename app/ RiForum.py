import json
import time
from db.database import *
from flask import Flask, request
from utils.md5 import *

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


@app.route('/sign_in', methods=['POST'])
def sign_in():
    error = None
    if request.method == 'POST':
        email = None
        phone = None
        password = None
        uname = None
        if 'email' in json.loads(request.get_data()).keys():
            email = json.loads(request.get_data())['email']
        if 'phone' in json.loads(request.get_data()).keys():
            phone = json.loads(request.get_data())['phone']
        if 'password' in json.loads(request.get_data()).keys():
            password = json.loads(request.get_data())['password']
        if 'name' in json.loads(request.get_data()).keys():
            uname = json.loads(request.get_data())['name']

        if email is None and phone is None:
            error = 'email and phone can not be empty at the same time'
        elif password is None and uname is None:
            error = 'password and name can not be empty'
        else:
            user = User(password=password, name=uname, time=long(time.time()))
            if email is not None:
                if db_session.query(User.email).filter(User.email == email).scalar() is not None:
                    response = Response(code='0', message='email has been already signed in',
                                        dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.email = email
            else:
                if db_session.query(User.phone).filter(User.phone == phone).scalar() is not None:
                    response = Response(code='0', message='phone has been already signed in',
                                        dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.phone = phone

            db_session.add(user)
            db_session.commit()
            response = Response(data=user.to_json(), message='sign in successfully', code='1',
                                dateline=long(time.time()))
            return json.dumps(response, default=lambda o: o.__dict__)

    response = Response(message=error, code='0', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/login', methods=['POST'])
def login():
    error = None
    if request.method == 'POST':
        email = None
        phone = None
        password = None
        if 'email' in json.loads(request.get_data()).keys():
            email = json.loads(request.get_data())['email']
        if 'phone' in json.loads(request.get_data()).keys():
            phone = json.loads(request.get_data())['phone']
        if 'password' in json.loads(request.get_data()).keys():
            password = json.loads(request.get_data())['password']
        if email is None and phone is None:
            error = 'email and phone can not be empty at the same time'
        elif password is None:
            error = 'password can not be empty'
        else:
            if email is not None:
                user = db_session.query(User).filter(User.email == email).one()
                if user is not None:
                    token = md5(user.password + str(long(time.time())))
                    user.token = token
                    db_session.commit()
                    response = Response(data={'uid': user.id, 'token': token}, code='1',
                                        message='login successfully', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = 'user is not exists'
            else:
                user = db_session.query(User).filter(User.phone == phone).one()
                if user is not None:
                    token = md5(user.password + str(long(time.time())))
                    user.token = token
                    db_session.commit()
                    response = Response(data={'uid': user.id, 'token': token}, code='1',
                                        message='login successfully', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = 'user is not exists'

    response = Response(message=error, code='0', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/release', methods=['POST'])
def release():
    error = None
    if request.method == 'POST':
        token = None
        uid = None
        title = None
        content = None
        plate = None
        sort = None
        if 'token' in json.loads(request.get_data()).keys():
            token = json.loads(request.get_data())['token']
        else:
            error = 'token is necessary'
        if 'uid' in json.loads(request.get_data()).keys():
            uid = json.loads(request.get_data())['uid']
        else:
            error = 'uid is necessary'
        if 'title' in json.loads(request.get_data()).keys():
            title = json.loads(request.get_data())['title']
        else:
            error = 'title is necessary'
        if 'content' in json.loads(request.get_data()).keys():
            content = json.loads(request.get_data())['content']
        else:
            error = 'content is necessary'
        if 'plate' in json.loads(request.get_data()).keys():
            plate = json.loads(request.get_data())['plate']
        else:
            error = 'plate is necessary'
        if 'sort' in json.loads(request.get_data()).keys():
            sort = json.loads(request.get_data())['plate']
        else:
            error = 'sort is necessary'

        if title is None or content is None or uid is None or plate is None or token is None:
            response = Response(message=error, code='0', dateline=long(time.time()))
            return json.dumps(response, default=lambda o: o.__dict__)
        else:
            user = db_session.query(User).filter(User.id == uid).one()
            if token != user.token:
                response = Response(message='not login', code='0', dateline=long(time.time()))
                return json.dumps(response, default=lambda o: o.__dict__)
            else:
                entry = Entries(title=title, content=content,  time=long(time.time()),
                                uid=uid, uname=user.name, plate=plate, sort=sort)
                db_session.add(entry)
                db_session.commit()
                response = Response(data=entry.to_json(), message='release successfully',
                                    code='1', dateline=long(time.time()))
                return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0')

