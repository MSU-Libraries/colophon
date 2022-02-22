# Colophon: File Quality Control Validator

TODO what is colophon?

## Installing
TODO

## What is Needed to Run
Before you can run Colophon, you will need the following:

* A folder with data to be checked (the files **source directory**)
* A CSV listing records that need to be verified (the **manifest**)
* A configuration file of what tests to run (the **suite** of tests)

## How Colophon Runs
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
```

### Colophon Exit Codes
The primary `colophon` script has three possible exit codes.
* `0` There were no failures when running stages on manifest entries.
* `1` An error occured while running. See output/logs for detals.
* `2` While running stages, failures occurred.
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

### Template String
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

## Check Scripts
Colophon works by running a set of check scripts in stages against your manifest.

A check script can be written in any lanugage or shell which abides by a set of rules.

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

#### Results JSON File
It is recommended that scripts accept a JSON file as an argument. The scripts
may then output results into the JSON file.

In dealing with the results JSON files, the script should:
* Never overwrite other data already in the JSON file.
* Attempt to write data in a way where collisions would never occur; e.g. appending to a list.
* Separate results generated using the check script from other results in the file.
* Preferably, output should be written under a key that matches the script's filename.

Writing to the results file in the following manner **is good**:
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
However, writing to the results file in this next manner **is bad**:
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
This second output fails to separate the script output from other types
of output. If two scripts did the same practice, then both differing
output types would be mixed in the same list format! This would be
very annoying to try to parse.
