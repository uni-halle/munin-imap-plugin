#!/bin/bash
# This script expects the following environment variables to be set:
#
#     - TEST_MAIL_INTERNAL_IMAP_HOST
#     - TEST_MAIL_INTERNAL_USERNAME
#     - TEST_MAIL_INTERNAL_PASSWORD
#
# Usage
#
#    ./run_imap4.check.bash config
#
#    ./run_imap4.check.bash
#
# VERBOSITY = 0 or 1
_V=0

function log () {
    if [[ $_V -eq 1 ]]; then
        echo "$@"
    fi
}

dir=$( dirname "$(readlink -f $0)" )

log "DEBUG: argument 0 = $0"
log "DEBUG: argument 1 = $1"

log "DEBUG: script source = $dir"
log "DEBUG: username = $TEST_MAIL_INTERNAL_USERNAME"
log "DEBUG: hostname = $TEST_MAIL_INTERNAL_IMAP_HOST"

if [[ "$1" = "config" ]]; then
    python $dir/check_imap4.py config
else
    python $dir/check_imap4.py -u "$TEST_MAIL_INTERNAL_USERNAME" -p "$TEST_MAIL_INTERNAL_PASSWORD" -H "$TEST_MAIL_INTERNAL_IMAP_HOST" -s
fi
