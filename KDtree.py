#!/usr/bin/env python

class KDTree(object):
    
    def __init__(self, point_list, _depth=0):

        if point_list:
            self.axis = _depth % len(point_list[0])
            point_list = sorted(point_list, key=lambda point: point[self.axis])
            median = len(point_list) // 2
            self.location = point_list[median]
            self.child_left = KDTree(point_list[:median], _depth + 1)
            self.child_right = KDTree(point_list[median + 1:], _depth + 1)
        else:
            self.axis = 0
            self.location = None
            self.child_left = None
            self.child_right = None

    def closest_point(self, point, _best=None):

        if self.location is None:
            return _best
        if _best is None:
            _best = self.location
        if distance(self.location, point) < distance(_best, point):
            _best = self.location
        _best = self._child_near(point).closest_point(point, _best)
        if self._distance_axis(point) < distance(_best, point):
            _best = self._child_away(point).closest_point(point, _best)
        return _best

    def _distance_axis(self, point):

        axis_point = list(point)
        axis_point[self.axis] = self.location[self.axis]
        return distance(tuple(axis_point), point)

    def _child_near(self, point):
        if point[self.axis] < self.location[self.axis]:
            return self.child_left
        else:
            return self.child_right

    def _child_away(self, point):
        if self._child_near(point) is self.child_left:
            return self.child_right
        else:
            return self.child_left

def distance(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2
