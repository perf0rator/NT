#!/usr/bin/env python

import tornado.ioloop
import motor.motor_tornado
import tornado.web
from tornado import gen
from datetime import datetime
from bson.json_util import dumps
from math import sqrt
from bson.son import SON
from KDtree import KDTree


MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017


class Home(tornado.web.RequestHandler):

    def initialize(self):
        self.conn = motor.motor_tornado.MotorClient(MONGODB_HOST, MONGODB_PORT)
        # self.conn = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
        self.db = self.conn['points']


class Initial(Home):

    def get(self):
        self.render("samples.html")


class Point(Home):

    @gen.coroutine
    def get(self, pid):
        self.set_header('Content-Type', 'application/json')
        point = yield self.db.points.find_one({"_id": int(pid)})
        self.write(dumps(point))
        yield gen.sleep(1)

    @gen.coroutine
    def post(self):
        count = yield self.db.points.count()
        _id = count + 1
        timestamp = str(datetime.now())
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))

        if x and y:
            if (-90 < x < 90) and (-180 < y < 180):
                point = {
                    "_id": _id,
                    "point": [x, y],
                    "timestamp": timestamp
                    }
                yield self.db.points.insert(point)
                self.set_status(201)
                self.write(dumps(point))
            else:
                self.set_status(400)
                self.write(dumps("coordinates must be in range x = [-90, 90], y = [-180, 180]"))
        else:
            self.set_status(400)
            self.write(dumps('Missing argument x or y'))
        # yield gen.sleep(10)

    @gen.coroutine
    def put(self, pid):
        timestamp = str(datetime.now())
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))
        if x and y:
            if (-90 < x < 90) and (-180 < y < 180):
                point = {
                    "point": [x, y],
                    "timestamp": timestamp
                    }
                yield self.db.points.update({"_id": int(pid)}, {"$set": point})
                self.set_header('Content-Type', 'application/json')
                self.write(dumps(point))
            else:
                self.set_status(400)
                self.write(dumps("coordinates must be in range x = [-90, 90], y = [-180, 180]"))
        else:
            self.set_status(400)
            self.write(dumps('Missing argument x or y'))

    @gen.coroutine
    def delete(self, pid):
        self.set_header('Content-Type', 'application/json')
        point = {
            "point": None,
            "timestamp": None
        }
        if point is None:
            self.write(dumps("point with id = {} does not exist".format(pid)))
        else:
            yield self.db.points.update({"_id": int(pid)}, {"$set": point})
            self.set_status(200)
            self.write(dumps("ok"))


class Points(Home):

    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')
        points = self.db.points.find()
        while (yield points.fetch_next):
            document = points.next_object()
            self.write(dumps(document))

    @gen.coroutine
    def delete(self):
        self.set_header('Content-Type', 'application/json')
        yield self.db.points.remove({})
        self.set_status(200)
        self.write(dumps("OK"))
      
        
class FindKnn(Home):

    @gen.coroutine
    def get(self, pid):
        r = int(self.get_query_argument('r'))
        point = yield self.db.points.find_one({"_id": int(pid)})
        xy = point["point"]
        print(xy, r)
        self.db.points.create_index({"point": "2d"})
        points = self.db.points.find({"point": SON([("$near", xy), ("$maxDistance", r)])})
        while (yield points.fetch_next):
            document = points.next_object()
            self.write(dumps(document))


class Distance(Home):

    @gen.coroutine
    def get(self):
        point1_id = self.get_query_argument('point1')
        point2_id = self.get_query_argument('point2')
        point1 = yield self.db.points.find_one({"_id": int(point1_id)})
        point2 = yield self.db.points.find_one({"_id": int(point2_id)})
        x1 = int(point1['point'][0])
        y1 = int(point1['point'][1])
        x2 = int(point2['point'][0])
        y2 = int(point2['point'][1])
        dist = sqrt((x2 - x1)**2 + (y2-y1)**2)
        self.write('distance: ')
        self.write(dumps(dist))


class KDtree_search(Home):

    @gen.coroutine
    def get(self, pid):
        point = yield self.db.points.find_one({"_id": int(pid)})
        xy = point["point"]
        points = []
        document = []
        data = self.db.points.find({}, {"point": 1})
        while (yield data.fetch_next):
            document.append(data.next_object())
        for point in document:
            points.append(point["point"])
        print(points,'oooooooooooooo')
        tree = KDTree(points)
        nn = tree.closest_point(xy)
        neighbours = yield self.db.points.find_one({"point": nn})
        self.write(dumps(neighbours))

application = tornado.web.Application([
    (r"/", Initial),
    (r"/point/([0-9]+)", Point),
    (r"/point", Points),
    (r"/dist/", Distance),
    (r"/point/([0-9]+)/find/", FindKnn),
    (r"/point/([0-9]+)/nn", KDtree_search)
    ], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()
