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
        return f"SuiteStage({self.name})"

class Suite:
    """
    The Suite file wrapper
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

    def filter(self, entry: ManifestEntry) -> str:
        """
        Given a manifest row, determine if the row should be filtered (that is, excluded) from
        from this suite of tests.
        args:
            entry: The entry to check
        returns:
            A string message describing why the row has been filtered/excluded, or empty string otherwise
        """
        filters = self.suite['manifest']['filter'] if 'filter' in self.suite['manifest'] else []
        filtered = ""
        for filt in filters:
            if not value_match(entry[filt['value']], filt, entry):
                filtered = f"Filter did not match: {filt}"
                break
        return filtered

    def label_files(self, entry: ManifestEntry) -> tuple[int,int]:
        """
        Given a manifest row, perform matches for all 'manifest.files' entries
        from the suite.
        args:
            entry: The entry find label matches for
        returns:
            A tuple containing:
              - A count of matched files
              - A count of the number of failures to match files
        """
        file_matches = self.suite['manifest']['files']
        total_files, total_failures = 0, 0
        for fmatch in file_matches:
            file_count, failures = self._match_label_files(entry, fmatch)
            total_files += file_count
            total_failures += failures
        return total_files, total_failures

    def _match_label_files(self, entry: ManifestEntry, fmatch: dict) -> tuple[int,int]:
        """
        Given a manifest row entry and having already loaded a Directory of files,
        this finds matching file(s) for a single suite 'manifest.files' entry and then
        adds the label for the match into them manifest with the associated file(s).
        Marks any associated files as such in the Directory once labeled.
        args:
            entry: The entry find a match for
            fmatch: A file match entry from the suite's manifest.files
        returns:
            A tuple containing:
              - A count of matched files
              - A count of the number of failures encountered
        """
        optional = fmatch.get('optional', False)
        multiple = fmatch.get('multiple', False)
        label = fmatch['label']
        entry[label] = [] if multiple else None
        files, failures = [], 0
        for fpath, fentry in app.sourcedir:
            context = {**entry, **{'file': dict(fentry)}}
            if value_match(fmatch.get('value', '{{ file.name }}'), fmatch, context):
                files.append(fentry.filepath)
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
        if len(files) == 0 and not optional:
            failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id(entry)} was required to match a file "
                f"for label {label}, but no matching files were found."
            )
        if len(files) > 1 and not multiple:
            failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id(entry)} matched muliple files for "
                f"{label} where only a single file match was allowed:"
                "\n - " + "\n - ".join(files)
            )
        return len(files), failures

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
