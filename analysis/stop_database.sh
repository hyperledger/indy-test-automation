#!/bin/bash
docker rm -vf indy-load-grafana
docker rm -vf indy-load-influx
docker network rm indy-load-net
