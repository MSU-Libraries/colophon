"""
Colophon reports and other output files
"""
import os
import csv
import json
from collections import defaultdict
import app

class ManifestReport:
    """Report for files left unassociated"""
    def generate(self, savedir: str=None, filename: str="manifest.csv"):
        """Create report and save in workdir"""
        savedir = savedir if savedir else app.workdir
        mfrows = [app.manifest[0].headers() if len(app.manifest) else app.manifest.headers]
        for entry in app.manifest:
            mfrows.append(entry.values())
        mfcsv_path = os.path.join(app.workdir, filename)
        with open(mfcsv_path, 'w', newline='') as mfcsv_file:
            mfcsv = csv.writer(mfcsv_file, quoting=csv.QUOTE_ALL)
            mfcsv.writerows(mfrows)

def rcode_counts(search_dir: str):
    """
    Given a directory, find all files in the form "rcode.N"
    where N is a return code. Return a dict of key N to the
    count of matching files grouped by N.
    """
    rcodes = defaultdict(int)
    for root, dirs, files in os.walk(search_dir):
        for fname in files:
            if fname.startswith("rcode."):
                rcodes[fname.removeprefix("rcode.")] += 1
    return dict(rcodes)

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

        for entry in app.manifest:
            mfid = app.suite.manifest_id(entry)

            # Exit-code summary per row
            summary['rows'][mfid] = (row := {})
            row['exit-codes'] = rcode_counts(os.path.join(app.workdir, mfid))

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
        succeeded = len([ent for ent in app.manifest if not ent.filtered and not ent.failures])
        summary['row-overview'] = {
            'succeeded': succeeded,
            'failed': self.failed,
            'skipped': self.skipped
        }

        # Write summary file
        summary_path = os.path.join(app.workdir, filename)
        with open(summary_path, 'w') as summary_file:
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
        rcode = 0
        if self.failed is None:
            raise app.ColophonException("Could not determine exit code: Must call generate() before exit_code()")
        if (
            self.failed or
            (strict and (self.skipped or self.unassociated))
        ):
            rcode = 2
        return rcode
