"""
Colophon reports and other output files
"""
import os
import csv
import json
import shutil
from datetime import datetime
from collections import defaultdict
import app
from app.helpers import ExitCode
from app.template import render_template_string

class ManifestReport:
    """Report for files left unassociated"""
    @staticmethod
    def generate(savedir: str=None, filename: str="manifest.csv"):
        """Create report and save in workdir"""
        savedir = savedir if savedir else app.workdir
        # pylint: disable=unsubscriptable-object
        mfrows = [max(app.manifest, key=len).headers() if len(app.manifest) else app.manifest.headers]
        for entry in app.manifest:
            mfrows.append(entry.values())
        mfcsv_path = os.path.join(app.workdir, filename)
        with open(mfcsv_path, 'w', newline='', encoding='utf8') as mfcsv_file:
            mfcsv = csv.writer(mfcsv_file, quoting=csv.QUOTE_ALL)
            mfcsv.writerows(mfrows)

class IgnoredReport:
    """Report for files left unassociated"""
    @staticmethod
    def generate(savedir: str=None, filename: str="ignored.json"):
        """Create report and save in workdir"""
        savedir = savedir if savedir else app.workdir
        ignored = []

        for entry in app.manifest:
            mfid = app.suite.manifest_id(entry)
            if entry.ignored:
                ignored.append(mfid)

        ignored_path = os.path.join(app.workdir, filename)
        with open(ignored_path, 'w', encoding='utf8') as ignored_file:
            json.dump(ignored, ignored_file, indent=2)
            ignored_file.write('\n')

def ecode_counts(search_dir: str):
    """
    Given a directory, find all files in the form "ecode.N"
    where N is a return code. Return a dict of key N to the
    count of matching files grouped by N.
    """
    ecodes = defaultdict(int)
    for _, _, files in os.walk(search_dir):
        for fname in files:
            if fname.startswith("ecode."):
                ecodes[fname.removeprefix("ecode.")] += 1
    return dict(ecodes)

class SummaryReport:
    """Summary report of overall run"""
    def __init__(self):
        self.failed = None
        self.skipped = None
        self.unassociated = None

    def generate(self, savedir: str=None, filename: str="summary.json"):
        """Create report and save in workdir"""
        savedir = savedir if savedir else app.workdir
        summary = {
            'row-overview': {},
            'skipped': [],
            'failed': [],
            'unassociated-files': [],
            'rows': {}
        }

        ignored = 0
        for entry in app.manifest:
            if entry.ignored:
                ignored += 1
                continue
            mfid = app.suite.manifest_id(entry)

            # Exit-code summary per row
            summary['rows'][mfid] = (row := {})
            if (exit_codes := ecode_counts(os.path.join(app.workdir, mfid))):
                ec_details = {
                    ec_val: {
                        "occurrences": ec_cnt,
                        "code-meaning": str(ExitCode(ec_val)),
                    }
                    for ec_val, ec_cnt in exit_codes.items()
                }
                row['exit-codes'] = ec_details

            # Failure reasons
            if entry.failures:
                summary['failed'].append(mfid)
                row['failures'] = entry.failures

            # Explain why filtered rows were skipped
            if entry.filtered:
                summary['skipped'].append(mfid)
                row['skipped-because'] = entry.filtered

        self.failed = len(summary['failed'])
        self.skipped = len(summary['skipped'])

        # Unassociated files
        for fpath, _ in app.sourcedir.files(associated=False):
            summary['unassociated-files'].append(fpath)
        self.unassociated = len(summary['unassociated-files'])

        # Manifest row overview
        succeeded = len([ent for ent in app.manifest if not ent.skipped and not ent.failures])
        summary['row-overview'] = {
            'succeeded': succeeded,
            'failed': self.failed,
            'skipped': self.skipped
        }
        if ignored:
            summary['row-overview']['ignored'] = ignored

        # Write summary file
        summary_path = os.path.join(app.workdir, filename)
        with open(summary_path, 'w', encoding='utf8') as summary_file:
            json.dump(summary, summary_file, indent=2)
            summary_file.write('\n')

    def exit_code(self, strict: bool=False):
        """
        Return the appropriate exit code given the report generated
        args:
            strict: Whether strict mode is enabled
        returns:
            0 on success
            2 on upon failure (taking into account strict flag)
        raises:
            ColophonException if generate() hasn't been called prior to exit_code()
        """
        ecode = 0
        if self.failed is None:
            raise app.ColophonException(
                "Could not determine exit code: Must call generate() before exit_code()"
            )
        if (
            self.failed or
            (strict and (self.skipped or self.unassociated))
        ):
            ecode = 2
        return ecode

class OverviewPage:
    """Overview of all reports, data, and files"""
    @staticmethod
    def generate(
        savedir: str=None,
        filename: str="overview.html",
        template: str="overview.html.j2"
    ):
        """Create overview and save in workdir"""
        savedir = savedir if savedir else app.workdir
        filename = filename if filename else app.workdir
        template = template if template else app.workdir

        with open(os.path.join(app.workdir, 'summary.json'), 'r', encoding='utf8') as sfh:
            sumdat = json.load(sfh)

        with open(os.path.join(app.workdir, 'results.json'), 'r', encoding='utf8') as rfh:
            resdat = json.load(rfh)

        with open(os.path.join(app.workdir, 'colophon.log'), 'r', encoding='utf8') as lfh:
            logdat = lfh.readlines()

        fildat = []
        for root, dirs, files in os.walk(app.workdir):
            if root == app.workdir:
                continue
            for file in files:
                fildat.append(os.path.join(root, file).removeprefix(f"{app.workdir}/"))
        fildat.sort()

        # Read in external files for embedding
        js_data, css_data = [], []
        with (
            open(
                os.path.join(app.install_path, 'ext/highlightjs/highlight.min.js'),
                'r', encoding='utf8') as hljs_js,
            open(
                os.path.join(app.install_path, 'ext/highlightjs/default.min.css'),
                'r', encoding='utf8') as hljs_css
        ):
            js_data.append(hljs_js.read())
            css_data.append(hljs_css.read())

        # Create context
        context = {
            "app": app,
            "now": datetime.now().replace(microsecond=0).isoformat(),
            "summary": json.dumps(sumdat, indent=2),
            "results": json.dumps(resdat, indent=2),
            "manifest": app.manifest,
            "files": fildat,
            "logs": logdat,
            "js_data": js_data,
            "css_data": css_data,
        }

        # Render template to output file
        overview_path = os.path.join(app.workdir, filename)
        template_path = os.path.join(app.install_path, 'templates', template)
        with (
            open(overview_path, 'w', encoding='utf8') as overview_file,
            open(template_path, 'r', encoding='utf8') as template_file
        ):
            overview_file.write(render_template_string(template_file.read(), context))
