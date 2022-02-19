"""
Colophon test Suite functionality
"""
import re
import yaml
import cerberus
import jinja2
import app
from app.template import render_template_string
from schemas import suite

def value_match(value: str, conditions: dict, context: dict = {}):
    """
    Check if the value meets all passed conditions
    """
    matched = True
    ignorecase = conditions.get('ignorecase', False)
    def prep(string):
        """Preprocess string before comparison"""
        string = render_template_string(string, context)
        return string.lower() if ignorecase else string

    for ckey, cval in conditions.items():
        if ckey == 'equals':
            matched &= prep(value) == prep(cval)
        elif ckey == 'startswith':
            matched &= prep(value).startswith(prep(cval))
        elif ckey == 'endswith':
            matched &= prep(value).endswith(prep(cval))
        elif ckey == 'regex':
            matched &= re.search(cval, prep(value), re.IGNORECASE if ignorecase else 0) is not None
    return matched

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

    def filter(self, rowmap: dict) -> bool:
        """
        Given a manifest row, determine if the row should be filtered (that is, excluded) from
        from this suite of tests.
        args:
            rowmap: A row mapping (of header: value) from the manifest
        returns:
            True if row should be filtered/excluded based on the suite filters
        """
        filters = self.suite['manifest']['filter'] if 'filter' in self.suite['manifest'] else []
        filtered = False
        for filt in filters:
            if not value_match(rowmap[filt['value']], filt, rowmap):
                filtered = True
                break
        return filtered

    def label_files(self, rowmap: dict) -> int:
        """
        Given a manifest row and having already loaded a Directory of files, this finds
        matching files from and label them into them manifest.
        Will mark them as associated in the Directory if labeled.
        args:
            rowmap: A row mapping (of header: value) from the manifest
        returns:
            A count of the number of failures to match/label files, or 0 if no failures
        """
        file_matches = self.suite['manifest']['files']
        failures = 0
        for fmat in file_matches:
            value = fmat.get('value', '{{ file.name }}')
            optional = fmat.get('optional', False)
            multiple = fmat.get('multiple', False)
            label = fmat['label']
            rowmap[label] = [] if multiple else None
            files_found = 0
            for fpath, fentry in app.sourcedir:
                context = {**rowmap, **{'file': dict(fentry)}}
                if value_match(value, fmat, context):
                    # set label in manifest
                    if multiple:
                        rowmap[label].append(fpath)
                    else:
                        rowmap[label] = fpath
                    # mark file as associated
                    if fentry.associated:
                        # TODO log more info
                        raise app.ColophonException(f"File matched on {dict(rowmap)}, but was already associated: {fpath}")
                    fentry.associated = True
                    files_found += 1
            if files_found == 0 and not optional:
                #TODO log and failures += 1
                raise app.ColophonException(f"No file matched on {dict(rowmap)} for {fmat}")
            if files_found > 1 and not multiple:
                #TODO log and failures += 1
                raise app.ColophonException(f"Multiple files matched on {dict(rowmap)} for {fmat}")
        return failures
