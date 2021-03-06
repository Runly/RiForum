# coding=UTF-8

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import sys

sys.path.append("..")
from utils.constant import *
from utils.text_util import *

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


# 用户
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(15))
    email = Column(String)
    phone = Column(String(11))
    password = Column(String(16), nullable=False)
    avatar = Column(String)
    gender = Column(Integer)  # 性别
    birth = Column(String(8))
    location = Column(String(20))
    grade = Column(Integer, nullable=False)  # 用户等级
    experience = Column(Integer, nullable=False)  # 用户经验
    time = Column(Integer, nullable=False)  # 注册时间
    permissions = Column(Integer, nullable=False)  # 权限等级
    entry_number = Column(Integer)  # 发帖数
    token = Column(String(32))

    def __init__(self, name='', email='', phone='', password='', avatar='', gender=0,
                 birth='', user_from='', grade=1, exp=0, time=0, permissions=USER, entry_number=0, token=''):
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password
        self.avatar = avatar
        self.gender = gender
        self.birth = birth
        self.location = user_from
        self.grade = grade
        self.experience = exp
        self.time = time
        self.permissions = permissions
        self.entry_number = entry_number
        self.token = token

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'password': '******',
            'avatar': self.avatar,
            'gender': self.gender,
            'birth': self.birth,
            'location': self.location,
            'grade': self.grade,
            'experience': self.experience,
            'time': self.time,
            'permissions': self.permissions,
            'entry_number': self.entry_number,
            'token': self.token
        }


# 板块
class Plate(Base):
    __tablename__ = 'plate'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    message = Column(String)
    icon = Column(String)

    def __init__(self, name='', message='', icon=''):
        self.name = name
        self.message = message
        self.icon = icon

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'message': self.message,
            'icon': self.icon
        }


# 发布的条目
class Entries(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    image = Column(String)
    file_ = Column(String)
    time = Column(Integer, nullable=False)  # 发布时间
    uid = Column(Integer, nullable=False)  # 用户id
    plate_id = Column(Integer, nullable=False)  # 板块名称
    sort = Column(Integer, nullable=False)  # 板块类别（新帖， 精华帖， 普通帖等）
    read_num = Column(Integer)  # 阅读次数
    like_num = Column(Integer)  # 点赞次数
    comment_num = Column(Integer)  # 评论次数
    user = None
    plate = None

    def __init__(self, title='', content='', image='', file_='', time='', uid='',
                 plate_id='', sort='', read_num=0, like_num=0, comment_num=0, user=None, plate=None):
        self.title = title
        self.content = content
        self.image = image
        self.file_ = file_
        self.time = time
        self.uid = uid
        self.plate_id = plate_id
        self.sort = sort
        self.read_num = read_num
        self.like_num = like_num
        self.comment_num = comment_num
        self.user = user
        self.plate = plate

    def set_user(self, user):
        self.user = user

    def set_plate(self, plate):
        self.plate = plate

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image': json.loads(self.image),
            'file': self.file_,
            'time': self.time,
            'plate': self.plate,
            'sort': self.sort,
            'read_num': self.read_num,
            'like_num': self.like_num,
            'comment_num': self.comment_num,
            'user': self.user.to_json(),
            'plate': self.plate.to_json()
        }


# 评论
class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)  # 评论内容
    plate_id = Column(Integer, nullable=False)  # 板块id
    entry_id = Column(Integer, nullable=False)  # 被评论的id
    comment_id = Column(Integer, nullable=False)  # 被评论者id
    uid = Column(Integer, nullable=False)  # 评论者id
    time = Column(Integer, nullable=False)  # 评论时间
    user = None
    commented = None

    def __init__(self, content='', plate_id=0, entry_id=0, comment_id=0, uid=0, time=0):
        self.content = content
        self.plate_id = plate_id
        self.entry_id = entry_id
        self.uid = uid
        self.comment_id = comment_id
        self.time = time

    def to_json(self):
        if self.commented is not None:
            return {
                'id': self.id,
                'content': self.content,
                'plate_id': self.plate_id,
                'entry_id': self.entry_id,
                'uid': self.uid,
                'comment_id': self.comment_id,
                'time': self.time,
                'user': self.user.to_json(),
                'commented': self.commented.to_json()
            }
        else:
            return {
                'id': self.id,
                'content': self.content,
                'plate_id': self.plate_id,
                'entry_id': self.entry_id,
                'uid': self.uid,
                'comment_id': self.comment_id,
                'time': self.time,
                'user': self.user.to_json(),
                'commented': {}
            }

    def set_user(self, user):
        self.user = user

    def set_commented(self, commented):
        self.commented = commented


# 点赞
class Like(Base):
    __tablename__ = 'like'
    id = Column(Integer, primary_key=True)
    plate_id = Column(Integer, nullable=False)
    entry_id = Column(Integer, nullable=False)
    uid = Column(Integer, nullable=False)  # 点赞者id
    uname = Column(String, nullable=False)  # 点赞者name
    to_uid = Column(Integer, nullable=False)  # 被点赞者id
    to_uname = Column(String, nullable=False)  # 被点赞者name

    def __init__(self, plate_id=0, entry_id=0, uid=0, uname='', to_uid=0, to_uname=''):
        self.plate_id = plate_id
        self.entry_id = entry_id
        self.uid = uid
        self.uname = uname
        self.to_uid = to_uid
        self.to_uname = to_uname

    def to_json(self):
        return {
            'plate_id': self.plate_id,
            'entry_id': self.entry_id,
            'uid': self.uid,
            'uname': self.uname,
            'to_uid': self.to_uid,
            'to_uname': self.uname
        }


# 版主
class PlateMaster(Base):
    __tablename__ = 'platemaster'
    id = Column(Integer, primary_key=True)
    uid = Column(Integer, nullable=False)
    uname = Column(String, nullable=False)
    plate_id = Column(Integer, nullable=False)
    flag = Column(Integer, nullable=False)  # 状态(正常或停职)
    time = Column(Integer, nullable=False)  # 任职时间

    def __init__(self, uid=0, uname='', plate_id=0, flag=MASTER_NORMAL, time=0):
        self.uid = uid
        self.uname = uname
        self.plate_id = plate_id
        self.flag = flag
        self.time = time

    def to_json(self):
        return {
            'uid': self.uid,
            'uname': self.uname,
            'plate_id': self.plate_id,
            'flag': self.flag,
            'time': self.time
        }


class Response(object):
    def __init__(self, data=dict(), code='', message='', dateline=0):
        self.data = data
        self.code = code
        self.message = message
        self.dateline = dateline


class SearchResponse(object):
    def __init__(self, user_list=[], entry_list=[], code='', message='', dateline=0):
        self.user_list = user_list
        self.entry_list = entry_list
        self.code = code
        self.message = message
        self.dateline = dateline


class PlateEntriesResponse(object):
    def __init__(self, entry_number, data=[], code='', message='', dateline=0):
        self.entry_number = entry_number
        self.data = data
        self.code = code
        self.message = message
        self.dateline = dateline


engine = create_engine('sqlite:////home/ranly/riforum_db/riforum.db')
# engine = create_engine('sqlite:////Users/ranly/riforum_db/riforum.db')
DbSession = sessionmaker(bind=engine)
