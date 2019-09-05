import os
from shutil import copyfile
import subprocess
import json
import re
import datetime
import pandas as pd
from system.perf_res_plotter import plot_metrics


NODES_NUM = 25
BASE_DIR = '/home/indy/indy-node/scripts/ansible/logs/'
NODE_INFO_DIR = BASE_DIR + 'node_info/'
JCTL_DIR = BASE_DIR + 'jctl/'
METRICS_DIR = BASE_DIR + 'metrics/'
OUTPUT_DIR = '/home/indy/performance-results__'+datetime.datetime.now().strftime('%d-%m-%Y__%H:%M/')
SUB_DIRS = [OUTPUT_DIR+'Node{}/'.format(i) for i in range(1, NODES_NUM+1)]
NATURAL_SORTING = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]


class PerformanceReport:
    def __init__(self, columns=None, rows=None):
        self._columns = columns if columns else [
            'DOMAIN_TXNS_WRITTEN',
            # 'DOMAIN_TXNS_EXPECTED',
            'TOKEN_TXNS_WRITTEN',
            # 'TOKEN_TXNS_EXPECTED',
            'VIEW_NO',
            'JCTL_EXCEPTIONS',
            'LOG_ERRORS'
        ]
        self._rows = rows if rows else list(range(1, NODES_NUM+1))
        self._report = pd.DataFrame(columns=self._columns, index=self._rows)
        self.create_dirs()
        self.process_node_info()
        self.process_journal_exceptions()
        self.process_log_errors()
        self.process_metrics()

    @property
    def report(self):
        return self._report

    @staticmethod
    def create_dirs(path=OUTPUT_DIR, sub_dirs=SUB_DIRS):
        assert os.mkdir(path) is None
        assert all([os.mkdir(sub_dir) is None for sub_dir in sub_dirs])

    def process_node_info(self, path=NODE_INFO_DIR):

        def get_node_info_as_dicts():  # return list of dicts
            # get info file paths and sort them in natural order
            ignore_list = ['additional', 'version']  # ignore excess files
            node_info_file_names = sorted(
                [x for x in os.listdir(path) if not any(map(x.__contains__, ignore_list))],
                key=NATURAL_SORTING
            )
            print(node_info_file_names)

            results = []
            # load json files as dicts
            for file_name in node_info_file_names:
                with open(path + file_name) as json_file:
                    results.append(json.load(json_file))

            return results

        for i, result in enumerate(get_node_info_as_dicts(), start=1):
            self._report.loc[[i], ['DOMAIN_TXNS_WRITTEN']] =\
                result['Node_info']['Metrics']['transaction-count']['ledger']
            self._report.loc[[i], ['TOKEN_TXNS_WRITTEN']] =\
                result['Node_info']['Metrics']['transaction-count']['1001']
            self._report.loc[[i], ['VIEW_NO']] =\
                result['Node_info']['View_change_status']['View_No']

    def process_journal_exceptions(self, path=JCTL_DIR):

        def get_journal_exceptions_as_lists():  # return list of lists
            # get journal file paths and sort them in natural order
            journal_file_names = sorted(os.listdir(path), key=NATURAL_SORTING)
            print(journal_file_names)

            results = []
            ignore_list = ['grep', 'preauth']  # ignore excess entries
            for file_name in journal_file_names:
                res = []
                try:
                    res += subprocess.check_output(
                        ['xzgrep', '-i', 'exception', path + file_name]
                    ).decode().strip().splitlines()
                except subprocess.CalledProcessError:
                    res += []
                try:
                    res += subprocess.check_output(
                        ['xzgrep', '-i', 'error', path + file_name]
                    ).decode().strip().splitlines()
                except subprocess.CalledProcessError:
                    res += []
                res = [x for x in res if not any(map(x.__contains__, ignore_list))]
                results.append(res)

            return results

        for i, result in enumerate(get_journal_exceptions_as_lists(), start=1):
            self._report.loc[[i], ['JCTL_EXCEPTIONS']] = len(result)

    def process_log_errors(self, path=BASE_DIR):

        def get_log_errors_as_lists():  # return list of lists
            log_file_names = sorted(
                [x for x in os.listdir(path) if (x.__contains__('log') and not x.__contains__('xz'))],
                key=NATURAL_SORTING
            )
            print(log_file_names)

            xz_file_names = sorted(
                [x for x in os.listdir(path) if x.__contains__('xz')],
                key=NATURAL_SORTING
            )
            print(xz_file_names)

            node_keys = ['Node{}.'.format(i) for i in range(1, NODES_NUM+1)]
            results = []
            for node_key in node_keys:
                res = []

                # find errors in all .log
                log_names = [x for x in log_file_names if x.__contains__(node_key)]
                if log_names:
                    for log_name in log_names:
                        try:
                            res += subprocess.check_output(
                                ['egrep', 'ERROR', path + log_name]
                            ).decode().strip().splitlines()
                        except subprocess.CalledProcessError:
                            res += []

                # find errors in all .xz
                xz_names = [x for x in xz_file_names if x.__contains__(node_key)]
                if xz_names:
                    for xz_name in xz_names:
                        try:
                            res += subprocess.check_output(
                                ['xzgrep', 'ERROR', path + xz_name]
                            ).decode().strip().splitlines()
                        except subprocess.CalledProcessError:
                            res += []

                results.append(res)

            return results

        for i, result in enumerate(get_log_errors_as_lists(), start=1):
            self._report.loc[[i], ['LOG_ERRORS']] = len(result)

    @staticmethod
    def process_metrics(path_from=METRICS_DIR, paths_to=SUB_DIRS):
        metric_file_names = sorted(
                [x for x in os.listdir(path_from) if not x.__contains__('summary')],
                key=NATURAL_SORTING
            )

        assert all(
            [plot_metrics([path_from+metric_file_name], path_to+'Figure.png') is None
             for metric_file_name, path_to in zip(metric_file_names, paths_to)]
        )

        summary_file_names = sorted(
                [x for x in os.listdir(path_from) if x.__contains__('summary')],
                key=NATURAL_SORTING
            )

        assert all(
            [copyfile(path_from+summary_file_name, path_to+summary_file_name) is not None
             for summary_file_name, path_to in zip(summary_file_names, paths_to)]
        )


if __name__ == '__main__':
    print(PerformanceReport().report)
