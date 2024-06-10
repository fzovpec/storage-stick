#!/bin/bash

if [ $# != 3 ]; then
    echo "Usage: $0 <memory group name> <memory limit (MB)> <memory+swap limit (MB)"
    exit 1
fi

function create_memory_group()
{
    local group_name=$1
    local mem_limit=$2
    local memswap_limit=$3

    sudo cgcreate -g memory:/"$group_name"
    sudo cgset -r memory.limit_in_bytes="$mem_limit"M "$group_name"
    sudo cgset -r memory.memsw.limit_in_bytes="$memswap_limit"M mygroup
}

create_memory_group $1 $2 $3