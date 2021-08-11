#!/bin/bash

# Dependencies: jq, moreutils

runhelp() {
    echo ""
    echo "Usage: verify-hash.sh"
    echo ""
    echo "  Verify a file contents matches a given hash"
    echo ""
    echo "FLAGS:"
    echo "  -c|--check-file FILE"
    echo "      The file to verify"
    echo "  -f|--hash-file HASH_FILE"
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

if [[ -z "$1" || $1 == "help" ]]; then
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
    ARGS[CHECK_FILE]=
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
        -c|--check-file)
            ARGS[CHECK_FILE]="$( readlink -f $2 )"
            if [[ $? -ne 0 || ! -f "${ARGS[CHECK_FILE]}" ]]; then
                stderr "File to check does not exist: $2"
                exit 3
            fi
            shift; shift ;;
        -f|--hash-file)
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
            shift ;;
        -h|--help)
            runhelp
            exit 0
            ;;
        *)
            stderr "Error: Unknown flag: $1"
            exit 1
        esac
    done

    required_flags

    if [[ -z "${ARGS[HASH_STR]}" && -z "${ARGS[HASH_FILE]}" ]]; then
        ARGS[HASH_FILE]="${ARGS[CHECK_FILE]}.${ARGS[ALGO]}"
        if [[ -f "${ARGS[HASH_FILE]}" ]]; then
            verbose "No hash source provided. Assuming: ${ARGS[HASH_FILE]}"
        else
            stderr "No hash source provided."
            exit 4
        fi
    fi
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
    REQUIRED=( CHECK_FILE ALGO )
    for REQ in "${REQUIRED[@]}"; do
        if [[ -z "${ARGS[$REQ]}" ]]; then
            stderr "Failure: Missing required flag --${REQ,,}"
            exit 1
        fi
    done
}

first_word_lower() {
    echo "${1,,}" | head -n1 | cut -d ' ' -f1
}

main() {
    HASH_CHECKED=0
    HASH_MISMATCH=0

    HASHBIN="${ARGS[ALGO]}sum"
    if [[ -n "${ARGS[HASH_FILE]}" && -n "${ARGS[HASH_STR]}" ]]; then
        stderr "Can only verify either --hash-file or --hash-str, but not both at the same time."
        exit 4
    elif [[ -n "${ARGS[HASH_FILE]}" ]]; then
        HASH_VERIFY=$( first_word_lower $( cat "${ARGS[HASH_FILE]}" ) )
        verbose "Read hash $HASH_VERIFY from ${ARGS[HASH_FILE]}"
    elif [[ -n "${ARGS[HASH_STR]}" ]]; then
        HASH_VERIFY=$( first_word_lower "${ARGS[HASH_STR]}" )
        verbose "Read hash $HASH_VERIFY from hash string"
    fi

    HASH_CHECK=$( first_word_lower $( $HASHBIN "${ARGS[CHECK_FILE]}" ) )
    verbose "Computed hash $HASH_CHECK from ${ARGS[CHECK_FILE]} using $HASHBIN"
    if [[ $HASH_VERIFY != $HASH_CHECK ]]; then
        verbose "Hashes do NOT match."
        HASH_MISMATCH=1
    fi
    HASH_CHECKED=1

    # Update JSON if provided
    if [[ -n "${ARGS[JSON]}" ]]; then
        verbose "Updating JSON file ${ARGS[ALGO]} with hash check results."
        # jq ".\"verify-hash\" |= .+ [{stuff:1}]" my.json
        jq ".\"verify-hash\" |= .+ [{ \
                algorithm: \"${ARGS[ALGO]}\", \
                expected: \"${HASH_VERIFY}\", \
                computed: \"${HASH_CHECK}\", \
                matched: $(( 1 - $HASH_MISMATCH )) \
            }]" \
            "${ARGS[JSON]}" | sponge "${ARGS[JSON]}"
    fi

    # Exit success only if a check occured and there was no mismatch
    if [[ $HASH_CHECKED -eq 1 && $HASH_MISMATCH -eq 0 ]]; then
        verbose "Hash checked and verified as matching."
        exit 0
    fi
    verbose "Hash check failed."
    exit 1
}

# Parse and start running
default_args
parse_args "$@"
main
