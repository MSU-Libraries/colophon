"""
Colophon Manifest functionality
"""
import cerberus
import app

class Manifest:
    """
    The Manifest file interface
    """
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.manifest = None
        if self.filepath:
            self.load()

    def load(self, filepath=None):
        self.filepath = filepath if filepath else self.filepath
        self.manifest = None
        try:
            with open(self.filepath) as mffile:
                # TODO load CSV
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open manifest - file missing: {self.filepath}") from None
        except Exception: #TODO CSV parse exception
            raise app.ColophonException(f"Unable to parse manifest -- invalid YAML.") from None

        # Assert structure
        #TODO
