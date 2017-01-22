# coding=UTF-8
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
from utils.permissions import *

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(15))
    email = Column(String, unique=True)
    phone = Column(String(11), unique=True)
    password = Column(String(16), nullable=False)
    gender = Column(Integer)  # 性别
    birth = Column(String(8))
    location = Column(String(20))
    grade = Column(Integer, nullable=False)
    experience = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    permissions = Column(Integer, nullable=False)
    token = Column(String(32))

    def __init__(self, _id=None, name=None, email=None, phone=None, password='123456', gender=None, birth=None,
                 user_from=None, grade=1, exp=0, time=0, permissions=USER):
        self.id = _id
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password
        self.gender = gender
        self.birth = birth
        self.location = user_from
        self.grade = grade
        self.experience = exp
        self.time = time
        self.permissions = permissions

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'password': self.password,
            'gender': self.gender,
            'birth': self.birth,
            'location': self.location,
            'grade': self.grade,
            'experience': self.experience,
            'time': self.time,
            'permissions': self.permissions
        }

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.__class__.__name__


class Response(object):
    def __init__(self, data=None, code='', message='', dateline=''):
        self.data = data
        self.code = code
        self.message = message
        self.dateline = dateline


engine = create_engine('sqlite:////home/ranly/riforum.db')
DbSession = sessionmaker(bind=engine)
