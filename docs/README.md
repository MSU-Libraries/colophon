# Colophon: File Quality Control Validator

Colophon is a tool to take a media object manifest, find related
files using a flexible matching system, and then run any
number of scripts to validate the files founds. The output is
then bundled into a zip file, including HTML report summary,
JSON data details, and full output of all scripts run.

**Table of Contents**  

* [Installing](#installing)
* [How Colophon Works](#how-colophon-works)
* [Running Colophon](#running-colophon)
* [The Manifest File](#the-manifest-file)
* [The Suite File](#the-suite-file)
* [Check Scripts](#check-scripts)
* [Copyright and License](#author-and-copyright)

## Installing
Colophon is written primarily in Python, but makes use of scripts
to run validation tests. These scripts can be written in any language,
and you can add your own quite easily!

Create your virutal environment
```sh
# Using virtualenv here, but you can use whatever you want
virtualenv -p python3 env
```

Install Python dependences
```sh
# Activate your virtual environment
. env/bin/activate
# Install dependencies defined in the requirements.txt file
pip3 install -r requirements.txt
```

Running colophon
```sh
# If you've activated your environment
./colophon -h
# Or call via env directly
./env/bin/python3 colophon -h
```

### Script Dependencies
Depending on which scripts you use, some of all of the following
dependendies will be needed. Here are the commands to install
them on Ubuntu, but you should be able to easily find these
packages on most Linux distributions.

Install dependencies on Ubuntu (`bash` already present)
```sh
apt install -y jq imagemagick mediainfo
```

## What is Needed to Run
Before you can run Colophon, you will need the following:

* A folder with data to be checked (the files **source directory**)
* A CSV listing records that need to be verified (the **manifest**)
* A configuration file of what tests to run (the **suite** of tests)

### Other Terms to Know

* __Error__: A script was unable to complete. This is likely due to due incorrect input or missing dependencies.
* __Failure__: A script ran to completion, but the validation did not succeed on the given file using the given parameters.

## How Colophon Works
Colophon starts with the manifest file. This is an arbitrary CSV file
with a header row to give column labels.

```csv
"mediatype","basename", "title"
"Video",    "UP-F00001","UPP302 - Press presentation 02/10/2004"
"Video",    "UP-F00002","UPP710 - President's speech 12/20/2007"
"Book",     "UP-F00003","UPP098 - College pamphlet 1921"
```

When running Colphon, you will also specify a directory where files
related to the manifest should be found.

```
batch_01/upp302/UP-F00001.mkv
batch_01/upp302/UP-F00001.mkv.md5
batch_01/upp302/UP-F00001.mp4
batch_01/upp302/UP-F00001.mp4.md5
batch_01/upp302/UP-F00001_asset_cover.tif
batch_01/upp302/UP-F00001_asset_back.tif
batch_01/upp710/UP-F00002.mkv
batch_01/upp302/UP-F00002.mkv.md5
batch_01/upp710/UP-F00002.mp4
batch_01/upp302/UP-F00002_digitization_notes.txt
batch_01/upp098/UP-F00003.pdf
batch_01/upp098/UP-F00003_front.tif
batch_01/upp098/UP-F00003_back.tif
batch_01/upp098/UP-F00003_front.jpg
batch_01/upp098/UP-F00003_back.jpg
```

And finally, a test suite file while specifies what Colophon should
do.

Example of the first part of a test suite file. The `manifest:` section:
```yaml
manifest:
  id: "{{ basename }}"  # id should be unique data; it's used in logs and output
  filter:               # only use manifest rows that match these filters
    - value: mediatype
      equals: Video
  files:                # find files matching the manifest row
    - label: preserve_copy
      startswith: "{{ basename }}"
      endswith: '.mkv'
    - label: access_copy
      startswith: "{{ basename }}"
      endswith: '.mp4'
    - label: preserve_hash
      startswith: "{{ basename }}"
      endswith: '.mkv.md5'
    - label: access_hash
      startswith: "{{ basename }}"
      endswith: '.mp4.md5'
    - label: asset_file
      multiple: true
      optional: true
      startswith: "{{ basename }}"
      regex: '_asset.*\.tif$'
```

Colophon will iterate over the rows in the manifest, comparing it to
the suite and source directory. If manifest row matches the given
suite files, Colophon will attempt to find matching _files_ from the
source directory based of definitions within the suite file.

Example of the second part of a test suite file. The `stages:` section:
```yaml
stages:                 # run a set of stages (scripts) for each manifest row
  access.hash:          # each stage name is just a label for identifing the stage
    script: "scripts/verify-hash -c {{ access_copy }} -f {{ access_hash }} -v -J {{ results_path }}"
  preserve.hash:
    script: "scripts/verify-hash -c {{ preserve_copy }} -f {{ preserve_hash }} -v -J {{ results_path }}"
  access.audio:
    script: "scripts/validate-audio -c {{ access_copy }} -s 48000 -m CBR -v -J {{ results_path }}"
  preserve.audio:
    script: "scripts/validate-audio -c {{ prezerve_copy }} -s 48000 -m CBR -b 24 -v -J {{ results_path }}"
  access.video:
    script: "scripts/validate-video -c {{ access_copy }} -d 640x480 -b 8 -v -J {{ results_path }}"
  preserve.video:
    script: "scripts/validate-video -c {{ preserve_copy }} -d 720x486 -b 10 -v -J {{ results_path }}"
```

With files in hand, Colophon then runs stages of user-defined scripts
(also defined in the suite file). If those scripts succeed, then we
move onto the next stage. Once all stages are completed for a manifest
row, the process repeats for the next row until all rows are completed.

Finally, all results, reports, and script output are bundled together
and returned as a zip file.

Example section of the `summary.json` file, which is included in the output:
```json
{
  "row-overview": {
    "succeeded": 1,
    "failed": 1,
    "skipped": 1
  },
  "skipped": ["UP-F00003"],
  "failed": ["UP-F00002"],
  "unassociated-files": [
    "batch_01/upp302/UP-F00002_digitization_notes.txt"
  ],
  "rows": {
    "UP-F00001": {
      "exit-codes": {
        "0": {
          "occurrences": 6,
          "code-meaning": "success"
        }
      }
    },
    "UP-F00002": {
      "failures": [
        "Manifest(id=UP-F00002) was required to match a file for label 'access_hash', but no matching file was found."
      ]
    },
    "UP-F00003": {
      "skipped-because": "Filter did not match: {'value': 'mediatype', 'equals': 'video'}"
    }
  }
}
```

Much of Colophon process is user defined, which makes it very flexible
and configurable. It does mean you will need to invest some time into
creating a the suite file before running your verifications.

## Running Colophon
Assuming you have the three required components ready (source directory,
manifest file, suite file), then running `colophon` is quite simple.
```sh
./colophon -m example_manifest.csv -s suites/verify-video.yml -d example_files/ -v
```

Where the arguments are:

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
* `-i, --ignore-missing`    Ignore manifest entries that have no files matched
* `-t, --strict`            Exit code 0 only with no manifest entries skipped and no unassociated files
* `-v, --verbose`           Provide details output while running (verbose logs will always be inlcuded in output bundle)
* `-q, --quiet`             Suppress output while running

### Colophon Exit Codes
The primary `colophon` script has three possible exit codes.

* `0` There were no failures when running stages on manifest entries.
* `1` An error occured. See output/logs for detals.
* `2` While running stages, one or more failures occurred.
* `2` (When using strict mode) A manifest entry was skipped or there were unassociated files.

### Colophon Output
If `colophon` exits without an error (exit code `0` or `2`), the only output to
**stdout** will be the full path of of the results zip file. Any other output during
a normal run will be to **stderr**.

Should `colophon` exit with an error, no results zip file will be generated. All
error messages will be send to **stderr**. You can also inspect files in the
**workdir** for additional information. The workdir is where files are placed before
getting added to the zip archive. The workdir is either manually specified with
the `--workdir` flag or created automatically in a temp directory (e.g. in `/tmp/`).

Details on what is contained within an output file are listed below.

__`summary.json`__  
A JSON file containing all manifest objects, including number of
successful stages for each, failures and a short description for the failure reason,
and explainations of why an manifest row was skipped. Additionally, if any files
from the source directory did not matched any rows, they are listed as
`unassociated-files` in the summary.

__`results.json`__  
A JSON files where scripts invoked by the stages can store additional
output.

__`manifest.csv`__  
The processed manifest file, including any additional columns created
from suite file matches.

__`colophon.log`__  
The verbose logs from the main `colophon` program.

__`{ID}/{STAGE}/stdout.txt`__  
For each stage/manifest row, the a file recording the
stdout generated by script script.

__`{ID}/{STAGE}/stderr.txt`__  
For each stage/manifest row, the a file recording the
stderr generated by script script.

__`{ID}/{STAGE}/ecode.{EXITCODE}`__  
For each stage/manifest row, the a file identifying
the exit code from the script run. Human readable tags
describing the exit code are within the file.

## The Manifest File
The manifest is a CSV file with fields relevant to performing the quality control
checks desired. The can include:

* Sufficient naming to identify files
* Some identifying data, in the case where the name info doesn't do this
* The type of object or media, if multiple types are present
* Additional fields specifying validation parameters where they could vary from record to record
  * E.g. Video resolution, color bit depth, compression type

An example manifest could look like this:
```csv
"mediatype","basename","name", "resolution", "DPI"
"audio","MSUF000000","Adams interview", "", ""
"Video","MSUF000001","Billing's debate", "720x480", ""
"book","MSUF000002","Chloe's Biography", "", "400"
"Audio","MSUF000003","Declan's speech", "", ""
"Video","MSUF000005","Eric's review", "640x480", ""
"Book","MSUF000006","Ferrell's history ", "", "300"
```

If an attribute of a file is going to be consistent across all items
being verified, they do _not_ need to be in the manifest. We can
put those values into the testing suite directly. 

### Generating a Manifest
If you have a spreadsheet, such as a `.xlsx` or `.ods` with the needed fields,
Colophon comes with a helper script to convert it to `.csv`. It may
be easier to create a new `.csv` using your preferred spreadsheet program, this
script may help if you are trying to create a programmatic solutions.

It takes a mapping of old column IDs (e.g. `a`, `b`, etc) to new column names,
as well as number of header rows to ignore.

Example manifest map `.yml` file:
```yaml
---
skiprows: 1
columns:
  - column: b
    label: mediatype
  - column: c
    label: basename
  - column: f
    label: name
  - column: j
    label: resolution
  - column: n
    label: dpi
```

Generating the manifest:
```sh
./helpers/generate-manifest-from-spreadsheet -s my-speadsheet.xlsx -m my-mapfile.yml -o my-new-manifest.csv
```

## The Suite File
The suite file is written in Yaml and defines everything Colophon does when you run it.
Example suite files are provided in the `suites/` directory with Colophon. You will
need to heavily modify these to suite your own media if you decide to start with one of these.

Basic structure of a suite files is as follows:
```yaml
---
# The manifest: section defines how Colophon will read/update the manifest.
# It operates on a row-by-row basis within the manifest. E.g. each row in the
# manifest will be checked against the filter: and each row will search to
# find matching files: from the source directory.
manifest:
  # The id: allows you to define how a manifest row is referred to by Colophon
  # A string value that should be unique (otherwise it would serve as a poor identifier!)
  id:       # (string)
  # The filter: allows you to selectively iterate over only manifest rows which
  # match all the filters you define here.
  filter:   # (list)
  # The files: has you define rules for finding each of the files from the source
  # directory which will be associated with the manifest row. Each file has
  # a label you define and that label will be added to the manifest with the
  # associated value being the matched file(s).
  files:    # (list)

# The stages: section defines a set of independent stages, each with a command
# that will be run using the manifest row data. This happens only AFTER the
# above manifest: section has completed filtering and finding files.
stages:     # (associative array)
```

A full definition of manifest fields, templating values into them, and their
sub-fields are covered in the next documentation sections.

### Template Strings
Colophon makes use of [Jinja2](https://jinja2docs.readthedocs.io/) template rendering
when parsing values from suite files (except for `regex` expressons).

Any fields within the manifest can be referenced inside the suite by means of Jinja expressions,
such as `{{ field_name }}`. Depending on the context, additional variables may be available within
the template render context.

For example, if the manifest had a column header called `objectname`, then you would
be able to reference `{{ objectname }}` within a string to insert the row value for
that column.

In addition to [built-in Jina2 filters](https://jinja.palletsprojects.com/en/3.0.x/templates/#builtin-filters),
Colophon provides the additional filters:

* `basename` Runs Python's `os.path.basename()` on the value.
* `esh` Escapes the value for use as a shell command argument. This is applied automatically within `stages:` section of suites.

__`manifest.files:`__  
Within the `files:` section, the following variables are available in addition to
the normal `manifest` fields:

- `file.name`: The full name of the file (no path)
- `file.path`: The full path of the file
- `file.base`: The name of the file without its extension
- `file.ext`: The file extension (no leading period)
- `file.size`: The size of the file in bytes

__`stages`__  
Within the `stages:` section, any files defined within the `manifest.files:` section have
already been added to the manifest. The `label:` becomes the manifest field name, and the
matched file becomes the value (or blank if not match and the file was optional).

With stages, the variable `results_path` is also available. This is the path to the
`results.json` which will be included in the output zip bundle. This is indended to be
used with scripts' `-J` flag, which may [output JSON results](#results-json-file-as-input-argument).

_Note_: Jinja variables within the `stages` section of the manifest will be automatically
quoted for use as arguments within a shell environment.

### Manifest Field Details

#### `manifest.id:` (string)
The `id:` field in the manifest is used within logs to identify which row the log entry
is referring to. It is strongly recommended you define this to be a unique value from
within your manifest.

```yaml
manifest:
  id: "{{ mediatype }}-{{ objectid }}"
```

#### `manifest.filters:` (list)
Allows the suite to filter specific rows to process. Only rows matching all
provided filters will be used. Rows which do not match the filters will be
ignored.

Each filter is an associative array and takes a `value:`, which must be a
manifest field name. Additionally, it needs one or more types of filters.

The __filter types__ are:

* `equals:` The field in `value:` must be exactly the value of this.
* `startswith:` The field in `value:` must start with the value of this.
* `endswith:` The field in `value:` must end with the value of this.
* `regex:` The field in `value:` must match this regular expression. (Note that `regex:` values do NOT render as Jinja2 templates.)
* `ignorecase:` Boolean. If set to `true`, the other filter types within this filter are case insensitive. (Note that this _does_ affect `regex:`.)
* `greaterthan:` The field in `value:` must be numerically greater than this.
* `lessthan:` The field in `value:` must be numerically less than this.

```yaml
manifest:
  filters:
  - value: mediatype
    equals: audio
    ignorecase: true
  - value: donor
    endswith: Smith
  - value: year
    greaterthan: 1950
    lessthan: 1961
```

#### `manifest.files:` (list)
Define which files should be found for each row in the manifest. Each
item in the `files:` section _requires_ a `label:` defined. The `label:`
will be a new field within the manifest for which the value will be the
path of the matched file(s).

Each entry in `files:` also makes use of the same __filter types__
defined in the `manifest.filters:` section above.

Additionally, the following fields are available:

* `multiple:` Boolean. If set to `true`, this file entry can match any number of files.
* `optional:` Boolean. If set to `true`, this file entry is optional and will not cause a failure should no matching files be found.
* `linkedto:` Defines a linked file. Must be given `label:` to another file that has already been defined. This requires a file match for each file match the linked file entry finds, even if that linked file entry was optional.

```yaml
manifest:
  files:
  - label: metadata_file
    startswith: "{{ objectname }}"
    endswith: '_mods.xml'
  - label: pres_file
    startswith: "{{ objectname }}"
    regex: '(?:\.mov|\.mkv)$'
  - label: pres_hash
    startswith: "{{ objectname }}"
    regex: '(?:\.mov|\.mkv).md5$'
  - label: asset
    multiple: true
    optional: true
    startswith: "{{ objectname }}"
    endswith: '_asset.tif'
  - label: asset_hash
    linkedto: asset
    startswith: "{{ asset | basename }}"
    endswith: '.md5'
```

#### `stages:` (associative array)
The `stages:` section contains any number of stages which will be iterated
over in order.

#### `stages.STAGE_NAME:` (associative array)
Where `STAGE_NAME` is a unique value used to identify that stage. For example,
it could be `stage1.0`, `stage1.1`, `stage1.2`, etc. Or more descriptive like
`audio.file-metadata`,`audio.waveform`,`video-metadata`, etc.

The `STAGE_NAME` will be used within logs and in structuring the location of script
output files (e.g. `stdout.txt`).

#### `stages.STAGE_NAME.script:` (string)
Define the script command to run for the given stage. Jinja expressions used
within the command will be auto-escaped for use as arguments within a shell command.

The output of the command will always be saved in the output zip bundle within
the path `{{ manifest.id }}/{{ STAGE_NAME }}/`:

* `stdout.txt` All output to stdout while the script ran.
* `stderr.txt` All output to stderr while the script ran.
* `ecode.?` The script exit code (where `?` is in the filename). The contents of the file will also include the exit code and human readable label(s) explaining the exit code's meaning.

```yaml
stages:
  video.hash:
    script: "scripts/verify-hash -c {{ media_file }} -f {{ media_file_hash }} -v -J {{ results_path }}"
  video.size:
    script: "custom-scripts/validate-size -c {{ media_file }} --min-size {{ bytes_lower }} --max-size {{ bytes_upper }} -v"
```

## Check Scripts
Colophon works by running a set of check scripts in stages against your manifest.

Well written scripts will provide a full list of flags and their use by using the `-h` or
`--help` flag.
```sh
$ ./scripts/verify-hash -h

Usage: verify-hash [FLAGS]

  Verify a file contents matches a given hash

FLAGS:
  -c|--check-file FILE
      The file to verify
  -f|--hash-file HASH_FILE
      A file containing a hash to verify against.
  -s|--hash-str HASH_STR
      A string hash to verify against.
  -a|--algo ALGO
      The algorithm to use. E.g. md5, sha1, sha256, etc
  -J|--json JSON
      Write results to the file JSON.
  -v|--verbose
      Display verbose output.
```

### Included Check Scripts
Colophon includes a number of check-scripts, though you can always [write your own](#writing-a-check-script). Additional scripts and script features will be included with each future Colophon release.

All these are included in the `scripts/` directory. A brief summary of these scripts are included below. For the most up-to-date info on these scripts, refer to their `--help` info.

#### `verify-hash`
Verify a file contents matches a given hash, the hash being either in
a file or passed as string argument.

Example use:
```sh
# Verify MD5 hash of media-file.wav matches hash within media-file.wav.md5 (algo auto-detected)
./scripts/verify-hash -c media-file.wav -f media-file.wav.md5 -v
# Verify MD5 hash of media-file.wav matches hash within media-file.wav.md5 (hash file auto-detected)
./scripts/verify-hash -c media-file.wav -a md5 -v
# Verify MD5 hash of media-file.wav matched provided string hash
./scripts/verify-hash -c media-file.wav -s d8e8fca2dc0f896fd7cb4cb0031ba249 -v
```

#### `validate-image`
Validate the given image has the attributes provided. If multiple values for the same attribute
is given, the image may match any one of them.

Example use:
```sh
# Validate image dimension either of the provided options and that compression is disabled
./scripts/validate-image -c media-file.tif -d 4000x3000 -d 6000x3000 -x none -v
# Validate image dimension is exactly the provided one and that compression is LZW
./scripts/validate-image -c media-file.tif -d 1600x1200 -x lzw -v
```

#### `validate-audio`
Validate the given audio file, or an audio stream in a video file, has the attributes provided.
If multiple values for the same attribute is given, the media file may match any one of them.

Example use:
```sh
# Validate audio stream sampling rate (either 44100 or 48000), bitrate mode (CBR), and bit depth (24)
./scripts/validate-audio -c media-file.wav -s 48000 -s 44100 -m cbr -b 24 -v
```

#### `validate-video`
Validate the given video file has the attributes provided.
If multiple values for the same attribute is given, the media file may match any one of them.

Example use:
```sh
# Validate video stream dimensions (either 720x486 or 720x480) and color bit depth (10)
./scripts/validate-video -c media-file.mkv -d 720x486 -d 720x480 -b 10 -v
```

### Writing a Check Script

A check script can be written in any lanugage or shell which abides by a set of rules.

#### Relative Paths
Check scripts should accept relative paths as input arguments and should _NOT_
attempt to convert them into absolute paths at any point. If relative paths were
passed in, then relative paths should be used for any logs or output.

#### Input
It is recommended that a check script can accept a JSON file as an input argument.
This would be the `results.json` and the script should write the result of its
check to this file in a manner that _does not overwrite any other data in the file_
(additions only).

The choice for how you accept input arguments for the script is up to you, but
it is recommended to follow the same style as existing scripts. Have a look at
the `scripts/` directory for examples.

#### File Modification
1. A script must **never** modify any data or file from the source directory.
2. A script must **never** create any files/folders inside the source directory.

#### Output
Output from a check script may write anything to stdout or stderr, be it output
from commands it is calling, debug messages, or informational messages.

A check script _should_ write failures or warning information to stderr instead
of stdout. This will be logged separately in order to help assist with reviewing
and media issues found.

A check script _may_ write structured output data into
the [Results-JSON](#results-json-file-as-input-argument) file.

#### Exit Codes
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

Note the special value `16` allows a script to stop a row from being futher processed.
Essentially, this can be leveraged to do the same thing as a `filter:` would (ignoring
the manifest row), only from within the `stages:` section.

Exit code can be broken down into binary representation, each bit indicated
a state. Each state has a descriptive string associated with it. Numerical values
may be added up to represent the desired status.
(E.g. `25` would indicate `16` + `8` + `1`)

| Number (Bit) | Descriptive message | Meaning |
| ------------ | ------------------- | ------- |
| 128 (7)      | N/A                 | Bit reserved for future use |
| 64 (6)       | N/A                 | Bit reserved for future use |
| 32 (5)       | N/A                 | Bit reserved for future use |
| 16 (4)       | `skip_manfest_row`  | Script indicated this manifest row should be skipped in all further processing |
| 8 (3)        | `warning_logged`    | One or more warning was generated by the script |
| 4 (2)        | `bad_argument`      | One or more script arguments were incorrect or misused |
| 2 (1)        | `inaccessible_file` | One or more files were missing or inaccessible |
| 1 (0)        | `failure`           | Script encountered failure |
| 0 (if unset) | `success`           | Script ran without a failure |

#### Results JSON File as Input Argument
It is recommended that scripts accept a JSON file as an argument (using the `-J`
flag is preferred). The scripts may then output structured results by
creating/updating the JSON file.

If the given results JSON file already exist, the script should add data to it.
If the JSON file does not exist, then the script must create the file itself.

In dealing with the results JSON files, the script should:

* Never overwrite other data already in and existing JSON file.
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


## Author and Copyright
Written by Nathan Collins (npcollins/gmail/com)  

Copyright © 2021 Michigan State University Board of Trustees  

## License
Released under the MIT License
