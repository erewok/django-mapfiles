import os

from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError


def validate_file(file_obj):
    filesize = file_obj.file.size
    megabyte_limit = 12.0
    if filesize > megabyte_limit*1024*1024:
        raise ValidationError("This file is too large: max file size is {}MB".format(str(megabyte_limit)))

def validate_zoom(value):
    if int(value) < 1 or int(value) > 20:
        raise ValidationError("Default zoom level must be a number between 1 and 20")


class DataFile(models.Model):
    """This model is for organizing all geographic data files
    whether csv, shapefile, kml, or anything else."""

    zoom_help_text = """Set default zoom level for this map from 1 (global) to 19 (extremely close, like one building). To see all of San Diego County is usually about an 8."""
    file_type_help_text="""Please select the type of file: If you have an American Community Survey dataset (.csv), please select the type of geographic data you will be uploading."""
    Am_Com_Surv_Label = "American Community Survey/Census Data (.csv)"
    FILE_UPLOAD_TYPES = (
        ("Shapefiles", (
            ("shapefile_zip", "Shapefile ZIP (.zip)"),
        )
     ),
        ("KML Files", (
            ("kml", "KML (.kml)"),
            ("kmz", "KMZ (.kmz)"),
        )
     ),
        (Am_Com_Surv_Label, (
            ("tracts", "by Census Tract"),
            ("county-subdivisions", "by County Subdivision"),
            ("counties", "by County"),
            ("states", "by State"),
            ("places", "by Census Designated Place")
        )
     )
    )
    ## Census Geographic JSON API
    ## Use the following url to retrieve geographic boundaries:
    ## http://census.ire.org/geo/1.0/boundary-set/{geography-type}/{geoid}

    CHARACTER_ENCODINGS = ( ("ascii", "ASCII"),
                            ("latin1", "Latin-1"),
                            ("utf8", "UTF-8"),
                            ("UNKNOWN", "Unknown") )
    name = models.CharField(max_length=255, 
                            verbose_name="File Name")
    file_type = models.CharField(max_length=100, 
                                   choices=FILE_UPLOAD_TYPES,
                                   verbose_name="File Type",
                                   help_text=file_type_help_text)
    stored_file = models.FileField(upload_to="uploads/mapfiles/datafiles/%Y/%m/%d",
                                   help_text="Select file",
                                   validators=[validate_file])
    updated = models.DateField(auto_now=True)
    first_uploaded = models.DateField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    process_note = models.CharField(max_length=255, blank=True)
    encoding = models.CharField(max_length=20, 
                                choices=CHARACTER_ENCODINGS,
                                blank=True)
    file_source = models.URLField(blank=True, null=True,
                                  help_text="Where did this file come from?",
                                  verbose_name="Original File URL")
    description = models.TextField(blank=True, null=True)

    ## Optional Geographic Parameters
    srs_wkt = models.TextField(blank=True)
    geom_type = models.CharField(max_length=50, blank=True)
    default_zoom = models.PositiveSmallIntegerField(blank=True, null=True,
                                                    verbose_name="Map Zoom Level",
                                                    help_text=zoom_help_text,
                                                    validators=[validate_zoom])
    default_center = models.PointField(srid=4326, blank=True, null=True)
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_datafile', kwargs={"file_id" : self.id})

    def _actual_filename(self):
        """The name of this data file is not actually its filename.
        It's whatever anyone put in for it while uploading the file. 
        Sometimes, we'll need to grab just the plain-jane filename."""
        return os.path.basename(self.stored_file.path)
    filename = property(_actual_filename)

    def _get_fieldnames(self):
        return self.feature_set.first().attribute_set.all().values_list('field_name', flat=True)

    class Meta:
        verbose_name = "Map Data File"
        verbose_name_plural = "Map Data Files"
        ordering = ['-first_uploaded']

class Feature(models.Model):
    """Generic geographic data model:
    This model is used when we are parsing a shapefile and we do not
    know what geometric types we will be storing in the database.

    This model can be used for any shapefile."""
    datafile = models.ForeignKey(DataFile)
    reference = models.CharField(max_length=100, blank=True)
    federal_geo_id = models.CharField(max_length=100, blank=True,
                                      default="")
    geom_point = models.PointField(srid=4326, blank=True, null=True)
    geom_multipoint = models.MultiPointField(srid=4326, blank=True, 
                                             null=True)
    geom_multilinestring = models.MultiLineStringField(srid=4326, 
                                                       blank=True, 
                                                       null=True)
    geom_multipolygon = models.MultiPolygonField(srid=4326, 
                                                 blank=True, 
                                                 null=True)
    geom_geometrycollection = models.GeometryCollectionField(srid=4326,
                                                             blank=True,
                                                             null=True)
    objects = models.GeoManager()

    def __str__(self):
        return "{}".format(self.id)

    ## need some method to return the geometry type this guy has.
    def _get_geometry(self):
        geoms = [self.geom_point, self.geom_multipoint,
                 self.geom_multilinestring, self.geom_multipolygon,
                 self.geom_geometrycollection]
        geom = next(filter(lambda x: x, geoms))
        return geom
    geometry = property(_get_geometry)

class Attribute(models.Model):
    """This model is for holding generic values that appear in the
    data files that are uploaded. This data is bound to a feature object
    (above), which is collected in a whole DataFile.

    This model is where most of the interesting data lives, but is
    stored generically, because it could really be anything..."""
    feature = models.ForeignKey(Feature)
    field_name = models.CharField(max_length=255)
    attr_type = models.CharField(max_length=20)
    width = models.IntegerField(blank=True,
                                null=True)
    precision = models.IntegerField(blank=True,
                                    null=True)
    field_value = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "{0}: {1}".format(self.field_name, self.field_value)
