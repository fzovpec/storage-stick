#!/bin/bash

# This script is adapted from the Zoned Storage Documentation at 

if [ $# != 2 ]; then
    echo "Usage: $0 <process id (pid)> <log file path>"
    exit 1
fi

function collect_page_fault_count()
{
    local pid=$1
    local log_fpath=$2

    pidstat -r -p $pid 1 > "$log_fpath"
}

collect_page_fault_count $1 $2