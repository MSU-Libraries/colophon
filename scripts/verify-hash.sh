#!/bin/bash

runhelp() {
    echo ""
    echo "Usage: verify-hash.sh"
    echo ""
    echo "  Verify a file contents matches a given hash"
    echo ""
    echo "FLAGS:"
    echo "  -f|--file FILE"
    echo "      The file to verify"
    echo "  -h|--hash-file HASH_FILE"
    echo "      A file containing a hash to verify against."
    echo "  -s|--hash-str HASH_STR"
    echo "      A string hash to verify against."
    echo "  -a|--algo ALGO"
    echo "      The algorithm to use. E.g. md5, sha1, sha256, etc"
    echo "  -J|--json JSON"
    echo "      A JSON results file from Colophon."
    echo "  -v|--verbose"
    echo "      Display verbose output."
    echo ""
}

if [[ -z "$1" || $1 == "-h" || $1 == "--help" || $1 == "help" ]]; then
    runhelp
    exit 0
fi

###############################
## Check if array contains a given value
##  $1 -> Name of array to search
##  $2 -> Value to find
## Returns 0 if an element matches the value to find
array_contains() {
    local ARRNAME=$1[@]
    local HAYSTACK=( ${!ARRNAME} )
    local NEEDLE="$2"
    for VAL in "${HAYSTACK[@]}"; do
        if [[ $NEEDLE == $VAL ]]; then
            return 0
        fi
    done
    return 1
}

# Set defaults
default_args() {
    declare -g -A ARGS
    ARGS[FILE]=
    ARGS[HASH_FILE]=
    ARGS[HASH_STR]=
    ARGS[ALGO]=
    ARGS[JSON]=
    ARGS[VERBOSE]=0
}

# Parse command arguments
parse_args() {
    # Parse flag arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
        -f|--file)
            ARGS[FILE]="$( readlink -f $2 )"
            if [[ $? -ne 0 || ! -f "${ARGS[FILE]}" ]]; then
                stderr "File does not exist: $2"
                exit 3
            fi
            shift; shift ;;
        -h|--hash-file)
            ARGS[HASH_FILE]="$( readlink -f $2 )"
            if [[ $? -ne 0 || ! -f "${ARGS[HASH_FILE]}" ]]; then
                stderr "Hash file does not exist: $2"
                exit 4
            fi
            shift; shift ;;
        -s|--hash-str)
            ARGS[HASH_STR]="$2"
            shift; shift
            if [[ $? -ne 0 ]]; then
                stderr "No hash provided"
                exit 4
            fi
            ;;
        -a|--algo)
            ARGS[ALGO]="$2"
            ALLOWED_ALGOS=( md5 sha1 sha224 sha256 sha384 sha512 )
            if ! array_contains ALLOWED_ALGOS "${ARGS[ALGO]}"; then
                stderr "Unsupported hash algorithm: $2. Supported: ${ALLOWED_ALGOS[*]}"
                exit 4
            fi
            shift; shift ;;
        -J|--json)
            ARGS[JSON]="$( readlink -f $2 )"
            if [[ $? -ne 0 || ! -f "${ARGS[JSON]}" ]]; then
                stderr "Results JSON file does not exist: $2"
                exit 4
            fi
            shift; shift ;;
        -v|--verbose)
            ARGS[VERBOSE]=1
            shift;;
        *)
            stderr "ERROR: Unknown flag: $1"
            exit 1
        esac
    done
}

verbose() {
    MSG="$1"
    if [[ "${ARGS[VERBOSE]}" -eq 1 ]]; then
        echo "${MSG}"
    fi
}

stderr() {
    1>&2 echo "$1"
}

required_flags() {
    REQUIRED=( FILE )
    for REQ in "${REQUIRED[@]}"; do
        if [[ -z "${ARGS[$REQ]}" ]]; then
            stderr "FAILURE: Missing required flag --${REQ,,}"
            exit 1
        fi
    done
}

main() {
    echo "TODO"
}

# Parse and start running
default_args
parse_args "$@"
required_flags
main

