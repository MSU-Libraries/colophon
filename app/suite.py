"""
Colophon test Suite functionality
"""
import re
import yaml
import cerberus
import app
from schemas import suite

class Suite:
    """
    The Suite interface
    """
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.suite = None
        if self.filepath:
            self.load()

    def load(self, filepath=None):
        """Load and validate the suite file"""
        self.filepath = filepath if filepath else self.filepath
        self.suite = None
        try:
            with open(self.filepath) as mffile:
                self.suite = yaml.load(mffile, Loader=yaml.CLoader)
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open suite - file missing: {self.filepath}") from None
        except yaml.parser.ParseError:
            raise app.ColophonException(f"Unable to parse suite -- invalid YAML.") from None

        # Assert structure
        cerbval = cerberus.Validator(suite)
        if not cerbval.validate(self.suite):
            raise app.ColophonException(f"Invalid suite structure: {cerbval.errors}")

    def filter(self, row: dict) -> bool:
        """
        Given a manifest row, determine if the row should be filtered (that is, excluded) from
        from this suite of tests.
        args:
            row: A row from the manifest
        returns:
            True if row should be filtered/excluded based on the suite filters
        """
        filters = self.suite['manifest']['filter'] if 'filter' in self.suite['manifest'] else []
        filtered = False
        tolower = lambda val, low: val.lower() if low else val
        for filt in filters:
            colval, re_flags, low = row[filt['label']], 0, False
            if 'ignorecase' in filt and filt['ignorecase']:
                colval, re_flags, low = colval.lower(), re.IGNORECASE, True

            if 'equals' in filt and colval != tolower(filt['equals'], low):
                filtered = True
                break
            if 'startswith' in filt and not colval.startswith(tolower(filt['startswith'])):
                filtered = True
                break
            if 'endswith' in filt and not colval.endswith(tolower(filt['endswith'])):
                filtered = True
                break
            if 'regex' in filt and not re.search(filt['regex'], colval, re_flags):
                filtered = True
                break
        return filtered
