import tornado.ioloop
import tornado.web
from datetime import datetime
from bson.json_util import dumps
from math import sqrt
import json

import pymongo

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017


class Home(tornado.web.RequestHandler):

    def initialize(self):
        self.conn = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
        self.db = self.conn['points']
        self.coords = self.db['coords']


class Point(Home):

    def get(self, pid):
        try:
            point = self.db.points.find_one({"_id": int(pid)})
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(point))
        except TypeError:
            self.write('788778')

    def post(self):
        _id = self.db.points.count() + 1
        timestamp = datetime.now()

        self.set_header("Content-Type", "application/json")
        #data = json.loads(self.get_body_arguments('x'))

        point = {
                "_id": _id,
                "x": self.get_query_argument('x'),
                "y": self.get_query_argument('y'),
                "timestamp": timestamp
        }
        self.db.points.insert(point)
        location = "/point/" + str(_id)
        self.set_header('Content-Type', 'application/json')
        self.set_header('Location', location)
        self.set_status(201)
        self.write(dumps(point))

    def put(self, pid):
        _id = int(pid)
        timestamp = datetime.now()
        point = {
                "x": self.get_query_argument('x'),
                "y": self.get_query_argument('y'),
                "timestamp": timestamp
        }
        self.db.points.update({"_id": _id}, {"$set": point})
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(point))

    def delete(self, pid):
        _id = int(pid)
        point = {
                "_id": None,
                "x": None,
                "y": None,
                "timestamp": None,
        }
        self.db.points.update({"_id": _id}, {"$set": point})
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(point))


class Points(Home):

    def get(self):
        points = str(list(self.db.points.find()))
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(points))

    def delete(self):
        points = str(list(self.db.points.find()))
        self.set_header('Content-Type', 'application/json')
        self.db.points.drop()
        self.write(dumps(points))


class Distance(Home):

    def get(self):
        location = "/dist/"
        point1_id = self.get_query_argument('point1')
        point2_id = self.get_query_argument('point2')
        point1 = self.db.points.find_one({"_id": int(point1_id)})
        point2 = self.db.points.find_one({"_id": int(point2_id)})
        x1 = int(point1['x'])
        y1 = int(point1['y'])
        x2 = int(point2['x'])
        y2 = int(point2['y'])
        dist = sqrt((x2 - x1)**2 + (y2-y1)**2)
        print(x1, y1, x2, y2)
        print(dist)
        self.write('distance: ')
        self.write(dumps(dist))


application = tornado.web.Application([
    (r"/", Home),
    (r"/point/([0-9]+)", Point),
    (r"/point/", Point),
    (r"/points/", Points),
    (r"/dist/", Distance)
    ], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()