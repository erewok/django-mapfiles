=============================
dj-mapfiles
=============================

A Django application for live loading and editing of shapfiles, kml files, and content from American Community Survey datasets.

Documentation
-------------

This application is not ready yet for production (see "Problems" below), but I am sharing it in the hopes that it may be useful for someone else. 

About six months ago, I first found myself setting up a Django mapping application, and I was unsure
how to go about mapping Shapefiles or how to get map data and display it. 

Thus,


Problems
---------

*Written for Python3.4 under Django 1.6 only and it has not been tested with any other Django version.

This won't work if you haven't already installed GEOS, GDAL, and PROJ1.4 (see Djano Documentation:
https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/geolibs/#geoslibrarypath)

These packages are particularly easy to install on Ubuntu, but I have not tried other systems.


Quickstart
----------

Clone this repo to somewhere on your Python path.

Install all of the required dependencies for a GeoDjango project: 
https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/geolibs/

Setup a PostGIS (or other spatial) database

Add django.contrib.gis to your django project's INSTALLED_APPS

Add 'djangomapfiles' to your django project's INSTALLED_APPS.

Add it to your main urls.py: 

```python
from djangomapfiles import urls as mapurls

urlpatterns += patterns(''
    url(r'^mapfiles/', include(mapurls)),
)
```
Features
--------

* 
