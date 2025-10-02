FROM mcr.microsoft.com/playwright:v1.55.1-noble

WORKDIR /app/e2e

COPY . .

RUN npm install

RUN git config --global --add safe.directory /app

