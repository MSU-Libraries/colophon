# Colophon: File Quality Control Validator

Colophon is a tool to ...

## Table of Contents
* [Installing](#installing)
* [What is Needed to Run](#what-is-needed-to-run)
* [How Colophon Works](#how-colophon-works)
* [Running Colophon](#running-colophon)
* [Flags and Arguments](#flags-and-arguments)
  - [Colophon Exit Codes](#colophon-exit-codes)
  - [Colophon Output](#colophon-output)
* [The Manifest File](#the-manifest-file)
  - [Generating a Manifest](#generating-a-manifest)
* [The Suite File](#the-suite-file)
  - [Template Strings](#template-strings)
* [Check Scripts](#check-scripts)
  - [Relative Paths](#relative-paths)
  - [Input](#input)
  - [File Modification](#file-modification)
  - [Output](#output)
  - [Exit Codes](#exit-codes)
  - [Results JSON File as Input Argument](#results-json-file-as-input-argument)

## Installing
TODO dependencies
TODO

## What is Needed to Run
Before you can run Colophon, you will need the following:

* A folder with data to be checked (the files **source directory**)
* A CSV listing records that need to be verified (the **manifest**)
* A configuration file of what tests to run (the **suite** of tests)

## How Colophon Works
Colophon starts with the manifest file. This is an arbitrary CSV file
with a header row to give column labels.

Colophon will iterate over the rows in the manifest, comparing it to
the suite and source directory. If manifest row matches the given
suite files, Colophon will attempt to find matching files from the
source directory based of definitions within the suite file.

With files in hand, Colophon then runs stages of user-defined scripts
(also defined in the suite file). If those scripts succeed, then we
move onto the next stage. Once all stages are completed for a manifest
row, the process repeats for the next row until all rows are completed.

Finally, all results, reports, and script output are bundled together
and returned as a zip file.

Much of process is user defined, which makes Colophon very flexible
and configurable. It does mean you will need to invest some time into
creating a the suite file before running your verifications.

## Running Colophon
Assuming you have the three required components ready (source directory,
manifest file, suite file), then running `colophon` is quite simple.
```
./colophon -m example_manifest.csv -s suites/verify-video.yml -d example_files/ -v
```
Where:
* `example_manifest.csv` is the CSV file containing the manifest
* `suites/verify-video.yml` is a YAML file defining the suite to run against the manifest
* `example_files/` is a directory where files associated with the manifest are located

### Flags and Arguments
A full list of command options is also avilable by using the `-h` or `--help` flag.

* `-m, --manifest MNFST`    The file manifest as csv file; first row defines labels for each column  [required]
* `-s, --suite SUITE`       The suite file defining files to match and what stages to run  [required]
* `-d, --dir DIR`           The source directory in which to find files defined by the suite and manifest  [required]
* `-w, --workdir WORKDIR`   A directory where to store temp files and results
* `-r, --retry FAILED`      Re-run failed tests specified in provided JSON file from previous run
* `-t, --strict`            Exit code 0 only with no manifest entries skipped and no unassociated files
* `-v, --verbose`           Provide details output while running
* `-q, --quiet`             Suppress output while running

### Colophon Exit Codes
The primary `colophon` script has three possible exit codes.
* `0` There were no failures when running stages on manifest entries.
* `1` An error occured. See output/logs for detals.
* `2` While running stages, one or more failures occurred.
* `2` (Strict mode) A manifest entry was skipped or there were unassociated files.

### Colophon Output
If `colophon` exits without an error (exit code `0` or `2`), the only output to
**stdout** will be the full path of of the results zip file. Any other output during
a normal run will be to **stderr**.

Should `colophon` exit with an error, no results zip file will be generated. All
error messages will be send to **stderr**.

## The Manifest File
TODO

### Generating a Manifest
TODO `generate-manifest-from-spreadsheet`  

## The Suite File
TODO

### Template Strings
Colophon makes use of [Jinja2](https://jinja2docs.readthedocs.io/) template rendering
when parsing values from suite files (except for `regex` expressons).

Depending on the context, different variables may be available within
the template render context.

`manifest`
The following variables are available:
 - All fields defined as headers in the manifest

For example, if the manifest had a column header called `basename`, then you would
be able to reference `{{ basename }}` within a string to insert the row value for
that column.

`manifest.files`
The following variables are available in addition to normal `manifest` fields.:
 - `file.name`: The full name of the file (no path)
 - `file.path`: The full path of the file
 - `file.base`: The name of the file without its extension
 - `file.ext`: The file extension (no leading period)
 - `file.size`: The size of the file in bytes

`stages`
The following variables are available:
 - All fields that are available from the `manifest` context.
 - All labels defined in `manifest.files` are now field names and can be referenced.

_Note_: Jinja variables within the `stages` section of the manifest will be automatically
quoted for use as arguments within a shell environment.

## Check Scripts
Colophon works by running a set of check scripts in stages against your manifest.

A check script can be written in any lanugage or shell which abides by a set of rules.

### Relative Paths
Check scripts should accept relative paths as input arguments and should _NOT_
attempt to convert them into absolute paths at any point. If relative paths were
passed in, then relative paths should be used for any logs or output.

### Input
It is recommended that a check script can accept a JSON file as an input argument.
This would be the `results.json` and the script should write the result of its
check to this file in a manner that _does not overwrite any other data in the file_
(additions only).

The choice for how you accept input arguments for the script is up to you, but
it is recommended to follow the same style as existing scripts. Have a look at
the `scripts/` directory for examples.

### File Modification
1. A script must **never** modify any data or file from the source directory.
2. A script must **never** create any files/folders inside the source directory.

### Output
Output from a check script may write anything to stdout or stderr, be it output
from commands it is calling, debug messages, or informational messages.

A check script _should_ write failures or warning information to stderr instead
of stdout. This will be logged separately in order to help assist with reviewing
and media issues found.

A check script _may_ write structured output data into
the [Results-JSON](#results-json-file-as-input-argument) file.

### Exit Codes
Check scripts **must** have a standard exit code which indicates the result
of the script. A code of `0` means the check was successful. Any other value means
something occurred which might require attention; this includes failing the
check entirely, but may also be something like a warning notice. In call cases
where a non-`0` exit code was generated, you can refer to the script output
for details.

**Exit Codes**
* `0`  indicates that the script ran successfully and no issues were found.
* `1`  indicates that the check failed for some reason. See output/logs.
* `3`  indicates that the file(s) used as part of the check were missing or unreadable.
* `5`  indicates that the parameters passed to the script were incomplete or invalid.
* `9`  indicates that the script ran, but warning messages were generated.
* `16` indicates that the check did NOT fail, but the manifest row should be marked as ignored.

When creating a check script at its simplest form, a script that returns
either `0` or `1` will suffice.

### Results JSON File as Input Argument
It is recommended that scripts accept a JSON file as an argument. The scripts
may then output structured results by updating the JSON file.

In dealing with the results JSON files, the script should:
* Never overwrite other data already in the JSON file.
* Attempt to write data in a way where collisions would never occur; e.g. appending to a list.
* Separate results generated using the check script from other results in the file.
* Preferably, output should be written under a key that matches the script's filename.

Writing to the results file in the following manner **is recommended**:
```
{
  "my-check-script": [
    {
      "file": "/path/to/fileA.txt",
      "outcome": "acceptable"
    },
    {
      "file": "/path/to/fileB.txt",
      "outcome": "unacceptable"
    }
  ]
}
```
However, writing to the results file in this next manner **is discouraged**:
```
{
  "/path/to/fileA.txt": [
    {
      "script": "my-check-script",
      "outcome": "acceptable"
    }
  ],
  "/path/to/fileB.txt": [
    {
      "script": "my-check-script",
      "outcome": "unacceptable"
    }
  ]
}
```

This second **bad example** of output fails to separate the script output from
other types of output. If two scripts did the same practice, then both
differing output types would be mixed in the same list format! This would be
very annoying to try to parse.
