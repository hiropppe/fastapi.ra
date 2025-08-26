#!/bin/bash

export USER=take
export HOME=/home/$USER

uid=$(stat -c "%u" .)
gid=$(stat -c "%g" .)

if [ "$uid" -ne 0 ]; then
  if [ "$(id -g $USER)" -ne $gid ]; then
      sudo getent group $gid >/dev/null 2>&1 || sudo groupmod -g $gid $USER
      sudo chgrp -R $gid $HOME
  fi
  if [ "$(id -u $USER)" -ne $uid ]; then
      sudo usermod -u $uid $USER
  fi
fi

if [ "$(id -u)" -eq 0 ]; then
  exec setpriv --reuid=$USER --regid=$USER --init-groups "$@"
else
  exec "$@"
fi

