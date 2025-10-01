Simple e2e testing environment using Playwright

# SSH Port forwading (localhost->remote host)
ssh -vvv -L 9323:localhost:9323 user@192.168.xx.xxx -N

# Playwright container
docker-compose build
docker-compose up -d
docker exec -it e2e bash

# Run test
PW_TEST_CONNECT_WS_ENDPOINT=ws://192.168.xx.xxx:3000/ npx playwright test

# Run UI Mode
PW_TEST_CONNECT_WS_ENDPOINT=ws://192.168.xx.xxx:3000/ npx playwright test --ui-host 0.0.0.0 --ui-port 9323

