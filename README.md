# Colophon: Media Validation Toon

TODO what is this?


## Running Colophon
TODO

### What is Needed to Run
Before you can run Colophon, you will need the following:

* A folder with data to be checked (the "data files")
* A CSV listing of files to verify (the "manifest")
* A configuration file of what tests to run (the "check config")

TODO:
* manifest contain expected files? flag to indicate file may exists or may not?
* manifest contain expected file formats with expected attributes (resolution, bitrate, etc)

### How Colophon Runs
Colophon will use a directory for maintaining the state and results
of its work progress. Unless you specifiy a directory, it will create
a temporary one to work within. The results will remain in the directory
until deleted, which for an automatically generated temp directory is up
to the operating system.

For each manifest entry, Colophon will maintain a state of the tests run
their output. Each script may create JSON data to be saved as well, for use
in subsequent scripts. This extra data is called the "JSON results".

### Generating a Manifest
TODO `generate-manifest-from-spreadsheet`  

## Check Scripts
Colophon works by running a set of check scripts against your file list.

A check script is a script that can be written in any lanugage or shell which
abides by a set of rules.

### Input
As input, each script can expect the following:
* A media file path
* A JSON results file path, which includes row data from the manifest

### Output
Output from a check script may write anything to stdout, be it output from commands
it is calling, debug messages, or informational messages.

A check script should write any failure or warning information to stderr instead
of stdout. This will be logged separately in order to help assist with reviewing
and media issues found.

### File Modification
A script must never modify a data file(s) that is being verified.

A script may add new data to the JSON results for a file, but should not
modify any data that was already in the JSON results.

### Exit Codes
Colophon check scripts must have a standard exit code which indicates the result
of the script. A code of `0` means the check was successful. Any other value means
something occurred which might require attention; this includes failing the
check entirely, but may also be something like a warning notice. In call cases
where a non-`0` exit code was generated, you can refer to the script output
for details.

**Exit Codes**
* `0` indicates that the script ran successfully and no issues were found.
* `1` indicates that the check failed for some reason.
* `2` indicates that the script ran, but warning messages were generated.
* `3` indicates that the file(s) to check were missing or unreadable.
* `4` indicates that the parameters passed to the script were incomplete or invalid.

When creating a check script at its simplest form, a script that returns
either `0` or `1` will suffice.

