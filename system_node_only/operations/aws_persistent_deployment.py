import boto3
from pprint import pprint
from system.utils import PERSISTENT_INSTANCES, ORIGINAL_MAPPING, UPGRADE_MAPPING  # instance ids are the same for now
import time
import botocore


REGION_NAMES = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
    'ap-northeast-1', 'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'sa-east-1'
]
DEVICE = '/dev/sda1'
OWNER = '962610246670'  # !!! EXTERNAL PRs MUST NOT CHANGE THIS VALUE !!!


def get_persistent_instance_ids():  # use this if instance ids will change
    instance_ids = {}
    for region_name in REGION_NAMES:
        instance_ids[region_name] = []
        ec2_client = boto3.client('ec2', region_name=region_name)
        result = ec2_client.describe_instances()
        for reservation in result['Reservations']:
            sec_groups = ''
            for sec_group_dict in reservation['Instances'][0]['SecurityGroups']:
                sec_groups += sec_group_dict['GroupName']
            if reservation['Instances'][0]['KeyName'] == 'Evernym-QA-Pool'\
                    and sec_groups.find('QA-Live-Node-Persistent') != -1:
                instance_ids[region_name].append(reservation['Instances'][0]['InstanceId'])
    pprint(instance_ids)
    return instance_ids


def get_instances(instance_ids):
    instances = {}
    for k, v in instance_ids.items():
        ec2_resource = boto3.resource('ec2', region_name=k)
        instances[k] = [ec2_resource.Instance(_id) for _id in v]
    pprint(instances)
    return instances


def operate_instances(action, instances, instance_ids=None):  # action -> 'start' | 'stop'
    if instance_ids:  # create instance objects from ids and then operate with them
        for k, v in instance_ids.items():
            ec2_resource = boto3.resource('ec2', region_name=k)
            _instances = [ec2_resource.Instance(_id) for _id in v]
            print([getattr(_instance, action)() for _instance in _instances])
    else:  # operate with instance objects directly
        for k, v in instances.items():
            print([getattr(instance, action)() for instance in v])


def operate_volumes(action, instances, mapping, instance_ids=None):  # action -> 'detach_volume' | 'attach_volume'
    if instance_ids:  # create instance objects from ids and then operate with them
        for k, v in instance_ids.items():
            ec2_resource = boto3.resource('ec2', region_name=k)
            _instances = [ec2_resource.Instance(_id) for _id in v]
            for _instance in _instances:
                try:
                    res = getattr(_instance, action)(Device=DEVICE, VolumeId=mapping[_instance.id])
                    print(res)
                except botocore.exceptions.ClientError as e:
                    pass
    else:  # operate with instance objects directly
        for k, v in instances.items():
            for instance in v:
                try:
                    res = getattr(instance, action)(Device=DEVICE, VolumeId=mapping[instance.id])
                    print(res)
                except botocore.exceptions.ClientError as e:
                    pass


def get_persistent_snapshot_ids(find_version):
    snapshot_ids = {}
    for region_name in REGION_NAMES:
        snapshot_ids[region_name] = []
        ec2_client = boto3.client('ec2', region_name=region_name)
        result = ec2_client.describe_snapshots(OwnerIds=[OWNER])
        for snapshot in result['Snapshots']:
            if snapshot['Description'].split('-')[0] == find_version:
                snapshot_ids[region_name].append(snapshot['SnapshotId'])
    pprint(snapshot_ids)
    return snapshot_ids


def create_volumes_from_snapshots():
    pass


def switch_volumes_for_upgrade():
    operate_instances('stop', get_instances(PERSISTENT_INSTANCES))
    time.sleep(60)  # FIXME use EC2.Waiter.InstanceStopped
    operate_volumes('detach_volume', get_instances(PERSISTENT_INSTANCES), ORIGINAL_MAPPING)
    # FIXME use EC2.Waiter.VolumeAvailable
    operate_volumes('attach_volume', get_instances(PERSISTENT_INSTANCES), UPGRADE_MAPPING)
    time.sleep(60)  # FIXME use EC2.Waiter.VolumeInUse
    operate_instances('start', get_instances(PERSISTENT_INSTANCES))


def switch_volumes_for_load():
    operate_instances('stop', get_instances(PERSISTENT_INSTANCES))
    time.sleep(60)  # FIXME use EC2.Waiter.InstanceStopped
    operate_volumes('detach_volume', get_instances(PERSISTENT_INSTANCES), UPGRADE_MAPPING)
    # FIXME use EC2.Waiter.VolumeAvailable
    operate_volumes('attach_volume', get_instances(PERSISTENT_INSTANCES), ORIGINAL_MAPPING)
    time.sleep(60)  # FIXME use EC2.Waiter.VolumeInUse
    operate_instances('start', get_instances(PERSISTENT_INSTANCES))


if __name__ == '__main__':
    operate_instances('stop', get_instances(PERSISTENT_INSTANCES))
    time.sleep(60)
    operate_instances('start', get_instances(PERSISTENT_INSTANCES))
