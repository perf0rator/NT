import tornado.ioloop
import tornado.web
from datetime import datetime
from urllib.parse import urlparse
from bson.json_util import dumps
from math import sqrt
import json

import pymongo

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017

class Home(tornado.web.RequestHandler):

    def initialize(self):
        '''self.conn = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
        self.db = self.conn['blogger']
        self.blogs = self.db['blogs']'''

        self.conn = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
        self.db = self.conn['users']
        self.coords = self.db['coords']

        ## Blog's Welcome entry
        '''timestamp = datetime.now()
        user = {
                "_id": 1,
                "x": 1,
                "y": 1,
                "timestamp": timestamp,
        }
        self.db.users.insert(user)'''


class User(Home):

    def get(self, usid):
        try:
            user = self.db.users.find_one({"_id": int(usid)})
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(user))
        except TypeError:
            self.write('788778')

    def post(self):
        _id = self.db.users.count() + 1
        timestamp = datetime.now()

        self.set_header("Content-Type", "application/json")
        #data = json.loads(self.get_body_arguments('x'))

        user = {
                "_id": _id,
                "x": self.get_query_argument('x'),
                "y": self.get_query_argument('y'),
                "timestamp": timestamp
        }
        self.db.users.insert(user)
        location = "/user/" + str(_id)
        self.set_header('Content-Type', 'application/json')
        self.set_header('Location', location)
        self.set_status(201)
        self.write(dumps(user))

    def put(self, usid):
        ## Convert unicode to int
        _id = int(usid)
        timestamp = datetime.now()
        user = {
                "x": self.get_query_argument('x'),
                "y": self.get_query_argument('y'),
                "timestamp": timestamp
        }
        self.db.users.update({"_id": _id}, {"$set": user})
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(user))

    def delete(self, usid):
        ## Convert unicode to int
        _id = int(usid)
        user = {
                "_id": None,
                "x": None,
                "y": None,
                "timestamp": None,
        }
        self.db.users.update({"_id": _id}, {"$set": user})
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(user))

class Users(Home):

    def get(self):
        users = str(list(self.db.users.find()))
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(users))

    def delete(self):
        users = str(list(self.db.users.find()))
        self.set_header('Content-Type', 'application/json')
        self.db.users.drop()
        self.write(dumps(users))

class Distance(Home):

    def get(self):
        location = "/dist/"
        user1_id = self.get_query_argument('user1')
        user2_id = self.get_query_argument('user2')
        user1 = self.db.users.find_one({"_id": int(user1_id)})
        user2 = self.db.users.find_one({"_id": int(user2_id)})
        x1 = int(user1['x'])
        y1 = int(user1['y'])
        x2 = int(user2['x'])
        y2 = int(user2['y'])
        dist = sqrt((x2 - x1)**2 + (y2-y1)**2)
        print(x1, y1, x2, y2)
        print(dist)
        self.write('distance: ')
        self.write(dumps(dist))



application = tornado.web.Application([
    (r"/", Home),
    (r"/user/([0-9]+)", User),
    (r"/user/", User),
    (r"/users/", Users),
    (r"/dist/", Distance)
    ], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()