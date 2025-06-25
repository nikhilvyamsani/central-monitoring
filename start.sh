#!/bin/bash
docker run -d \
  --name my-monitor \
  --network host \
  --privileged \
  -v /:/host:ro,rslave \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v my-monitor-data:/var/lib/grafana \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=password \
  -e MYSQL_DB=take_leap \
  -e MYSQL_PORT=3306 \
  --restart unless-stopped \
  nikhilvyamsani/my-monitor:latest