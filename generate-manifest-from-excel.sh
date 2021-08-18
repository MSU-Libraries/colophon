#!/bin/bash

###########################
##
## This file was for experimenting if Bash was a usable base for processing
## JSON and CSV files. While possible, it was quite messy. Switched to
## Python instead. Keeping this file around for a bit just for reference.
##
###########################
exit 1

# Dependencies: jq, libreoffice-common

stderr() {
    1>&2 echo "$1"
}

declare -g -A ARGS
ARGS[MAPPING]=manifest_mapping.json
ARGS[SPREADSHEET]=MetadataWorksheet_UAPilot.xlsx

TEMPDIR=$( mktemp -d )

SSEXT="${ARGS[SPREADSHEET]: -4}"
if [[ "${SSEXT,,}" != ".csv" ]]; then
    libreoffice --headless --convert-to csv "${ARGS[SPREADSHEET]}" --outdir "$TEMPDIR"
    if [[ $? -ne 0 ]]; then
        stderr "Unable to convert file '${ARGS[SPREADSHEET]}' to a CSV file. Verify valid spreadsheet file and that libreoffice-common is installed."
        exit 1
    fi
    ARGS[SPREADSHEET]="$( ls ${TEMPDIR}/*.csv )"
fi

# Convert letter to number
letter_to_number() {
    echo "$1" | awk '@load "ordchr"; { print ord($1) - 96 }'
}

###
# Convert a JSON string into a global bash associative array
# Params:
#   $1 => The name of the bash array to create
#   $2 => A string containing the JSON
# Example:
#   json_to_aa MYARR '{ "key1": "val1", "key2": "val2" }'
json_to_aa() {
    declare -g -A $1
    while IFS="=" read -r KEY VAL; do
        read $1[$KEY] <<< "$VAL"
    done < <( jq -r 'to_entries|map("\(.key)=\(.value)")|.[]' <<< "$2" )
}

declare -a COLUMNS
while read -r ROW; do
    json_to_aa MAPPING "$ROW"
    COL_NAME=
    COL_NUM=
    for M in "${!MAPPING[@]}"; do
        if [[ $M == "manifest" ]]; then
            COL_NAME=${MAPPING[$M]}
        fi
        if [[ $M == "column" ]]; then
            COL_NUM=$( letter_to_number ${MAPPING[$M]} )
        fi
    done
    COLUMNS+=( "$COL_HEAD $COL_NAME" )
done < <( jq -rc .columns[] ${ARGS[MAPPING]} )

STARTROW=$( jq .startrow ${ARGS[MAPPING]} )


# Clean up temp space
rm -r "$TEMPDIR"

# TODO take as flag a list of desired formats and attributes
#[{
#    "_comment": "Matching mezzanine mov files (but excluding _pres.mov)",
#    "manifest_match": [
#        {
#            "field": "mediatype",
#            "regex": "Video"
#        }
#    ],
#    "files_match": [
#        "(?<!_pres).mov$"
#    ],
#    "present": "must",      # must, may (exist), warn (if exists), never (should exist)
#    "cmds": [{
#        "cmd": "file {}",
#        # 'each' ignores first and last line if they are specified
#        "line_each_contains": [
#            "Apple QuickTime movie",
#            "Apple QuickTime (.MOV/QT)"
#        ],
#        "output_contains": [
#        ],
#        "output_regex": [
#        ]
#    },
#    {
#        "cmd": "identify {}",
#        "line_first_regex": [
#        ],
#        "line_last_regex": [
#        ],
#        # 'each' ignores first and last line if they are specified
#        "line_each_regex": [
#            "MOV 720x480 720x480+0+0 8-bit TrueColor sRGB"
#        ]
#    }]
#}]
