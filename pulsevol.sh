#!/bin/sh
#   pulsevol.sh
#
#   Usage:  pulsevol.sh [up|down|min|max|overmax|toggle|mute|unmute]
#

EXPECTED_ARGS=1
E_BADARGS=65
if [ $# -ne $EXPECTED_ARGS ]
then
    echo "Usage: `basename $0` [up|down|min|max|toggle|mute|unmute]"
    exit $E_BADARGS
fi

STEP=5
MAXVOLUME=150  # max vol in percent

getDefaultSinkIndex() {
    pactl list short sinks | sed -e 's,^\([0-9][0-9]*\)[^0-9].*,\1,' | head -n 1
}

getDefaultSinkVolPerc() {
    VOLUME=$( pactl list sinks | grep '^[[:space:]]Volume:' | head -n $(( $SINK + 1 )) | tail -n 1 | sed -e 's,.* \([0-9][0-9]*\)%.*,\1,' )
}

getDefaultSinkVolPerc;

setSinkVolPerc() {
    local num=$1

    if [ $num -gt $MAXVOLUME ]; then
	num=$MAXVOLUME
    elif [ $num -lt 0 ]; then
	num=0
    fi
    local vol=$((num * 655)); 
    vol=$((num * 36 / 100 + vol));
    # echo -e "\033[0;32mVol - ${num}:${vol}\033[0;m"
    pactl -- set-sink-volume $SINK $vol
}


up(){
    VOLUME="$(( $VOLUME+$STEP ))";
}

down(){
    VOLUME="$(( $VOLUME-$STEP ))";
}

max(){
    pacmd set-sink-volume $SINK $OVERMAX > /dev/null
}

min(){
    pacmd set-sink-volume $SINK 0 > /dev/null
}

mute(){
    pactl set-sink-mute $SINK 1 > /dev/null
    notify-send " " -i "audio-volume-muted" -h int:value:0 -h string:synchronous:volume
}

unmute(){
    pactl set-sink-mute $SINK 0 > /dev/null
}

toggle(){
    pactl set-sink-mute $SINK toggle
}

SINK=$(getDefaultSinkIndex)

case $1 in
up)
    up;;
down)
    down;;
max)
    max
    exit 0;;
min)
    min
    exit 0;;
toggle)
    toggle
    exit 0;;
mute)
    mute;
    exit 0;;
unmute)
    unmute;;
*)
    echo "Usage: `basename $0` [up|down|min|max|toggle|mute|unmute]"
    exit 1;;
esac

setSinkVolPerc $VOLUME

# get new value to VALUE to show in notify
getDefaultSinkVolPerc

if [ "$VOLUME" = "0" ]; then
        icon_name="audio-volume-off"
    else
        if [ "$VOLUME" -lt "33" ]; then
            icon_name="audio-volume-low"
        else
            if [ "$VOLUME" -lt "67" ]; then
                icon_name="audio-volume-medium"
            else
                icon_name="audio-volume-high"
            fi
        fi
fi

# only use this if replacing of windows works...
#notify-send " " -i $icon_name -h int:value:$VOLUME -h string:synchronous:volume
