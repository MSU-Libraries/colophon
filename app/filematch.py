"""
Colophon file matching logic
"""
import re
import app
from app.template import render_template_string
from app.manifest import ManifestEntry
from app.directory import FileInfo

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


class FileMatcher:
    """
    Attempt to match a file(s) for the given entry. If matched, label them in the global
    manifest and associated them in the global app Directory.
    """
    def __init__(self, entry: ManifestEntry, file_match: dict):
        self.files = []
        self.failures = 0
        self.entry = entry
        self.fmatch = file_match
        self.optional = self.fmatch.get('optional', False)
        self.linkedto = self.fmatch.get('linkedto', None)
        self.multiple = (
            self.fmatch.get('multiple', False)
            or isinstance(self.entry.get(self.linkedto), list)
        )

    @property
    def files_matched(self):
        return len(self.files)

    def manifest_id(self):
        return app.suite.manifest_id(self.entry)

    def _assert_linkedto_exists(self):
        if self.linkedto and self.linkedto not in self.entry:
            app.logger.error(
                f"Suite manifest.files references 'linkedto: {linkedto}' which does not exist."
            )
            self.failures += 1

    def _assert_valid_optional(self):
        if self.files_matched == 0 and not self.optional:
            self.failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id()}) was required to match a file "
                f"for label '{self.label}', but no matching files were found."
            )

    def _assert_valid_multiple(self):
        if self.files_matched > 1 and not self.multiple:
            self.failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id()}) matched muliple files for "
                f"'{self.label}' where only a single file match was allowed:"
                "\n - " + "\n - ".join(self.files)
            )

    def associate_file(self, finfo: FileInfo):
        if finfo.associated:
            self.failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id()} matched an already associated file: {finfo}"
            )
        else:
            finfo.associated = self.manifest_id()

    @property
    def label(self):
        return self.fmatch['label']

    def set_label(self, value):
        if self.label not in self.entry:
            self.entry[self.label] = [] if self.multiple else None

        if self.multiple:
            self.entry[self.label].append(value)
        else:
            self.entry[self.label] = value

    def process(self):
        self._assert_linkedto_exists()

        for fpath, finfo in app.sourcedir:
            context = {**self.entry, **{'file': dict(finfo)}}
            if value_match(self.fmatch.get('value', '{{ file.name }}'), self.fmatch, context):
                self.files.append(finfo.filepath)
                self.set_label(fpath)
                self.associate_file(finfo)

        self._assert_valid_optional()
        self._assert_valid_multiple()
