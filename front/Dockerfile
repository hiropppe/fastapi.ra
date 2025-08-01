FROM ubuntu:22.04
 
ENV DEBIAN_FRONTEND=noninteractive
 
WORKDIR /root
 
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential locales tzdata \
    wget vim git curl jq \
    nodejs npm
 
RUN locale-gen ja_JP.UTF-8
 
ENV LANG=ja_JP.UTF-8
ENV TZ=Asia/Tokyo
ENV PATH=${PATH}:/root/.local/bin
 
RUN npm install n -g
RUN n stable
RUN apt-get purge -y nodejs npm
 
RUN mkdir -p /app/front
COPY . /app/front
 
WORKDIR /app/front

RUN npm install

COPY docker-entrypoint.sh /
RUN chown root:root /docker-entrypoint.sh && chmod 700 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
 
CMD ["bash"]
