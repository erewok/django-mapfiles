import os

from django.test import TestCase

from selenium import webdriver

from mapfiles.file_processors.shapefile_processor import ProcessShapefile
from .exceptions import ProcessingException
from .exceptions import InvalidShapefile
from .exceptions import IncompleteShapefileZipArchive

class ShapefileImportTest(TestCase):
    
    def setUp(self):
        ## The test files must be supplied
        self.testfile = os.path.abspath("testshapefile.shp")
        self.testzip = os.path.abspath("testzip.zip")
        if not os.path.exists(self.testfile):
            self.fail("Please put testing files into testing directory")
        if not os.path.exists(self.testzip):
            self.fail("Please put testing files into testing directory")
        self.processor = ProcessShapefile()
        # This guy is probably going to need a datafile object to interact with

    def test_zip_writing(self):
        shapefile = self.processor.save_zip(self.testzip)
        with self.raises(IncompleteShapefileZipArchive):
            self.processor.save_zip(self.testfile)

    def test_processing(self):
        pass

    def test_item_upload_process(self):
        pass
        # how to upload through selenium and check back on processing?
        ## This one should go in the actual database
    
