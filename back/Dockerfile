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

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and other necessary packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential pkg-config locales tzdata \
    neovim python3-neovim git curl jq less \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up locale
RUN locale-gen ja_JP.UTF-8

# Set environment variables for locale and timezone
ENV LANG=ja_JP.UTF-8
ENV TZ=Asia/Tokyo
ENV PATH=${PATH}:/root/.local/bin

# Install Node.js and npm
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN echo 'eval "$(uv generate-shell-completion bash)"' >> $HOME/.bashrc

RUN mkdir -p /app/back
COPY . /app/back
RUN chown -R $USER_UID:$USER_GID /app

WORKDIR /app/back

# Install Python dependencies
RUN uv sync --reinstall

COPY docker-entrypoint.sh /
RUN chown $USER_UID:$USER_GID /docker-entrypoint.sh && chmod 0700 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

RUN ["bash"]

# [Optional] Set the default user. Omit if you want to keep the default as root.
USER $USERNAME

