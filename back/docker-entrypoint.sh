#!/bin/bash

export USER=take
export HOME=/home/$USER

uid=$(stat -c "%u" .)
gid=$(stat -c "%g" .)

if [ "$BUILD_MODE" == "devel" ]; then
  if [ "$(id -u)" -eq 0 ]; then
    sd=""  
  else
    sd="sudo"
  fi
  if [ "$(id -g $USER)" -ne $gid ]; then
    $sd getent group $gid >/dev/null 2>&1 || $sd groupmod -g $gid $USER
    $sd chgrp -R $gid $HOME
  fi
  if [ "$(id -u $USER)" -ne $uid ]; then
    $sd usermod -u $uid $USER
  fi
fi

if [ "$(id -u)" -eq 0 ]; then
  exec setpriv --reuid=$USER --regid=$USER --init-groups "$@"
else
  ## TODO. error after changing uid and gid.
  # groups: cannot find name for group ID 1000
  # bash: /home/take/.bashrc: Permission denied
  exec "$@"
fi

