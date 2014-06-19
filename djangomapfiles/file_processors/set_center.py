from functools import reduce

from django.contrib.gis.geos.collections import Point

from ..models import Feature

def set_center(features):
    """This function runs through all the features and uses
    their centers to calculate an average center. This center can later be
    overwritten."""

    def add_tuples(t1, t2):
        return t1[0] + t2[0], t1[1] + t2[1]

    centers = set(feat.geometry.centroid.tuple for feat in features)
    total = len(centers)
    fold_centers = reduce(add_tuples, centers)
    avglon, avglat = map(lambda x: x / total, fold_centers)
    center = Point(avglat, avglon)
    return center
