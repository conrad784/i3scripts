#!/bin/bash
. ~/i3scripts/net-speed.sh
i3status | (read line && echo "$line" && read line && echo "$line" && read line && echo "$line" && while :
do
  read line
  update_rate
  echo ",[{\"full_text\":\"${rate}\" },${line#,\[}" || exit 1
done)
