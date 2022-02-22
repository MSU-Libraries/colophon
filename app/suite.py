"""
Colophon test Suite functionality
"""
import os
import re
import yaml
import cerberus
import jinja2
import app
from app.template import render_template_string
from app.manifest import ManifestEntry
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

class SuiteStage:
    """A Stage within the suite"""
    def __init__(self, name, stage):
        self.name = name
        self.raw_script = stage['script']

    def script(self, context):
        return render_template_string(self.raw_script, {**context, **app.globalctx}, shell=True)

    def __repr__(self):
        return f"SuiteStage({self.name}, script={self.raw_script})"

class Suite:
    """
    The Suite interface
    """
    def __init__(self, filepath: str=None):
        self.filepath = None
        self.suite = None
        if filepath:
            self.load(filepath)

    def load(self, filepath: str=None):
        """Load and validate the suite file"""
        self.filepath = filepath.rstrip('/') if filepath else self.filepath
        self.suite = None
        try:
            with open(self.filepath) as mf_file:
                self.suite = yaml.load(mf_file, Loader=yaml.CLoader)
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open suite - file missing: {self.filepath}") from None
        except yaml.parser.ParseError:
            raise app.ColophonException(f"Unable to parse suite -- invalid YAML.") from None

        # Assert structure
        cerbval = cerberus.Validator(suite)
        if not cerbval.validate(self.suite):
            raise app.ColophonException(f"Invalid suite structure: {cerbval.errors}")
        app.logger.info(f"Loaded {self}")

    def manifest_id(self, manifest_entry: ManifestEntry) -> str:
        """
        Get the identifier string for an entry. The id is a string that should uniquely identify
        a manifest row
        """
        return render_template_string(self.suite['manifest']['id'], manifest_entry).replace('/','_')

    def filter(self, entry: ManifestEntry) -> bool:
        """
        Given a manifest row, determine if the row should be filtered (that is, excluded) from
        from this suite of tests.
        args:
            entry: The entry to check
        returns:
            True if row has been filtered/excluded based on the suite filters
        """
        filters = self.suite['manifest']['filter'] if 'filter' in self.suite['manifest'] else []
        filtered = False
        for filt in filters:
            if not value_match(entry[filt['value']], filt, entry):
                filtered = True
                break
        return filtered

    def label_files(self, entry: ManifestEntry) -> tuple[int,int]:
        """
        Given a manifest row and having already loaded a Directory of files, this finds
        matching files from and label them into them manifest.
        Will mark them as associated in the Directory if labeled.
        args:
            entry: The entry find label matches for
        returns:
            A tuple containing:
              - A count of matched files
              - A count of the number of failures to match files
        """
        file_matches = self.suite['manifest']['files']
        total_files, failures = 0, 0
        for fmat in file_matches:
            value = fmat.get('value', '{{ file.name }}')
            optional = fmat.get('optional', False)
            multiple = fmat.get('multiple', False)
            label = fmat['label']
            entry[label] = [] if multiple else None
            files_found = []
            for fpath, fentry in app.sourcedir:
                context = {**entry, **{'file': dict(fentry)}}
                if value_match(value, fmat, context):
                    files_found.append(fentry.filepath)
                    # set label in manifest
                    if multiple:
                        entry[label].append(fpath)
                    else:
                        entry[label] = fpath
                    # mark file as associated
                    if fentry.associated:
                        failures += 1
                        app.logger.error(
                            f"Manifest(id={self.manifest_id(entry)} matched a file, but was already associated: {fpath}"
                        )
                        break
                    fentry.associated = True
            if len(files_found) == 0 and not optional:
                failures += 1
                app.logger.error(
                    f"Manifest(id={self.manifest_id(entry)} was required to match a file "
                    f"for label {label}, but no matching files were found."
                )
            if len(files_found) > 1 and not multiple:
                failures += 1
                app.logger.error(
                    f"Manifest(id={self.manifest_id(entry)} matched muliple files for "
                    f"{label} where only a single file match was allowed:"
                    "\n - " + "\n - ".join(files_found)
                )
            total_files += len(files_found)
        return total_files, failures

    def stages(self):
        """Iterate and return SuiteStage instances for each stage"""
        for name in self.suite['stages']:
            yield SuiteStage(name, self.suite['stages'][name])

    def __repr__(self):
        return (
            f"Suite(filename={os.path.basename(self.filepath)}, "
            f"filters={len(self.suite['manifest'].get('filter', []))}, "
            f"files={len(self.suite['manifest']['files'])}, "
            f"stages={len(self.suite['stages'])})"
        )
