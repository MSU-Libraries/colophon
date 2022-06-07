"""
Colophon file matching logic
"""
import app
from app.manifest import ManifestEntry
from app.directory import FileInfo
from app.helpers import value_match

class FileMatcher:
    """
    Attempt to match a file(s) for the given entry. If matched, label them in the global
    manifest and associated them in the global app Directory.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, entry: ManifestEntry, file_match: dict):
        self.files = []
        self.failures = []
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
        """Total number of matched files"""
        return len(self.files)

    def manifest_id(self):
        """Returns the rendered manifest_id for the current manifest entry"""
        return app.suite.manifest_id(self.entry)

    def _assert_linkedto_exists(self):
        if self.linkedto and self.linkedto not in self.entry:
            self.failures.append(
                f"Suite manifest.files has 'linkedto: {self.linkedto}', but the "
                f"'{self.linkedto}' field does not exist."
            )
        elif self.linkedto and not isinstance(self.entry[self.linkedto], list):
            self.failures.append(
                f"Suite manifest.files has 'linkedto: {self.linkedto}', but '{self.linkedto}' "
                "does not have 'multiple: true' set."
            )

    def _assert_valid_optional(self):
        if self.files_matched == 0 and not self.optional and not self.linkedto:
            self.failures.append(
                f"Manifest(id={self.manifest_id()}) was required to match a file "
                f"for label '{self.label}', but no matching file was found."
            )
        if self.linkedto and not self.optional and not all(self.files):
            self.failures.append(
                f"Manifest(id={self.manifest_id()}) was required to match files for "
                f"label '{self.label}', each being 'linkedto: {self.linkedto}', but not "
                "all linked files were found:\n { " + " }\n { ".join(map(
                    lambda x: f"{x[0]}: {x[1]}",
                    zip(self.entry[self.linkedto], self.files)
                )) + " }\n"
            )

    def _assert_valid_multiple(self):
        if self.files_matched > 1 and not self.multiple:
            self.failures.append(
                f"Manifest(id={self.manifest_id()}) matched muliple files for "
                f"'{self.label}' where only a single file match was allowed:"
                "\n - " + "\n - ".join(self.files)
            )

    def associate_file(self, finfo: FileInfo):
        """
        Set the given file as associated, or tag a failure if the file was already associated.
        """
        if finfo.associated:
            self.failures.append(
                f"Manifest(id={self.manifest_id()} matched an already associated file: {finfo}"
            )
        else:
            finfo.associated = self.manifest_id()
            self.entry.associated.append(finfo.filepath)

    @property
    def label(self):
        """Get the filematch label"""
        return self.fmatch['label']

    def set_label(self, value):
        """
        Set the label value in the current entry.
        Will be a list that is appended to if the match is designated as 'multiple: true'
        """
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
                    self.failures.append(
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

        # Default to empty
        if self.label not in self.entry:
            self.entry[self.label] = [] if self.multiple else None

        # Loop for files linked to another multiple-files match
        for link_idx in linked_idxs:
            entry_ctx = dict(self.entry)
            self.set_file(linked_idx=link_idx)
            # Only for list linked, get appropriate value at index
            if link_idx is not None:
                entry_ctx[self.linkedto] = entry_ctx[self.linkedto][link_idx]

            # Search all files to find a match
            try:
                for fpath, finfo in app.sourcedir:
                    context = {**entry_ctx, **{'file': dict(finfo)}}
                    if value_match(self.fmatch.get('value', '{{ file.name }}'), self.fmatch, context):
                        self.set_label(fpath)
                        self.associate_file(finfo)
                        self.set_file(filepath=finfo.filepath)
            except app.TemplateRenderFailure as exc:
                self.failures.append(
                    f"Encounted template render failure during file match for {self.manifest_id()}; "
                    f"stopping further file match attempts for this manifest entry. Error was: {exc}"
                )
            # For linked files, populate misses with null to indicate missed match
            if link_idx is not None and not self._linked_filepath:
                self.files.append(None)

        self._assert_valid_optional()
        self._assert_valid_multiple()
