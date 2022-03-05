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
        # State vars used while iterating to track if a linked file has been found or not
        self._linked_index = None
        self._linked_filepath = None

    @property
    def files_matched(self):
        return len(self.files)

    def manifest_id(self):
        return app.suite.manifest_id(self.entry)

    def _assert_linkedto_exists(self):
        if self.linkedto and self.linkedto not in self.entry:
            app.logger.error(
                f"Suite manifest.files has 'linkedto: {self.linkedto}', a field which does not exist."
            )
            self.failures += 1
        elif self.linkedto and not isinstance(self.entry[self.linkedto], list):
            app.logger.error(
                f"Suite manifest.files has 'linkedto: {self.linkedto}', but '{self.linkedto}' "
                "does not have 'multiple: true' set."
            )
            self.failures += 1

    def _assert_valid_optional(self):
        if self.files_matched == 0 and not self.optional:
            self.failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id()}) was required to match a file "
                f"for label '{self.label}', but no matching files were found."
            )
        if self.linkedto and not self.optional and not all(self.files):
            self.failures += 1
            app.logger.error(
                f"Manifest(id={self.manifest_id()}) was required and 'linkedto: {self.linkedto}' "
                f"for label '{self.label}', but not all linked files were found:"
                "\n - " + "\n - ".join(map(
                    lambda x: f"{x[0]}: {x[1]}",
                    zip(self.entry[self.linkedto], self.files)
                ))
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

    def set_file(self, linked_idx: int=None, filepath: str=None):
        """
        Set the state for file(s) found.
        args:
            linked_idx: Set to the index for a linkedto file, or None for non-linkedto
            filepath: The filepath to set for a file
        """
        # If no params, then reset
        if linked_idx is None and filepath is None:
            self._linked_index = None
            self._linked_filepath = None

        if linked_idx is not None:
            self._linked_index = linked_idx
            self._linked_filepath = None

        if filepath is not None:
            if self._linked_index is not None:
                # Trigger failure if attempting to set multiple files for linkedto index
                if bool(filepath) == bool(self._linked_filepath) == True:
                    self.failures += 1
                    app.logger.error(
                        f"Manifest(id={self.manifest_id()}) matched multiple files for "
                        f"linked '{self.label}' at index {self._linked_index}; "
                        f"previously matched: {self._linked_filepath}; "
                        f"ignoring additional match: {filepath}"
                    )
                # Found file for linkedto index with no previous path was set
                else:
                    self._linked_filepath = filepath
                    self.files.append(filepath)
            # Found a normal file (not linkedto)
            else:
                self.files.append(filepath)

    def process(self):
        """
        Run the file matching process
        """
        self._assert_linkedto_exists()

        # Default state is not linked to a list (i.e. single iteration)
        linked_idxs = [None]
        if isinstance(self.entry.get(self.linkedto), list):
            linked_idxs = range(len(self.entry[self.linkedto]))

        # Loop for files linked to another multiple-files match
        for link_idx in linked_idxs:
            entry_ctx = dict(self.entry)
            self.set_file(linked_idx=link_idx)
            # Only for list linked, get appropriate value at index
            if link_idx is not None:
                entry_ctx[self.linkedto] = entry_ctx[self.linkedto][link_idx]

            # Search all files to find a match
            for fpath, finfo in app.sourcedir:
                context = {**entry_ctx, **{'file': dict(finfo)}}
                if value_match(self.fmatch.get('value', '{{ file.name }}'), self.fmatch, context):
                    self.set_label(fpath)
                    self.associate_file(finfo)
                    self.set_file(filepath=finfo.filepath)
            # For linked files, populate misses with null to indicate missed match
            if link_idx is not None and not self._linked_filepath:
                self.files.append(None)

        self._assert_valid_optional()
        self._assert_valid_multiple()