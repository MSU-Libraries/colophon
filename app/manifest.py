"""
Colophon Manifest functionality
"""
import csv
import cerberus
import app

class Manifest:
    """
    The Manifest file interface
    """
    def __init__(self, filepath: str=None):
        self.filepath = filepath
        self.headers = None
        self.manifest = None
        if self.filepath:
            self.load()

    def load(self, filepath: str=None):
        """Load the manifest file"""
        self.filepath = filepath if filepath else self.filepath
        self.headers = None
        self.manifest = None
        try:
            with open(self.filepath, newline='') as mffile:
                csvr = csv.reader(mffile, dialect='unix')
                self.manifest = []
                for row in csvr:
                    if self.headers is None:
                        self.headers = row
                        continue
                    if len(row) != len(self.headers):
                        raise app.ColophonException(f"Column count in row {len(self.manifest)+2} does not match header.")
                    self.manifest.append(row)
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open manifest - file missing: {self.filepath}") from None

    def __getitem__(self, row: int):
        return dict(zip(self.headers, self.manifest[row]))

    def __iter__(self):
        for row in range(len(self.manifest)):
            yield self[row]
