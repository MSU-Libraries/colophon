"""
Colophon filesystem directory functionality
"""
import os
import app

class Directory:
    """
    The directory interface
    """
    def __init__(self, dirpath=None):
        self.dirpath = dirpath
        self.filelist = None
        if self.dirpath:
            self.load()

    def load(self, dirpath=None):
        self.dirpath = dirpath if dirpath else self.dirpath
        self.filelist = None
        if not os.path.isdir(self.dirpath) or not os.access(self.dirpath, os.R_OK):
            raise app.ColophonException(f"Unable to read from specified directory: {self.dirpath}")
        self.filelist = {}
        for root, dirs, files in os.walk(self.dirpath):
            for filename in files:
                self.filelist[os.path.join(root,filename)] = 'STAT dataclass?'
