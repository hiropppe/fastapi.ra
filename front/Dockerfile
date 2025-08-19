FROM ubuntu:22.04

ARG USERNAME=take
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential locales tzdata \
    wget vim git curl jq \
    nodejs npm

# Set locale
RUN locale-gen ja_JP.UTF-8

# Set timezone
ENV LANG=ja_JP.UTF-8
ENV TZ=Asia/Tokyo
ENV PATH=${PATH}:/root/.local/bin

# Install Node.js and npm
RUN npm install n -g
RUN n stable
RUN apt-get purge -y nodejs npm

RUN mkdir -p /app/front
COPY . /app/front
RUN chown -R $USER_UID:$USER_GID /app
 
WORKDIR /app/front

# Install Node.js dependencies
RUN npm install

COPY docker-entrypoint.sh /
RUN chown $USER_UID:$USER_GID /docker-entrypoint.sh && chmod 0700 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
 
CMD ["bash"]

# [Optional] Set the default user. Omit if you want to keep the default as root.
USER $USERNAME

