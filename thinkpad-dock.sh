#!/bin/sh -e

# Save this file as /usr/local/sbin/thinkpad-dock.sh

# NB: you will need to modify the username and tweak the xrandr
# commands to suit your setup.

# wait for the dock state to change
sleep 0.5
#DOCKED=$(cat /sys/devices/platform/dock.0/docked)  # not working since some kernel version

username=conrad

#export IFS=$"\n"

if [[ "$ACTION" == "add" ]]; then
  DOCKED=1
  logger -t DOCKING "Detected condition: docked"
elif [[ "$ACTION" == "remove" ]]; then
  DOCKED=0
  logger -t DOCKING "Detected condition: un-docked"
else
  logger -t DOCKING "Detected condition: unknown"
  echo Please set env var \$ACTION to 'add' or 'remove'
  exit 1
fi

# invoke from XSetup with NO_KDM_REBOOT otherwise you'll end up in a KDM reboot loop
NO_KDM_REBOOT=0
for p in $*; do
  case "$p" in
  "NO_KDM_REBOOT") NO_KDM_REBOOT=1 ;;
  "SWITCH_TO_LOCAL") DOCKED=0 ;;
  esac
done

function switch_to_local {
    export DISPLAY=$1
    export XAUTHORITY=/home/conrad/.Xauthority
    #export XAUTHORITY=$(find /var/run/kdm -name "A${DISPLAY}-*")
    #export XAUTHORITY=/var/run/lightdm/sflaniga/xauthority
    logger -t DOCKING "Switching off other displays and switching on internal display"
    su $username -c '/usr/local/sbin/i3plug.py save' > /tmp/i3plug.log 2>&1
    su $username -c '
        /usr/bin/xrandr \
    	  --output eDP-1 --primary --mode 1920x1080 --pos 0x0 --rotate normal \
	  --output HDMI-1 --off \
      	  --output HDMI-2 --off \
      	  --output DP-1 --off \
      	  --output DP-2 --off \
      	  --output DP-2-1 --off \
      	  --output DP-2-2 --off \
      	  --output DP-2-3 --off \
	  ';
    nmcli radio wifi on;
}

function switch_to_external {
  export DISPLAY=$1
  export XAUTHORITY=/home/conrad/.Xauthority
  #export XAUTHORITY=/var/run/lightdm/sflaniga/xauthority
  #export XAUTHORITY=$(find /var/run/kdm -name "A${DISPLAY}-*")

  # The Display port on the docking station is on HDMI2 - let's use it and turn off local display
  logger -t DOCKING "Switching off internal display and switching on external setup"

  su $username -c '
    /usr/bin/xrandr \
      --output DP-2-2 --primary --mode 1920x1200 --pos 0x0 --rotate normal \
      --output DP-2-1 --mode 1920x1200 --pos 1920x0 --rotate normal \
      --output DP-2-3 --off \
      --output eDP-1 --off \
      --output HDMI-2 --off \
      --output HDMI-1 --off \
      --output DP-2 --off \
      --output DP-1 --off \
    '
  # alternative:
  # xrandr --output LVDS1 --off --output HDMI3 --primary --auto --pos 0x0
  # --output HDMI2 --auto --rotate left --pos 1680x-600

  # this will probably fail ("Configure crtc 2 failed"):
  #/usr/bin/xrandr --output LVDS1 --auto
  sleep 1;
  #systemctl restart NetworkManager.service
  nmcli radio wifi off;
  su $username -c '/usr/local/sbin/i3plug.py restore' > /tmp/i3plug.log 2>&1
}

case "$DOCKED" in
  "0")
    #undocked event
    switch_to_local :0 ;;
  "1")
    #docked event
    switch_to_external :0 ;;
esac
