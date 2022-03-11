"""
Colophon test Suite functionality
"""
import os
from copy import deepcopy
import yaml
import cerberus
import app
from app.template import render_template_string
from app.manifest import ManifestEntry
from app.filematch import value_match, FileMatcher
from schemas import suite

class SuiteStage:
    """A Stage within the suite"""
    def __init__(self, name, stage):
        self.name = name
        self.raw_script = stage["script"]
        self.loopvars = stage.get("loopvars", [])

    def script(self, context):
        """
        Run the script for the given context, looping over loopvars if set, yielding the result(s).
        yields:
            tuple(
                ready_script_string: The rendered string, ready to execute
                stage_suffix: A suffix string to append to the stage when using loopvar
            )
        """
        pairs = [] if self.loopvars else [(context, '')]
        if self.loopvars:
            varcount = None
            for loopvar in self.loopvars:
                # Verify all loopvars exist in context
                if loopvar not in context or not isinstance(context[loopvar], list):
                    fmsg = (
                        f"Unable to process stage '{self.name}'; loopvar "
                        "'{loopvar}' must be a 'multiple: true' field."
                    )
                    app.logger.error(fmsg)
                    app.StageProcessingFailure(fmsg)
                # Verify all loopvars are of the same length
                if varcount and varcount != len(context[loopvar]):
                    fmsg = (
                        f"Unable to process stage '{self.name}'; loopvar "
                        f"'{loopvar}' length ({len(context[loopvar])}) does "
                        f"not match other loopvars ({varcount})."
                    )
                    app.logger.error(fmsg)
                    app.StageProcessingFailure(fmsg)
                varcount = len(context[loopvar])

            for idx in range(varcount):
                # Copy context and set loopvar to appropriate index for given loop
                loopctx = deepcopy(context)
                for loopvar in self.loopvars:
                    loopctx[loopvar] = loopctx[loopvar][idx]
                pairs.append((loopctx, f".{idx}"))

        for ctx, suf in pairs:
            yield render_template_string(self.raw_script, {**ctx, **app.globalctx}, shell=True), suf

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
            with open(self.filepath, encoding='utf8') as mf_file:
                self.suite = yaml.load(mf_file, Loader=yaml.CLoader)
        except FileNotFoundError:
            raise app.ColophonException(f"Unable to open suite - file missing: {self.filepath}") from None
        except yaml.parser.ParserError:
            raise app.ColophonException("Unable to parse suite -- invalid YAML.") from None

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
            matcher = FileMatcher(entry, fmatch)
            matcher.process()
            total_files += matcher.files_matched
            total_failures += matcher.failures
        return total_files, total_failures

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
