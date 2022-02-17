"""
Colophon filesystem directory functionality
"""
import os
import app

class FileInfo:
    """File metadata for a file"""
    def __init__(self, filepath: str):
        self.filename: str = os.path.basename(filepath)
        self.path: str = os.path.dirname(filepath)
        fsplit = os.path.splitext(self.filename)
        self.basename: str = fsplit[0]
        self.ext: str = fsplit[1]
        fstat = os.stat(filepath)
        self.size: int = fstat.st_size

    def __repr__(self):
        return f"FileInfo({os.path.join(self.path, self.filename)}, {self.size})"

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
