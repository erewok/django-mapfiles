import csv
import os
import requests
import json

from django.contrib.gis.geos import GEOSGeometry

from djangomapfiles.models import DataFile, Feature, Attribute
from .exceptions import AcsException


class ProcessAcs:
    
    def __init__(self, file_type):
        self.file_type = file_type

        ## Census Geographic JSON API
        ## Use the following url to retrieve geographic boundaries:
        ## http://census.ire.org/geo/1.0/boundary-set/{geography-type}/{geoid}
        self.ire_census_url = "http://census.ire.org/geo/1.0/boundary-set/{0}/{1}"

    def get_path(self, file_id):
        """This method performs raw file processing and type-checking
        only. For the methods that import the data into the database once 
        the file has been retrieved, see below.

        Here we are processing an American Community Survey .csv file."""
     
        self.datafile = DataFile.objects.get(id=file_id)
        self.datafile.process_note = "Initiated datafile processing."
        self.datafile.save()
        self.file_path = self.datafile.stored_file.path
        *file_path, extension = os.path.splitext(self.file_path)
        if extension == ".zip":
            self.datafile.process_note = "Zip archive found: please unpack zip and upload csv with named fields."
            self.datafile.save()
            raise AcsException("Please unpack your zip archive and upload a csv.")

        elif extension == ".csv":
            self.acs_filepath = self.file_path
            if os.path.exists(self.acs_filepath):
                self.datafile.process_note = "Located datafile for processing."
                self.datafile.save()
            else:
                err_msg = "File does not exist. Was it deleted?"
                self.datafile.process_note = err_msg
                self.datafile.save()
                raise DataFileException("File does not exist")

        else:
            err_msg = """Exception: this file went down the acs-processing
            path and yet the file extension is neither '.csv' nor
            '.zip'. How did it end up getting processed here?"""
            self.datafile.process_note = err_msg
            self.datafile.save()
            raise DataFileException("Unknown filetype or archive uploaded.")

        return self.acs_filepath

    def parse_csv(self, file_path):
        with open(file_path, 'r') as f:
            self.datafile.process_note = "File opened for parsing..."
            self.datafile.save()
            feats = 0
            # They usually use numeric ids for first row field names.
            # We are tossing this first row and using the text fields 
            # instead; IF there are weird results, check that uploaded
            # file has fieldnames.      
            _ = next(f)
            dictread = csv.DictReader(f)
            for row in dictread:
                geo_id = row['Id2']
                feat = self.process_feature(geo_id)
                if feat:
                    feats += 1 
                    self.process_attributes(feat, row)
            self.datafile.process_note = "{0} features in file processed.".format(feats)
            self.datafile.save()

    def process_feature(self, geo_id):
        feature_type = "Census {}".format(self.file_type)

        if Feature.objects.filter(reference = feature_type, 
                                  federal_geo_id = geo_id).exists():
            already_saved_feature = Feature.objects.filter(
                reference = feature_type, 
                federal_geo_id = geo_id).first()
            geo_object = already_saved_feature.geom_multipolygon
            new_feature = Feature(datafile = self.datafile,
                                  reference = feature_type,
                                  federal_geo_id = geo_id,
                                  geom_multipolygon = geo_object)
            new_feature.save()

        else:
            shape = self.get_geo_boundaries(geo_id)
            if shape:
                geo_object = GEOSGeometry(json.dumps(shape))
                new_feature = Feature(datafile = self.datafile,
                                      reference = feature_type,
                                      federal_geo_id = geo_id,
                                      geom_multipolygon = geo_object)
                new_feature.save()
            else:
                return False

        return new_feature
        

    def get_geo_boundaries(self, federal_geo_id):
        url = self.ire_census_url.format(self.file_type, federal_geo_id)
        result = requests.get(url)
        if result.status_code == 200:
            payload = result.json()
            shape = payload['simple_shape']
            return shape
        else:
            return False

    def process_attributes(self, feat, attr_dict):
        for key in attr_dict:
            attribute = Attribute(feature=feat,
                                  field_name = key,
                                  attr_type = "",
                                  field_value = attr_dict[key])
            attribute.save()

