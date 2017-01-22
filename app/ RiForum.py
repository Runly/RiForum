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
            user = User(password=password, time=time.time())
            if email is not None:
                if db_session.query(User.email).filter(User.email == email).scalar() is not None:
                    response = Response(data=dict(), code='0', message='email has been already signed in', dateline=time.time())
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.email = email
            else:
                if db_session.query(User.phone).filter(User.phone == phone).scalar() is not None:
                    response = Response(data=dict(), code='0', message='phone has been already signed in', dateline=time.time())
                    return json.dumps(response, default=lambda o: o.__dict__)
                user.phone = phone

            db_session.add(user)
            db_session.commit()
            response = Response(data=user.to_json(), message='sign in successfully', code='1', dateline=time.time())
            return json.dumps(response, default=lambda o: o.__dict__)

    response = Response(message=error, data=dict(), code='0', dateline=time.time())
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
                    token = md5(user.password)
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
                    token = md5(user.password)
                    user.token = token
                    db_session.commit()
                    response = Response(data={'uid': user.id, 'token': token}, code='1',
                                        message='login successfully', dateline=long(time.time()))
                    return json.dumps(response, default=lambda o: o.__dict__)
                else:
                    error = 'user is not exists'

    response = Response(message=error, data=dict(), code='0', dateline=long(time.time()))
    return json.dumps(response, default=lambda o: o.__dict__)


@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0')


