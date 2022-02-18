"""
Colophon filesystem directory functionality
"""
import os
from collections.abc import MutableMapping
import app

class FileInfo(MutableMapping):
    """File metadata for a file"""
    def __init__(self, filepath: str):
        self.file: dict = {}
        self.file['name'] = os.path.basename(filepath)
        self.file['path'] = os.path.dirname(filepath)
        fsplit = os.path.splitext(self.file['name'])
        self.file['base'] = fsplit[0]
        self.file['ext'] = fsplit[1][1:]
        fstat = os.stat(filepath)
        self.file['size'] = fstat.st_size
        # Has this file been associated with something in the manifest
        self.associated: bool = False

    def __iter__(self):
        for key in self.file:
            yield key

    def __len__(self):
        return len(self.key)

    def __getitem__(self, key):
        return self.file[key]

    def __setitem__(self, key, val):
        self.file[key] = val

    def __delitem__(self, key):
        del self.file[key]

    def __repr__(self):
        return f"FileInfo({os.path.join(self.file['path'], self.file['name'])}, size={self.file['size']}, associated={self.associated})"

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
        """Load filenames and filesystem metadata from the directory"""
        self.dirpath = dirpath if dirpath else self.dirpath
        self.filelist = None
        if not os.path.isdir(self.dirpath) or not os.access(self.dirpath, os.R_OK):
            raise app.ColophonException(f"Unable to read from specified directory: {self.dirpath}")
        self.filelist = {}
        for root, dirs, files in os.walk(self.dirpath):
            aroot = os.path.abspath(root)
            for filename in files:
                filepath = os.path.join(aroot,filename)
                self.filelist[filepath] = FileInfo(filepath)

    def __len__(self):
        return len(self.filelist) if self.filelist is not None else 0

    def __getitem__(self, key):
        return self.filelist[key]

    def __iter__(self):
        for fpair in self.filelist.items():
            yield fpair
