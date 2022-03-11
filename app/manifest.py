"""
Colophon Manifest functionality
"""
import os
from collections.abc import MutableMapping, MutableSequence
import csv
import app

class ManifestEntry(MutableMapping):
    """Represent a single row in the Manifest"""
    def __init__(self, headers, values):
        self.rowmap = dict(zip(headers, values))
        # Filtered entries are skipped; reason for being skipped stored here
        self.filtered: str = ""
        # Ignored entries are skipped due to there being no files matched.
        self.ignored: bool = False
        # Failure messages should any failures occur for this entry
        self.failures: list = []
        # List of files associated with this entry
        self.associated: list = []

    @property
    def skipped(self):
        """Returns True if entry is either filtered or skipped"""
        return bool(self.filtered) or self.ignored

    def headers(self) -> list:
        """Keys for this row as a list"""
        return list(self.rowmap.keys())

    def values(self) -> list:
        """Values for this row as a list"""
        return list(self.rowmap.values())

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
        return (
            f"ManifestEntry({self.rowmap}, files={len(self.associated)}, "
            f"filtered={bool(self.filtered)}, ignored={self.ignored})"
        )

class Manifest(MutableSequence):
    """The Manifest file wrapper"""
    def __init__(self, filepath: str=None):
        self.filepath = None
        self.headers = None
        self.manifest = None
        if filepath:
            self.load(filepath)

    def load(self, filepath: str=None):
        """Load the manifest file"""
        self.filepath = filepath.rstrip('/') if filepath else self.filepath
        self.headers = None
        self.manifest = None
        try:
            with open(self.filepath, newline='', encoding='utf8') as mffile:
                csvr = csv.reader(mffile, dialect='unix')
                self.manifest = []
                for row in csvr:
                    if self.headers is None:
                        self.headers = row
                        continue
                    if len(row) != len(self.headers):
                        raise app.ColophonException(
                            f"Column count in row {len(self.manifest)+2} does not match header."
                        )
                    self.manifest.append(ManifestEntry(self.headers, row))
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open manifest - file missing: {self.filepath}") from None
        app.logger.info(f"Loaded {self}")

    def __getitem__(self, idx: int):
        return self.manifest[idx]

    def __setitem__(self, idx, entry):
        self.manifest[idx] = entry

    def __delitem__(self, idx):
        del self.manifest[idx]

    def __len__(self):
        return len(self.manifest)

    def selected(self):
        """
        Returns the number count of manifest entries that were not skipped.
        """
        return len(self.manifest) - self.skipped()

    def skipped(self, *, filtered: bool=True, ignored: bool=True):
        """
        Return the number count of manifest entires skipped based on their status
        Args:
            filtered: If True (default), will include entries that have been filtered in the count
            ignored: If True (default), will include entries that have been ignored in the count
        """
        return len([
            0 for _ in self.manifest
            if (
                bool(_.filtered) == filtered == True
                or _.ignored == ignored == True
            )
        ])

    def insert(self, index, value):
        """Insert a new manifest entry at the given index"""
        self.manifest.insert(index, value)

    def __repr__(self):
        return (
            f"Manifest(filename={os.path.basename(self.filepath)}, "
            f"fields={len(self.headers)}, datarows={len(self.manifest)})"
        )
