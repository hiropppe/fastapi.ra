#!/bin/bash

export USER=take
export HOME=/home/$USER

uid=$(stat -c "%u" .)
gid=$(stat -c "%g" .)

if [ "$(id -u)" -eq 0 ] && [ "$uid" -ne 0 ]; then
  if [ "$(id -g $USER)" -ne $gid ]; then
      getent group $gid >/dev/null 2>&1 || groupmod -g $gid $USER
      chgrp -R $gid $HOME
  fi
  if [ "$(id -u $USER)" -ne $uid ]; then
      usermod -u $uid $USER
  fi
fi

if [ "$(id -u)" -eq 0 ]; then
  exec setpriv --reuid=$USER --regid=$USER --init-groups "$@"
else
  exec "$@"
fi

