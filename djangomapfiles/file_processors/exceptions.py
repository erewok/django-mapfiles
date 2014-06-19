"""Exceptions used by all of the different
processors"""


class ProcessingException(Exception):
    pass

class ShapefileException(ProcessingException):
    pass

class KmlException(ProcessingException):
    pass

class AcsException(ProcessingException):
    pass

class FileTooLarge(ProcessingException):
    pass
