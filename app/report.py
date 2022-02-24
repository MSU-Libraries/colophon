"""
Colophon reports and other output files
"""
import os
import csv
import json
import app

class UnassociatedReport:
    @staticmethod
    def generate(savedir: str=None, filename: str="unassociated.json"):
        unassociated = []
        for fpath, _ in app.sourcedir.files(associated=False):
            unassociated.append(fpath)
        unassociated_path = os.path.join(app.workdir, filename)
        with open(unassociated_path, 'w') as unassociated_file:
            json.dump(unassociated, unassociated_file, indent=2)
            unassociated_file.write('\n')

class ManifestReport:
    @staticmethod
    def generate(savedir: str=None, filename: str="manifest.csv"):
        savedir = savedir if savedir else app.workdir
        mfrows = [app.manifest[0].headers() if len(app.manifest) else app.manifest.headers]
        for entry in app.manifest:
            mfrows.append(entry.values())
        mfcsv_path = os.path.join(app.workdir, filename)
        with open(mfcsv_path, 'w', newline='') as mfcsv_file:
            mfcsv = csv.writer(mfcsv_file, quoting=csv.QUOTE_ALL)
            mfcsv.writerows(mfrows)

class SummaryReport:
    @staticmethod
    def generate(savedir: str=None, filename: str="summary.json"):
        savedir = savedir if savedir else app.workdir
        summary = {}
        #TODO - success, failure, skipped
        #TODO - count number of stages run on success
        #TODO - enumerate failures on failure
        #TODO - explain why skipped on skipped
        summary_path = os.path.join(app.workdir, filename)
        with open(summary_path, 'w') as summary_file:
            json.dump(summary, summary_file, indent=2)
            summary_file.write('\n')
