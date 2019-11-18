import os
from shutil import copyfile
import subprocess
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from system.analysis.perf_res_plotter import plot_metrics
from system.utils import run_external_cmd


NODES_NUM = 25
NATURAL_SORTING = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]
LOG_PATTERNS = [
    'blacklisting',
    'invalid BLS signature',
    'request digest is incorrect',
    'has incorrect digest',
    'time not acceptable',
    'incorrect state trie root',
    'incorrect transaction tree root',
    'has incorrect reject',
    'error in plugin field',
    'incorrect audit ledger',
]


class PathReg:
    def __init__(
            self, base_dir='/tmp/summary/', output_dir='/tmp/summary/'
    ):
        self._base_dir = base_dir
        self._output_dir = output_dir

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def output_dir(self):
        return self._output_dir

    @property
    def node_info_dir(self):
        return os.path.join(self.base_dir, 'node_info/')

    @property
    def jctl_dir(self):
        return os.path.join(self.base_dir, 'jctl/')

    @property
    def metrics_dir(self):
        return os.path.join(self.base_dir, 'metrics/')


path_reg = PathReg()
sub_dirs = [os.path.join(path_reg.output_dir, 'Node{}/'.format(i)) for i in range(1, NODES_NUM+1)]


class PerformanceReport:
    def __init__(self, columns=None, rows=None):
        self._columns = columns if columns else [
            'DOMAIN_TXNS_WRITTEN',
            # 'DOMAIN_TXNS_EXPECTED',
            'TOKEN_TXNS_WRITTEN',
            # 'TOKEN_TXNS_EXPECTED',
            'VIEW_NO',
            'VC_IN_PROGRESS',
            'HAS_WRITE_CONSENSUS'
            # 'JCTL_EXCEPTIONS',
            # 'LOG_ERRORS',
            # 'PATTERN_MATCHES'
        ]
        self._rows = rows if rows else list(range(1, NODES_NUM+1))
        self._report = pd.DataFrame(columns=self._columns, index=self._rows)
        # self.create_dirs()
        self.process_node_info()
        # self.process_journal_exceptions()
        # self.process_log_errors()
        # self.process_metrics()
        self.save_report()

    @property
    def report(self):
        return self._report

    @staticmethod
    def create_dirs(path=path_reg.output_dir, sub_dirs=sub_dirs):
        assert os.mkdir(path) is None
        assert all([os.mkdir(sub_dir) is None for sub_dir in sub_dirs])

    def save_report(self, path=path_reg.output_dir):
        # save csv
        self.report.to_csv(os.path.join(path, 'report.csv'))

        plt.clf()
        fig, ax = plt.subplots()

        # hide axes
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')

        ax.table(
            cellText=self.report.values, colLabels=self.report.columns, rowLabels=list(self.report.index), loc='center'
        )

        # save figure
        plt.savefig(os.path.join(path, 'report.png'), dpi=500)

    def process_node_info(self, path=path_reg.node_info_dir):

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
                with open(os.path.join(path, file_name)) as json_file:
                    try:
                        results.append(json.load(json_file))
                    except json.decoder.JSONDecodeError:
                        results.append({})

            return results

        for i, result in enumerate(get_node_info_as_dicts(), start=1):
            try:
                self._report.loc[[i], ['DOMAIN_TXNS_WRITTEN']] = \
                    result['Node_info']['Metrics']['transaction-count']['ledger']
            except KeyError:
                self._report.loc[[i], ['DOMAIN_TXNS_WRITTEN']] = None
            try:
                self._report.loc[[i], ['TOKEN_TXNS_WRITTEN']] = \
                    result['Node_info']['Metrics']['transaction-count']['1001']
            except KeyError:
                self._report.loc[[i], ['TOKEN_TXNS_WRITTEN']] = None
            try:
                self._report.loc[[i], ['VIEW_NO']] = \
                    result['Node_info']['View_change_status']['View_No']
            except KeyError:
                self._report.loc[[i], ['VIEW_NO']] = None
            try:
                self._report.loc[[i], ['VC_IN_PROGRESS']] = \
                    result['Node_info']['View_change_status']['VC_in_progress']
            except KeyError:
                self._report.loc[[i], ['VC_IN_PROGRESS']] = None
            try:
                self._report.loc[[i], ['HAS_WRITE_CONSENSUS']] = \
                    result['Node_info']['Freshness_status']['0']['Has_write_consensus']
            except KeyError:
                self._report.loc[[i], ['HAS_WRITE_CONSENSUS']] = None

    def process_journal_exceptions(self, path=path_reg.jctl_dir):

        def get_journal_exceptions_as_lists():  # return list of lists
            # get journal file paths and sort them in natural order
            journal_file_names = sorted(os.listdir(path), key=NATURAL_SORTING)
            print(journal_file_names)

            results = []
            ignore_list = ['grep', 'preauth', 'user']  # ignore excess entries
            for i, file_name in enumerate(journal_file_names):
                res = []
                try:
                    res += run_external_cmd(
                        'xzcat {} | sed -n "/Traceback/,/Error/p"'.format(os.path.join(path, file_name))
                    )
                except subprocess.CalledProcessError:
                    res += []
                res = [x for x in res if not any(map(x.__contains__, ignore_list))]

                results.append(res)

                # create file with exception entries for each node
                with open(sub_dirs[i] + 'exception_journal_entries.txt', 'w') as f:
                    for item in res:
                        f.write('{}\n'.format(item))

            return results

        for i, result in enumerate(get_journal_exceptions_as_lists(), start=1):
            self._report.loc[[i], ['JCTL_EXCEPTIONS']] = len(result)

    def process_log_errors(self, path=path_reg.base_dir):

        def get_log_errors_as_lists():  # return list of lists
            log_file_names = sorted(
                [x for x in os.listdir(path) if x.__contains__('log')],
                key=NATURAL_SORTING
            )
            print(log_file_names)

            node_keys = ['Node{}.'.format(i) for i in range(1, NODES_NUM+1)]
            results = []
            pattern_results = []
            for i, node_key in enumerate(node_keys):
                res = []
                pattern_res = []

                # find errors and patterns in logs including xz
                log_names = [x for x in log_file_names if x.__contains__(node_key)]
                for log_name in log_names:
                    try:
                        res += subprocess.check_output(
                            ['xzgrep', 'ERROR', os.path.join(path, log_name)]
                        ).decode().strip().splitlines()
                    except subprocess.CalledProcessError:
                        res += []

                    for item in LOG_PATTERNS:
                        try:
                            pattern_res += subprocess.check_output(
                                ['xzgrep', item, os.path.join(path, log_name)]
                            ).decode().strip().splitlines()
                        except subprocess.CalledProcessError:
                            pattern_res += []

                results.append(res)
                pattern_results.append(pattern_res)

                # create file with error entries for each node
                with open(sub_dirs[i] + 'error_log_entries.txt', 'w') as f:
                    for item in res:
                        f.write('{}\n'.format(item))

                # create file with pattern matching entries for each node
                with open(sub_dirs[i] + 'pattern_log_entries.txt', 'w') as f:
                    for item in pattern_res:
                        f.write('{}\n'.format(item))

            return results, pattern_results

        error_results, pattern_results = get_log_errors_as_lists()

        for i, item in enumerate(error_results, start=1):
            self._report.loc[[i], ['LOG_ERRORS']] = len(item)
        for i, item in enumerate(pattern_results, start=1):
            self._report.loc[[i], ['PATTERN_MATCHES']] = len(item)

    @staticmethod
    def process_metrics(path_from=path_reg.metrics_dir, paths_to=sub_dirs):
        ignore_list = ['summary', 'db']
        metric_file_names = sorted(
                [x for x in os.listdir(path_from) if not any(map(x.__contains__, ignore_list))],
                key=NATURAL_SORTING
            )

        # create metrics figure for each node
        assert all(
            [plot_metrics([os.path.join(path_from, metric_file_name)], os.path.join(path_to, 'Figure.png')) is None
             for metric_file_name, path_to in zip(metric_file_names, paths_to)]
        )

        summary_file_names = sorted(
                [x for x in os.listdir(path_from) if x.__contains__('summary')],
                key=NATURAL_SORTING
            )

        # copy metrics summary for each node
        assert all(
            [copyfile(os.path.join(path_from, summary_file_name), os.path.join(path_to, summary_file_name)) is not None
             for summary_file_name, path_to in zip(summary_file_names, paths_to)]
        )

        # # generate and save summary figure FIXME subplots can't contain other subplots so now it looks bad
        # plt.clf()
        # for i, metric_file_name in enumerate(metric_file_names, start=1):
        #     plt.subplot(5, 5, i)
        #     data = pd.read_csv(os.path.join(path_from, metric_file_name)).loc[:, metrics]
        #     plt.plot(data['timestamp'], data['ordered_batch_size_per_sec'], 'g-')
        #     plt.plot(data['timestamp'], data['backup_ordered_batch_size_per_sec'], 'b-')
        # plt.savefig(os.path.join(path_reg.output_dir, 'SummaryFigure.png'))


if __name__ == '__main__':
    print(PerformanceReport().report)
