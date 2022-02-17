"""
Colophon test Suite functionality
"""
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
            raise app.ColophonException(f"Invalid suite structure: {v.errors}")
