#!/bin/bash

PROGRAMS=( evolution telegram-desktop signal-desktop rambox spotify )

for p in "${PROGRAMS[@]}"
do
    if pgrep -f "$p" >/dev/null 2>&1 ; then
	echo "$p already running"
    else
	$p >/dev/null 2>&1 & disown
    fi
done
