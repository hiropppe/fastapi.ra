FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /root

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential pkg-config locales tzdata \
    neovim python3-neovim git curl jq less \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen ja_JP.UTF-8

ENV LANG=ja_JP.UTF-8
ENV TZ=Asia/Tokyo
ENV PATH=${PATH}:/root/.local/bin

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN echo 'eval "$(uv generate-shell-completion bash)"' >> $HOME/.bashrc

RUN mkdir -p /app/back
COPY . /app/back

WORKDIR /app/back

RUN uv sync --reinstall

COPY docker-entrypoint.sh /
RUN chown root:root /docker-entrypoint.sh && chmod 700 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

RUN ["bash"]
