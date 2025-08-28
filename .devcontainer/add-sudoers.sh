#!/bin/bash

export USERNAME=take

# [Optional] Add sudo support. Omit if you don't need to install software after connecting.
apt-get update \
  && apt-get install -y sudo \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME

