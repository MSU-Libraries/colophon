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
        # Has file been associated with row in the manifest (empty string is unassociated)
        self.associated: str = ''

    @property
    def filepath(self):
        """Return the full filepath of file"""
        return os.path.join(self.file['path'], self.file['name'])

    def __iter__(self):
        for key in self.file:
            yield key

    def __len__(self):
        return len(self.file)

    def __getitem__(self, key):
        return self.file[key]

    def __setitem__(self, key, val):
        self.file[key] = val

    def __delitem__(self, key):
        del self.file[key]

    def __repr__(self):
        return f"FileInfo({self.filepath}, size={self.file['size']}, associated={self.associated})"

class Directory(MutableMapping):
    """
    The directory interaction wrapper
    """
    _instantiated: bool = False

    def __init__(self, dirpath: str=None):
        self.dirpath = None
        self.filelist = None
        if dirpath:
            self.load(dirpath)

    def chdir(self):
        """Change into the dirpath for the Directory"""
        if not self.dirpath:
            raise app.ColophonException("Cannot change directory path; path was never set.")

        app.logger.info(f"Change directory to: {self.dirpath}")
        # Change effective working directory to files sourcedir
        # This is to be able to have relative paths in output
        os.chdir(self.dirpath)

    def load(self, dirpath: str=None):
        """
        Change into directory given and load filenames and filesystem metadata
        from the directory"""
        if Directory._instantiated:
            raise app.ColophonException("Cannot have more than one Directory instance instantiated.")
        Directory._instantiated = True

        self.dirpath = dirpath.rstrip('/') if dirpath else self.dirpath
        if not os.path.isdir(self.dirpath) or not os.access(self.dirpath, os.R_OK):
            raise app.ColophonException(
                f"Unable to read from specified directory: {os.path.abspath(self.dirpath)}"
            )
        self.filelist = {}
        self.chdir()
        app.logger.info(f"Building file list for: {os.path.basename(self.dirpath)}")
        for root, _, files in os.walk('.'):
            for filename in files:
                filepath = os.path.join(root, filename).removeprefix("./")
                self.filelist[filepath] = FileInfo(filepath)
        app.logger.info(f"Loaded {self}")

    def files(self, associated: bool=True):
        """Iterate through files, returning only either associated/unassociated files"""
        for fpair in self:
            if bool(fpair[1].associated) == associated:
                yield fpair

    def __len__(self):
        return len(self.filelist) if self.filelist is not None else 0

    def __getitem__(self, key):
        return self.filelist[key]

    def __setitem__(self, key, val):
        self.filelist[key] = val

    def __delitem__(self, key):
        del self.filelist[key]

    def __iter__(self):
        for fpair in self.filelist.items():
            yield fpair

    def __repr__(self):
        return (
            f"Directory(dirname={os.path.basename(os.path.abspath(self.dirpath))}, "
            f"files={len(self.filelist)})"
        )
