#!/usr/bin/env python

import tornado.ioloop
import motor.motor_tornado
import tornado.web
from tornado import gen

from datetime import datetime
from bson.json_util import dumps
from bson.son import SON
from bson.objectid import ObjectId

from math import sqrt
import random

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27017
db = motor.MotorClient(MONGODB_HOST, MONGODB_PORT).points


class Home(tornado.web.RequestHandler):
    def init(self):
        self.render("samples.html")


class Point(Home):
    @gen.coroutine
    def get(self, pid):
        self.set_header('Content-Type', 'application/json')
        point = yield db.points.find_one({"_id": int(pid)})
        self.write(dumps(point))
        yield gen.sleep(1)

    @gen.coroutine
    def put(self, pid):
        timestamp = str(datetime.now())
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))
        if x and y:
            if -90 < x < 90 and -180 < y < 180:
                point = {
                    "point": [x, y],
                    "timestamp": timestamp
                }
                yield db.points.update({"_id": int(pid)}, {"$set": point})
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
            yield db.points.update({"_id": int(pid)}, {"$set": point})
            self.set_status(200)
            self.write(dumps("ok"))


class Points(Home):
    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')
        points = db.points.find()
        while (yield points.fetch_next):
            document = points.next_object()
            self.write(dumps(document))

    @gen.coroutine
    def post(self):
        timestamp = datetime.now()
        time = int(datetime.timestamp(timestamp))
        rand = random.randint(1, 1000)
        _id = rand * 10 ** 10 + time  # smekalochka
        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))

        if x and y:
            if -90 < x < 90 and -180 < y < 180:
                point = {
                    "_id": _id,
                    "point": [x, y],
                    "timestamp": str(timestamp)
                }
                yield db.points.insert(point)
                self.set_status(201)
                self.write(dumps(point))
            else:
                self.set_status(400)
                self.write(dumps("coordinates must be in range x = [-90, 90], y = [-180, 180]"))
        else:
            self.set_status(400)
            self.write(dumps('Missing argument x or y'))

    @gen.coroutine
    def delete(self):
        self.set_header('Content-Type', 'application/json')
        yield db.points.remove({})
        self.set_status(200)
        self.write(dumps("OK"))


class FindKnn(Home):
    @gen.coroutine
    def get(self, pid):
        r = int(self.get_query_argument('r'))
        point = yield db.points.find_one({"_id": int(pid)})
        xy = point["point"]
        yield db.points.create_index([("point", "2d")])
        points = db.points.find({"point": SON([("$near", xy), ("$maxDistance", r)])})
        while (yield points.fetch_next):
            document = points.next_object()
            self.write(dumps(document))


application = tornado.web.Application([
    (r"/", Home),
    (r"/point/([0-9]+)", Point),
    (r"/point", Points),
    (r"/point/([0-9]+)/find", FindKnn)
], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()