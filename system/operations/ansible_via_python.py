import json
import shutil
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context
import ansible.constants as C


context.CLIARGS = ImmutableDict(
    connection='ssh',
    module_path=None,
    forks=25,
    remote_user='ubuntu',
    private_key_file=None,
    ssh_common_args=None,
    ssh_extra_args=None,
    sftp_extra_args=None,
    scp_extra_args=None,
    become=True,
    become_method='sudo',
    become_user='root',
    verbosity=20,
    check=False
)

loader = DataLoader()

passwords = dict(vault_pass='secret')

inventory = InventoryManager(loader=loader, sources='/etc/ansible/hosts')

variable_manager = VariableManager(loader=loader, inventory=inventory)

play_source = dict(
        name='Ansible Play',
        hosts='pool',
        gather_facts='no',
        tasks=[
            dict(action=dict(module='shell', args='systemctl status indy-node'), register='shell_out'),
            dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
         ]
    )

play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

if __name__ == '__main__':
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  passwords=passwords,
              )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()

        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
