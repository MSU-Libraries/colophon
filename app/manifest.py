"""
Colophon Manifest functionality
"""
from collections.abc import MutableMapping, MutableSequence
import csv
import cerberus
import app

class ManifestEntry(MutableMapping):
    def __init__(self, headers, values):
        # Filtered entries are to be ignored
        self.filtered = False
        self.rowmap = dict(zip(headers, values))

    def __iter__(self):
        for key in self.rowmap:
            yield key

    def __len__(self):
        return len(self.rowmap)

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.rowmap.values())[key]
        return self.rowmap[key]

    def __setitem__(self, key, val):
        self.rowmap[key] = val

    def __delitem__(self, key):
        del self.rowmap[key]

    def __repr__(self):
        return f"ManifestEntry({self.rowmap}, filtered={self.filtered})"

class Manifest(MutableSequence):
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
                    self.manifest.append(ManifestEntry(self.headers, row))
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open manifest - file missing: {self.filepath}") from None

    def __getitem__(self, idx: int):
        return self.manifest[idx]

    def __setitem__(self, idx, entry):
        self.manifest[idx] = entry

    def __delitem__(self, idx):
        del self.manifest[idx]

    def __len__(self):
        return len(self.manifest)

    def insert(self, idx, entry):
        self.manifest.insert(idx, entry)

    #def __iter__(self):
    #    for row_idx in range(len(self.manifest)):
    #        yield self[row_idx]
