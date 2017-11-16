#!/usr/bin/env python

import tornado.ioloop
import tornado.web
from tornado import gen
from datetime import datetime
from bson.json_util import dumps
from math import sqrt
from bson.son import SON
from KDtree import KDTree
import motor.motor_tornado
import pymongo

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017


class Home(tornado.web.RequestHandler):

    def initialize(self):
        self.conn = motor.motor_tornado.MotorClient(MONGODB_HOST, MONGODB_PORT)#pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
        self.db = self.conn['points']
        #self.coords = self.db['geosp']


class Initial(Home):

    def get(self):
        self.render("samples.html")


class Point(Home):

    @gen.coroutine
    def get(self, pid):
        point = yield self.db.points.find_one({"_id": int(pid)})
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(point))

        '''if point is None:
            self.write(dumps(point))#"point with id = {} does not exist".format(pid))
        else:
            self.write(dumps(point))#dumps(point))'''

    @gen.coroutine
    def post(self):
        count = yield self.db.points.count()
        _id = count + 1
        print(count, _id)
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
                self.set_status(201)
                self.write("coordinates must be in range x = [-90, 90], y = [-180, 180]")
        else:
            self.write('Missing argument x or y')

    @gen.coroutine
    def put(self):
        pid = self.get_query_argument('id')
        timestamp = str(datetime.now())
        x = self.get_query_argument('x')
        y = self.get_query_argument('y')
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
                self.set_status(201)
                self.write("coordinates must be in range x = [-90, 90], y = [-180, 180]")
        else:
            self.write('Missing argument x or y')

    @gen.coroutine
    def delete(self, pid):
        point = yield self.db.points.find_one({"_id": int(pid)})
        self.set_header('Content-Type', 'application/json')
        if point is None:
            self.write(dumps(point))#("point with id = {} does not exist".format(pid))
        else:
            self.db.points.remove({"_id": int(pid)})
            self.write(dumps("ok"))



class Points(Home):
    @gen.coroutine
    def get(self):
        points = yield self.db.points.find()
        self.set_header('Content-Type', 'application/json')
        self.write(dumps(points))

    @gen.coroutine
    def delete(self):
        points = yield list(self.db.points.find())
        self.set_header('Content-Type', 'application/json')
        self.db.points.remove({})
        self.write(dumps(points))
      
        
class FindKnn(Home):
    
    def get(self):
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))
        r = int(self.get_query_argument('r'))
        self.db.points.createIndex({"point": "2d"})
        points = list(self.db.points.find({"point": SON([("$near", [x, y]), ("$maxDistance", r)])}))
        self.write(dumps(points))


class Distance(Home):

    def get(self):
        location = "/dist/"
        point1_id = self.get_query_argument('point1')
        point2_id = self.get_query_argument('point2')
        point1 = self.db.points.find_one({"_id": int(point1_id)})
        point2 = self.db.points.find_one({"_id": int(point2_id)})
        x1 = int(point1['point'][0])
        y1 = int(point1['point'][1])
        x2 = int(point2['point'][0])
        y2 = int(point2['point'][1])
        dist = sqrt((x2 - x1)**2 + (y2-y1)**2)
        print(x1, y1, x2, y2)
        print(dist)
        self.write('distance: ')
        self.write(dumps(dist))


class KDtree_search(Home):

    def get(self):
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))
        points = []
        data = self.db.points.find({}, {"point": 1})
        for point in data:
            points.append(point["point"])

        tree = KDTree(points)
        nn = tree.closest_point((x, y))
        neighbours = self.db.points.find_one({"point": nn})

        self.write(dumps(neighbours))

application = tornado.web.Application([
    (r"/", Initial),
    (r"/point/([0-9]+)", Point),
    (r"/point/", Point),
    (r"/points/", Points),
    (r"/dist/", Distance),
    (r"/find/", FindKnn),
    (r"/nn/", KDtree_search)
    ], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()
