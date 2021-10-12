from influxdb import InfluxDBClient
from collections import defaultdict

BATCH_SIZE = 10000


def line_to_points(node_id, labels, line):
    timestamp = line[0]
    measurements = defaultdict(dict)
    for label, value in zip(labels[1:], line[1:]):
        if label.endswith('_count_per_sec'):
            measurements[label[:-len('_count_per_sec')]]['count_per_sec'] = float(value)
            continue
        if label.endswith('_per_sec'):
            measurements[label[:-len('_per_sec')]]['per_sec'] = float(value)
            continue
        if label.startswith('min_'):
            measurements[label[len('min_'):]]['min'] = float(value)
            continue
        if label.startswith('max_'):
            measurements[label[len('max_'):]]['max'] = float(value)
            continue
        if label.startswith('avg_'):
            measurements[label[len('avg_'):]]['avg'] = float(value)
            continue
    return [{
        'measurement': measurement.strip(),
        'time': timestamp,
        'tags': {'host': 'Node{}'.format(node_id)},
        'fields': fields
    } for measurement, fields in measurements.items()]


def upload_metrics(client, node_id):
    print("Uploading metrics from node {}".format(node_id))
    with open('logs/metrics/metrics{}.csv'.format(node_id), 'rt') as f:
        labels = f.readline().split(',')
        points = []
        for line in f:
            points.extend(line_to_points(node_id, labels, line.split(',')))
            if len(points) > BATCH_SIZE:
                client.write_points(points)
                points.clear()


client = InfluxDBClient('localhost', 8086, 'root', 'root', 'load-results')
client.create_database('load-results')
for i in range(25):
    upload_metrics(client, i+1)
