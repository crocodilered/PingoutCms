import math


__all__ = ['Coordinates']


class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.WORLD_SIZE = 268435456.0
        self.EARTH_RADIUS_M = 6378137
        self.DEG2RAD = math.pi / 180.0
        self.RAD2DEG = 180.0 / math.pi
        self.M2PI = 2 * math.pi
        self.LATITUDE_MAX = 85.051128779806604
        self.LONGITUDE_MAX = 180.0

    def from_location(self, lon, lat):
        if lat < -self.LATITUDE_MAX or lat > self.LATITUDE_MAX or lon < -self.LONGITUDE_MAX or lat > self.LONGITUDE_MAX:
            raise()
        sin_y = math.sin(lat * self.DEG2RAD)
        self.x = (lon / 360 + 0.5) * self.WORLD_SIZE
        self.y = (0.5 * math.log((1 + sin_y) / (1 - sin_y)) / -self.M2PI + 0.5) * self.WORLD_SIZE

    def get_location(self):
        lng = (self.x / self.WORLD_SIZE - 0.5) * 360
        lat = 90 - 2 * math.atan(math.exp(-(0.5 - (self.y / self.WORLD_SIZE)) * self.M2PI)) * self.RAD2DEG
        return lng, lat

    def get_distance(self, point):
        distance = math.hypot(self.x - point.x, self.y - point.y)
        return distance * self.get_meters_per_pixel() if distance > 1 else 0.0

    def get_meters_per_pixel(self):
        return math.cos(self.get_location()[1] * self.DEG2RAD) * self.M2PI * self.EARTH_RADIUS_M / self.WORLD_SIZE
