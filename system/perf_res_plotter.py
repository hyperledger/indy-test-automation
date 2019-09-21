import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

sns.set()

metrics = [
    'ordered_batch_size_per_sec',
    'backup_ordered_batch_size_per_sec',
    'client_stack_messages_processed_per_sec',
    'avg_monitor_avg_latency',
    'avg_request_queue_size',
    'avg_monitor_unordered_request_queue_size',
    'max_view_change_in_progress',
    'max_current_view',
    'max_domain_ledger_size',
    'avg_node_rss_size',
    'avg_node_prod_time',
    'max_node_prod_time',
    'timestamp'
]


def plot_metrics(paths, save_path=None):  # takes list of paths to csv metrics files
    titles = [path.split('/')[-1].replace('.csv', '') for path in paths]
    for path, title in zip(paths, titles):
        try:
            pd.read_csv(path).loc[:, metrics].plot(
                x='timestamp', subplots=True, cmap='cool', title=title, figsize=(20, 10),  # logy=True
            )
        except pd.errors.EmptyDataError:
            plt.clf()
            plt.plot()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()


def plot_client_stats(path):  # takes path to `total`
    data = pd.read_csv(path, sep='|')
    data = data.loc[data['status'] == 'succ', :]
    data['latency'] = data['client_reply'] - data['client_sent']
    test_time = np.max(data['client_reply']) - np.min(data['client_sent'])
    print('MEAN LATENCY: {}'.format(np.mean(data['latency'])))
    print('MEAN THROUGHPUT: {}'.format(len(data.index)/test_time))


if __name__ == '__main__':
    plot_metrics([
        '/home/indy/indy-node/scripts/ansible/logs/metrics/metrics1.csv'
    ])
    # plot_client_stats('/home/indy/total_writes.csv')
