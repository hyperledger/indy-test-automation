#!/bin/bash
docker network create indy-load-net
docker run --network indy-load-net -d --name indy-load-influx -p 8086:8086 influxdb
docker run --network indy-load-net -d --name indy-load-grafana -p 3000:3000 grafana/grafana

