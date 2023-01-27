#!/bin/sh
sudo docker-compose down
sudo docker image rm application_scubot-nonebot
sudo docker image rm application_scubot-scripts
sudo docker-compose up -d
sudo docker logs -f scubot-gocq
