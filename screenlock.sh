#!/bin/bash
# first lock keepassxc
qdbus org.keepassxc.KeePassXC.MainWindow /keepassxc org.keepassxc.MainWindow.lockAllDatabases
# try to stop music with playerctl
if test -x /usr/bin/playerctl
then
    playerctl -a pause
fi

# now start locking screen
TMPBG=/tmp/screen.png
LOCK=$HOME/i3scripts/lock.png
RES=$(xrandr | grep 'current' | sed -E 's/.*current\s([0-9]+)\sx\s([0-9]+).*/\1x\2/')
 
ffmpeg -f x11grab -video_size $RES -y -i $DISPLAY -i $LOCK -filter_complex "boxblur=5:1,overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2" -vframes 1 $TMPBG -loglevel quiet
# call lock binary
i3lock -i $TMPBG
rm $TMPBG
