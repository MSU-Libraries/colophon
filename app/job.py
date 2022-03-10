"""
Colophon job running functionality
"""
import os
import tempfile
import zipfile
import app
from app.manifest import ManifestEntry
from app.suite import SuiteStage

class ColophonJob:
    """Class to organize steps in running a Colophon job"""

    @staticmethod
    def apply_filters():
        """Pass manifest through suite to filter out rows to ignore"""
        app.logger.debug("Applying suite filter to manifest...")
        for entry in app.manifest:
            entry.filtered = app.suite.filter(entry)
        app.logger.debug(
            f"Manifest rows: selected={app.manifest.filtered(False)}, "
            f"filtered={app.manifest.filtered(True)}"
        )

    @staticmethod
    def label_files():
        """For each manifest row, match/associate files to that row"""
        for entry in app.manifest:
            app.logger.debug(f"Labeling files for manifest row: {app.suite.manifest_id(entry)}")
            matched, failed = app.suite.label_files(entry)
            app.logger.debug(f"Files-found={matched}, failed-labels={failed}")
            if failed:
                fmsg = (
                    f"Manifest(id={app.suite.manifest_id(entry)}) encountered "
                    f"{failed} failures while creating file labels."
                )
                entry.failures.append(fmsg)
                app.logger.warning(fmsg)

    @classmethod
    def run_stages(cls):
        """For each manifest row, run scripts from stages"""
        for entry in app.manifest:
            if entry.filtered or entry.failures:
                continue
            try:
                cls._run_stages_on(entry)
            except app.EndStagesProcessing:
                pass

    @classmethod
    def _run_stages_on(cls, entry: ManifestEntry):
        """Run stages on a single entry"""
        mfid = app.suite.manifest_id(entry)
        for stage in app.suite.stages():
            app.logger.debug(f"Running Stage(stage={stage.name}, manifest-id={mfid})")
            stage_basedir = os.path.join(app.workdir, mfid, stage.name)
            try:
                cls._run_scripts_for(stage, stage_basedir, entry)
            except app.StageProcessingFailure:
                fmsg = (
                    f"Stage could not be processed (stage={stage.name}, manifest-id={mfid}); "
                    "see logs for details."
                )
                entry.failures.append(fmsg)
                app.logger.info(fmsg)

    @staticmethod
    def _run_scripts_for(stage: SuiteStage, stage_basedir: str, entry: ManifestEntry):
        """
        Run scripts for a stage
        Args:
            stage: The stage for which to run scripts
            stage_basedir: The directory where to write results of the script
            entry: The manifest entry to run the scripts with
        """
        for ready_script, stage_suffix in stage.script(entry):
            rcode = app.write_output(
                f"{stage_basedir}{stage_suffix}",
                *app.exec_command(ready_script, shell=True)
            )
            if rcode % 2 == 1:
                fmsg = f"Script failure (stage={stage.name}{stage_suffix}, exit={rcode}): {ready_script}"
                entry.failures.append(fmsg)
                app.logger.info(fmsg)
            if rcode & 16 == 16:
                fmsg = (
                    "Script set entry as filtered "
                    f"(stage={stage}{stage_suffix}, exit={rcode}): {ready_script}"
                )
                entry.filtered(fmsg)
                app.logger.info(fmsg)
                raise app.StopProcessing

    @staticmethod
    def generate_reports(strict: bool=False) -> int:
        """
        Do calls to compile reports and determine exit_code
        args:
            strict: If enabled, strict mode can affect the exit_code
        returns:
            The exit_code for the colophon run
        """
        app.logger.debug("Generating final manifest CSV.")
        app.report.ManifestReport().generate()

        app.logger.debug("Generating summary JSON report.")
        summary = app.report.SummaryReport()
        summary.generate()
        return summary.exit_code(strict)


    @staticmethod
    def zip_output():
        """Save all output as zip file"""
        with (
            tempfile.NamedTemporaryFile(prefix='colophon_', suffix='.zip', delete=False) as ztemp,
            zipfile.ZipFile(ztemp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zfile
        ):
            app.logger.debug(f"Bundling output into zip file: {ztemp.name}")
            for root, _, files in os.walk(app.workdir):
                for fname in files:
                    filepath = os.path.join(root, fname)
                    zfile.write(
                        filepath,
                        arcname=filepath.removeprefix(app.workdir).lstrip("/")
                    )

            # Return fullpath to zip file
            return ztemp.name
