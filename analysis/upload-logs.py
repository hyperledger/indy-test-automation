import os, re, lzma
from influxdb import InfluxDBClient

BATCH_SIZE = 10000


def line_to_point(node_id, line):
    try:
        timestamp, severity, source, msg = line.split('|', maxsplit=4)
        return {
            'measurement': 'log-entry',
            'time': timestamp,
            'tags': {
                'host': 'Node{}'.format(node_id),
                'severity': severity.lower(),
                'source': source
            },
            'fields': {
                'msg': msg
            }
        }
    except:
        return


def upload_log(client, node_id, filename):
    print("Uploading {}...".format(filename))

    open_fn = lzma.open if filename.endswith('.xz') else open
    with open_fn(filename, 'rt') as f:
        points = []
        for line in f:
            point = line_to_point(node_id, line)
            if not point:
                continue
            points.append(point)
            if len(points) >= BATCH_SIZE:
                client.write_points(points)
                points.clear()


client = InfluxDBClient('localhost', 8086, 'root', 'root', 'load-results')
client.create_database('load-results')

log_filename_matcher = re.compile("Node(\d+).log.*")
matches = [log_filename_matcher.search(name) for name in os.listdir('logs')]
log_filenames = [(m.group(0), m.group(1)) for m in matches if m]

for filename, node_id in log_filenames:
    upload_log(client, node_id, os.path.join('logs', filename))
