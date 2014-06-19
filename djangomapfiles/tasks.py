"""This tasks file is for asynchronously
digesting and processing uploaded geographic data
files. 

It uses the database model to examine  
"""
from celery import task

from .file_processors import shapefile_processor
from .file_processors import acs_processor
# from .file_processors import kml_processor
from .file_processors.set_center import set_center

from .models import DataFile, Feature

@task
def process_files(model_id, file_type):
    processor = FileProcessor(model_id, file_type)
    processor.process()
    processor.set_default_center()


## API Goals: Everything this guy calls should
## raise exceptions on any problem
## those exceptions should be emailed and should
## log themselves inside the database object's notes/comments field

class FileProcessor:

    def __init__(self, model_id, file_type):
        self.model_id = model_id
        self.file_type = file_type
        self._router()

    def _router(self):
        self.types = { "tracts": self.process_acs_datafile,
                       "county-subdivisions": self.process_acs_datafile,
                       "counties": self.process_acs_datafile,
                       "states": self.process_acs_datafile,
                       "places": self.process_acs_datafile,
                       "kml": self.process_kml_file,
                       "kmz": self.process_kml_file,
                       "shapefile": self.process_shapefile,
                       "shapefile_zip": self.process_shapefile }
        self.process = self.types[self.file_type]

    def process_shapefile(self):
        file_processor = shapefile_processor.ProcessShapefile(self.file_type)
        shapefile = file_processor.get_path(self.model_id)
        file_processor.process_shapefile(shapefile)


    def process_acs_datafile(self):
        file_processor = acs_processor.ProcessAcs(self.file_type)
        acs_file = file_processor.get_path(self.model_id)
        file_processor.parse_csv(acs_file)

    def process_kml_file(self):
        pass

        
    def set_default_center(self):
        file_features = Feature.objects.filter(datafile__id=self.model_id)
        if file_features: 
            center_point = set_center(file_features)
            self.datafile = DataFile.objects.get(id=self.model_id)
            self.datafile.default_center = center_point
            self.datafile.process_note = "Center point saved. Processing complete."
        else: 
            self.datafile.process_note = "No Features saved. Center could not be processed."
        self.datafile.processed = True
        self.datafile.save()




