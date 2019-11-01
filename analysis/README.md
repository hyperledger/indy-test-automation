# Metrics and logs analysis toolset

**NOTICE: Currently scripts are of PoC quality, expect rough edges**

## How to use

- install `influxdb` python package (preferably with pip in virtual environment with python3) 
- run `start_database.sh` - this will start docker containers with InfluxDB and Grafana
- open `localhost:3000` in browser and login to Grafana, then
  - add InfluxDB data source pointing at `http://indy-load-influxdb:8086`
  - upload `general_metrics.json` dashboard
- run `upload_metrics.py` - it will look for `logs/metrics/metrics*.csv` files
- optionally run `upload_logs.py` - it will look for `logs/Node*.log*` files
  - this can take some time, for example it took 30 minutes to upload 3 Gb of uncompressed logs 
  - compression looks quite good - aforementioned 3 Gb of logs took about 350 Mbs inside database
- look at dashboard, analyze metrics and logs, create new dashboards (don't forget to save and commit them so others can use them as well)
- when you're done you can run `stop_database.sh` to stop and remove all related containers and docker volumes

