import os
import json
import re
import pandas as pd

BASE_DIR = '/home/indy/indy-node/scripts/ansible/logs/'
NODE_INFO_DIR = BASE_DIR + 'node_info/'
JCTL_DIR = BASE_DIR + 'jctl/'
METRICS_DIR = BASE_DIR + 'metrics/'


def get_nodes_info(file_names, path=NODE_INFO_DIR):
    results = []

    for file_name in file_names:
        with open(path + file_name) as json_file:
            results.append(json.load(json_file))

    return results


if __name__ == '__main__':
    # form empty csv report
    columns = [
        'DOMAIN_TXNS_WRITTEN',
        'TOKEN_TXNS_WRITTEN',
        'TXNS_EXPECTED',
        'VIEW_NO',
        'JCTL_EXCEPTIONS',
        'LOG_ERRORS'
    ]
    rows = list(range(1, 26))
    report = pd.DataFrame(columns=columns, index=rows)

    # get info file paths and sort them in natural order
    node_info_file_names = sorted(
        [x for x in os.listdir(NODE_INFO_DIR) if (x.find('additional') == -1 and x.find('version') == -1)],
        key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]
    )

    for i, result in enumerate(get_nodes_info(node_info_file_names), start=1):
        report.loc[[i], ['DOMAIN_TXNS_WRITTEN']] = result['Node_info']['Metrics']['transaction-count']['ledger']
        report.loc[[i], ['TOKEN_TXNS_WRITTEN']] = result['Node_info']['Metrics']['transaction-count']['1001']
        report.loc[[i], ['VIEW_NO']] = result['Node_info']['View_change_status']['View_No']

    print(report)
