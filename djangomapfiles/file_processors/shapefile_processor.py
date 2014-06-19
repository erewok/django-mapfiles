"""This module processes shapefiles for our
kpbs_maps Django application.

This function is meant to be given
a shapefile ZIP archive, which it will unpack,
or a direct path to a shapefile. 

It will process the file and load it into the database."""
import os, shutil # These go together. sys too. PEP 8 be dammed.
import tempfile 
import zipfile

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal import OGRGeomType
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.gdal import CoordTransform
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.collections import MultiPolygon
from django.contrib.gis.geos.collections import MultiLineString

from mapfiles.models import DataFile, Feature, Attribute
from .exceptions import ProcessingException
from .exceptions import ShapefileException


class ProcessShapefile:
    
    def __init__(self, file_type):
        self.file_type = file_type
        # Common reference datums:
        self.REFERENCE_DATUMS = ("NAD27", "NAD83", "WGS84")

    def find_ref_datum(self, srs):
        """Goal: find the datum used in the layer's SRS by filtering 
        our common reference datums by year.

        If you add reference datums, keep in mind that this will
        look for the last two characters in order to pattern-match
        against the datum in the layer's SRS."""

        datums = {dat[-2:] : dat for dat in self.REFERENCE_DATUMS}
        key = next(filter(lambda d: d in srs['DATUM'], datums))
        return datums[key]

    def calc_geometry_field(self, geometry_type):
        """Return the proper geometry type used in the Feature model."""
        if geometry_type == "Polygon":
            return "geom_multipolygon"
        elif geometry_type == "LineString":
            return "geom_multilinestring"
        else:
            return "geom_" + geometry_type.lower()

    def wrap_GEOS_geometry(self, geometry):
        """Shapefiles use simpler geometries than our GeoDjango App
        will use, so we need to wrap those geometries. This comes 
        from the book Python for Geo-Spatial Development."""
        if geometry.geom_type == "Polygon":
            return MultiPolygon(geometry)
        elif geometry.geom_type == "LineString":
            return MultiLineString(geometry)
        else:
            return geometry        

    def get_path(self, file_id):
        """This method performs raw file processing and type-checking
        only. For the methods that import the data into the database once 
        the file(s) have been retrieved, see below.

        We are processing either a 'shapefile' or a 'shapefile_zip'        
        If it is a ZIP, we check to make sure all files are included."""
        ## This must be the only function that calls self.teardown()
        
        self.datafile = DataFile.objects.get(id=file_id)
        self.datafile.process_note = "Initiated datafile processing."
        self.datafile.save()
        self.file_path = self.datafile.stored_file.path

        if self.file_type == "shapefile_zip":
            self.shapefile_path = self.save_zip(self.file_path)

        elif self.file_type == "shapefile":
            self.shapefile_path = self.file_path

        else:
            err_msg = """Exception: this file went down the shapefile-processing
            path and yet the file type is listed as neither 'shapefile' nor
            'shapefile_zip'. How did it end up getting processed here?"""
            self.datafile.process_note = err_msg
            self.datafile.save()
            raise ProcessingException("Unknown filetype or archive uploaded.")

        return self.shapefile_path

    def save_zip(self, file_path):
        """Check for files required to make a proper shapefile
        zip archive and return None, error message if they are not
        present."""
        required_files = { ".shp",
                           ".shx",
                           ".dbf",
                           ".prj"} # This one's optional?
        self.zip_file = file_path
        if not zipfile.is_zipfile(self.zip_file):
            self.datafile.process_note = "Exception raised: Not a valid ZIP archive."
            self.datafile.save()
            raise ShapefileException("Not a valid zip archive")
        
        with zipfile.ZipFile(self.zip_file) as zipf:
            zipfiles = [name.lower() for name in zipf.namelist()]
            zip_extensions = set(os.path.splitext(x)[1] for x in zipfiles)
            
            if not required_files.issubset(zip_extensions):
                err_msg = "Exception raised: Archive missing the following file types: {}"
                err_msg = err_msg.format(" ".join(
                    required_files - zip_extensions))
                self.datafile.process_note = err_msg
                self.datafile.save()
                raise ShapefileException("Not a valid zip archive")
                
            else:
                self.tempdir = tempfile.mkdtemp()
                for fname in zipf.namelist():
                    fname_ext = os.path.splitext(fname)[1].lower()
                    if fname_ext in required_files:
                        zipf.extract(fname, path = self.tempdir) 
                    if fname_ext == '.shp':
                        shapefile_path = os.path.join(self.tempdir,
                                                      fname)
        self.datafile.process_note = "Shapefile found in zip. Processing shapefile."
        self.datafile.save()
        return shapefile_path


    def process_shapefile(self, file_path):
        """This is where the shapefile is processed and data is added
        to the models."""
        try:
            ds = DataSource(file_path)
            layer = ds[0]
        except (IOError, IndexError):
            self.datafile.process_note = "Either DataSource couldn't be created or layer could not be indexed. Check shapefile: does it have one data layer?"
            self.datafile.save()
            raise InvalidShapefile("Check shapefile.") 
        
        ## Process shapefile
        self.datafile.srs_wkt = layer.srs.wkt
        self.datafile.geom_type = layer.geom_type.name
        self.datafile.process_note = "Processing attributes and featuers."
        self.datafile.save()

        ## Find the field_name each feature will have and
        ## Prepopulate attribute information.
        attr_data = list(zip(layer.fields, 
                        map(lambda x : x.__name__, 
                            layer.field_types),
                        layer.field_widths, 
                        layer.field_precisions))

        ## Set up coordinate transformation to 4326.
        ## This is used to transform feature's geometry
        srs = SpatialReference(layer.srs.wkt)
        ct = CoordTransform(srs, SpatialReference(4326))

        ## Process features
        for feat_datum in layer:
            geo = feat_datum.geom
            geo.transform(ct)
            geometry = GEOSGeometry(geo.wkt)
            geometry = self.wrap_GEOS_geometry(geometry)
            geometry_field = self.calc_geometry_field(layer.geom_type.name)
            
            args = {}
            args['datafile'] = self.datafile
            args[geometry_field] = geometry
            model_feature = Feature(**args)
            model_feature.save()

            for attr in attr_data:
                if attr[0] in [f.decode('utf-8') 
                               for f in feat_datum.fields]:
                    val = str(feat_datum.get(attr[0]))
                else:
                    val = "None"

                attribute = Attribute(feature=model_feature,
                                      field_name = attr[0],
                                      attr_type = attr[1],
                                      width = attr[2],
                                      precision = attr[3],
                                      field_value = val)
                attribute.save()
        try:
            shutil.rmtree(self.tempdir)
        except FileNotFoundError:
            pass
