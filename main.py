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
        self.coords = self.db['geosp']

class Initial(Home):

    def get(self):
        self.render("samples.html")

class Point(Home):

    def get(self):
        pid = self.get_query_argument('id')
        try:
            point = self.db.points.find_one({"_id": int(pid)})
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(point))
        except TypeError:
            self.write('788778')

    def post(self):
        _id = self.db.points.count() + 1
        timestamp = str(datetime.now())

        self.set_header("Content-Type", "application/json")
        #data = json.loads(self.get_body_arguments('x'))

        x = int(self.get_query_argument('x'))
        y = int(self.get_query_argument('y'))

        if x and y:
            if (-90 < x < 90) and (-180 < y < 180):
                point = {
                    "_id": _id,
                    "point": [x, y],
                    "timestamp": timestamp
                    }
                self.db.points.insert(point)
                location = "/point/" + str(_id)
                self.set_header('Content-Type', 'application/json')
                self.set_header('Location', location)
                self.set_status(201)
                self.write(dumps(point))
            else:
                self.set_status(201)
                self.write("coordinates must be in range x = [-90, 90], y = [-180, 180]")
        else:
            self.write('Missing argument x or y')

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
                self.db.points.update({"_id": int(pid)}, {"$set": point})
                self.set_header('Content-Type', 'application/json')
                self.write(dumps(point))
            else:
                self.set_status(201)
                self.write("coordinates must be in range x = [-90, 90], y = [-180, 180]")
        else:
            self.write('Missing argument x or y')



    def delete(self):
        pid = self.get_query_argument('id')
        point = {
                "_id": None,
                "point": [None,
                          None],
                "timestamp": None,
        }
        self.db.points.update({"_id": pid}, {"$set": point})
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
      
        
class FindKnn(Home):
    
    def get(self):
        x = self.get_query_argument('x')
        y = self.get_query_argument('y')
        r = self.get_query_argument('r')
        points = str(list(self.db.points.find({"point": {"$near": [x, y],
                                                         "$maxDistance": r}})))
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


application = tornado.web.Application([
    (r"/", Initial),
    (r"/point/([0-9]+)", Point),
    (r"/point/", Point),
    (r"/points/", Points),
    (r"/dist/", Distance),
    (r"/find/", FindKnn)
    ], debug=True)

if __name__ == "__main__":
    application.listen(7777)
    tornado.ioloop.IOLoop.instance().start()
