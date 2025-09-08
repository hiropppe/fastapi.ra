## Base Stage
FROM ubuntu:22.04 as base

ARG USERNAME=take
ARG USER_UID=1000
ARG USER_GID=1000

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
 && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME 

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and other necessary packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential pkg-config locales tzdata \
    curl jq less \
    ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Set up locale
RUN locale-gen ja_JP.UTF-8

# Copy app
RUN mkdir -p /app/back
COPY . /app/back
RUN chown -R $USERNAME:$USERNAME /app

WORKDIR /app/back

USER $USERNAME

# Set environment variables for locale and timezone
ENV LANG=ja_JP.UTF-8
ENV TZ=Asia/Tokyo
ENV PATH=${PATH}:/home/$USERNAME/.local/bin

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN echo 'eval "$(uv generate-shell-completion bash)"' >> $HOME/.bashrc

# Install Python dependencies
RUN uv sync --reinstall

USER root

# Copy entrypoint
COPY docker-entrypoint.sh /
#RUN chown $USERNAME:$USERNAME /docker-entrypoint.sh && chmod 0500 /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["bash"]


## Devel Stage 
FROM base as devel

USER root

# Install dev packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends neovim python3-neovim git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Add sudo support. Omit if you don't need to install software after connecting.
RUN apt-get update \
 && apt-get install -y sudo \
 && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME

ENV BUILD_MODE=devel

USER $USERNAME


## Runtime Stage
FROM base as runtime

ENV BUILD_MODE=runtime

CMD ["uv", "run", "python3", "app/main.py"]

USER $USERNAME

