# Summary
A Vagrant + Virtualbox project that sets up an Indy Chaos experiment development
environment comprised of 1 or more clients and 4 or more validator nodes. The
client(s) are configured with a python virtual environment (chaostk) in which
all dependencies for Chaos development are installed. The chaostk virtual
environment is activated/sourced on login and numerous aliases are available for
your convenience. See /home/[vagrant/ubuntu]/.profile on any of the VMs for
details.

# TODOs
Please consider completing the following as part of your efforts to contribute
to this project.

1. Copy the users ~/.vimrc to each VM if it exists on the Vagrant host. If one
   does not exist, copy the following at minimum to encourage some best
   practices for column width:
   ```
   highlight OverLength ctermbg=black ctermfg=white guibg=#592929
   match OverLength /\%81v.\+/
   ```

# Overview
Topics covered in this README:
* Installation
  * config.properties File
  * Setup - Please consider completing TODOs
  * Virtualbox
  * Vagrant
* Login
  * Client(s)
  * Validator(s)
* Aliases
* Running Experiments
* Writing Experiments
* Debugging Experiments
 
# Installation

# config.properties File
A `config.properties` file is used to manage/store all configurable options
within this project. The `config.properties` file is generated from the
`config.properties.template` file and should never be checked into version
control (`config.propoerties` is ignored by .gitignore). Please take a moment
and get familiar with each configurable option (open and read
config.properties.template). You do not need to modify the `config.properties`
file unless you need to add additional repos containing Chaos experiment
modules/source/etc.

# Source Control Management (SCM)
The standard Github Fork & Pull Request Workflow is required. Fork the following
projects:
[**indy-node**](https://github.com/hyperledger/indy-node)
[**indy-test-automation**](https://github.com/hyperledger/indy-test-automation)

Additional repos can be added to the config.properties file before or after
running the `setup` script mentioned below. For example, Chaos experiments that
test Indy Node/Plenum plugin functionality can be added for
[**sovrin-test-automation**](https://github.com/sovrin-foundation/sovrin-test-automation)
by copying config.properties.template to config.properties (if and only if it
does not already exist) and adding the following lines to config.properties:

```
# Sovrin Test Automation
repos.sovrin.test.automation.path=
repos.sovrin.test.automation.username=
repos.sovrin.test.automation.url=git@github.com:<USERNAME>/sovrin-test-automation.git
repos.sovrin.test.automation.git.private.key=~/.ssh/id_rsa
repos.sovrin.test.automation.branch=master
```

The `setup` script in the following section will clone the branch configured in
the config.properties file. The branch defaults to the repo's "default" branch
if not present in the properties file. If you want to use a different branch for
one or more of the repos, you can either clone each of the repos and checkout
the branch, or you can set the `branch` property for each repo
(repos.\<REPO\>.branch) and let the setup script clone the configured branch
before you run `vagrant up`.

## Setup
Run the setup script. The setup script will do the following:

1. Create an 'ssh' directory in the root of this vagrant project. The 'ssh'
   directory is included in .gitignore file, because we don't want to
   store keys in git.
2. Generate an SSH key pair and PEM file in the 'ssh' directory. Each vagrant VM
   will use this key pair for the `vagrant` and `ubuntu` user.
3. Copy the config.properties.template file to config.properties, if and only if
   it does not already exist.
4. Check that each of the repos defined in the confg.properties file
   (repos.<REPO>...) have been cloned to the root of this Vagrant project.
   If clones do not exist, you will have the option of specifying where the
   clone exists on disk, or the setup script will prompt you for your username
   and clone the repo assuming you have a fork at
   `https://github.com/<USERNAME>/<REPO>.git`.

   Each repo will be mounted to /src/\<REPO\> on each VM.

   Note that all files and folders found in the root of this project (where the
   Vagrantfile is located) are shared (bi-directionally) on each VM in the
   /vagrant directory.  In other words, changes made to
   /vagrant/<REPOS>|<FILES>|<DIRECTORIES> while logged into the vagrant VMs are
   effectively making changes to repos/files/folders in the root of this Vagrant
   project on your Vagrant host. The same is true for /src/\<REPO\> depending on
   the repos.\<REPO\>.sharedfolder.type property set in the config.properties
   file (not defined by default). When the sharedfolder.type property is not
   defined, Vagrant's default behavior is to decide the best method of sharing
   based on your systems capabilities. See Vagrant's
   [Synced Folders](https://www.vagrantup.com/docs/synced-folders/) feature
   documentation for details.

   Note: Commits should be authored/pushed from the vagrant host (not from the
   VM), because you will be a different user and have different keys while
   logged into the VM.

   1. **indy-node**:
      Shared as /src/indy-node on each VM. Only the client node(s) have a
      symlink (/home/[vagrant|ubuntu]/indy-node -> /src/indy-node) in the
      'vagrant' and 'ubuntu' home directories. The indy-node repo contains a
      perf_processes.py batch script used for load/stress testing and is used by
      Chaos experiments to generate load when needed. The Choas experiments
      expect a clone of the indy-node repo to be present on each client node in
      the home directory of the the user running chaos experiments.

   2. **indy-test-automation**:
      Shared as /src/indy-test-automation on each VM. A 'cdindy' alias is
      placed in /home/[vagrant|ubuntu]/.profile for convenience. When on client
      machines (i.e. cli1), running 'cdindy' changes directory to
      /src/indy-test-automation/chaos.

      Chaos experiments are found under the 'chaos' directory. This project has
      a 'run.py' script capable of running any/all chaos experiments, even in
      other repos (clones present on the same machine). The run script is
      maintained in this repo, because it is assumed (at this time) that all
      experiments either directly or indirectly (i.e. plugins) test
      indy-node/indy-plenum functionality. See
      '/src/indy-test-automation/run.py --help' for details.

      A run\<REPO\> (i.e. replace \<REPO\> with indy or sovrin) alias is placed
      in /home/[vagrant|ubuntu]/.profile for convenience in running _**all**_ of
      the experiments in the given repo. Login to a client (i.e. cli1) and run
      the 'alias' command to list all available aliases and get familiar with
      run\<REPO\> aliases.

      Several monitor\<SUFFIX\> (i.e. replace \<SUFFIX\> with 'all', 'catchup',
      'master', 'replicas', services', etc.) aliases are placed in
      /home/[vagrant|ubuntu]/.profile for convenience in monitoring aspects of
      the pool, ledgers, etc. Login to a client (i.e. cli1) and run the
      'alias' command to list all available aliases and get familiar with
      monitor\<SUFFIX\> aliases.

      Several reset\<SUFFIX\> (i.e. replace \<SUFFIX\> with 'pool', etc.)
      aliases are placed in /home/[vagrant|ubuntu]/.profile for convenience in
      resetting aspects of the pool, ledgers, etc. Login to a client
      (i.e. cli1) and run the 'alias' command to list all available aliases and
      get familiar with reset\<SUFFIX\> aliases.

   3. All other repos added will follow the same pattern:
      **\<REPO\>**:
      Shared as /src/\<REPO\> on each VM. A 'cd\<REPO\>' alias is placed in
      /home/[vagrant|ubuntu]/.profile for convenience. When on client machines
      (i.e. cli1), running 'cd\<REPO\>' changes directory to
      /src/\<REPO\>/chaos.

      Chaos experiments are found under the 'chaos' directory.

## Virtualbox

[Install Virtualbox](https://www.virtualbox.org/wiki/Downloads)

Tested with VirtualBox 5.2.16 r123759 (Qt5.6.3) on macOS 10.12.6 

## Vagrant

[Install Vagrant](https://www.vagrantup.com/docs/installation/)

Tested with Vagrant 2.1.2 on macOS 10.12.6 

Run `vagrant up`

# Login

You can ssh to any of the nodes using either `vagrant ssh \<HOST\>` or
`ssh vagrant@127.0.0.1 -p \<PORT\> -i ./ssh/id_rsa` where `./ssh/id_rsa` is the
ssh key created by running the setup script. Note that the port may be different
if the ports are already in use when you run `vagrant up`. Vagrant will pick the
next available port to map to port 22 if the configured port (in the
Vagrantfile) is already in use. If you want to use `ssh` instead of
`vagrant ssh` and you feel the port-picking feature of vagrant is annoying, you
can configure each VM in the Vagrantfile to use specific ports.
## Client(s)
### Vagrant
```
vagrant ssh cli1
```
### SSH
Note that when Vagrant maps port 22 (SSH) on the Vagrant guest (VM) to a port on
the Vagrant host (your machine - typically port 2222). The port numbers
may be different if Vagrant detects a collision (port already in use). If a
collision is detected, Vagrant assigns an available port
(i.e. 2200,2201,...,2221) and noitifies you of the collision and the unique port
mapping via stdout/stderr. This is likely a design choice by the Vagrant folks,
because `vagrant ssh <VM>` is the typical way a user will SSH to a Vagrant
managed VM.
```
ssh vagrant@127.0.0.1 -p 2222 -i ./ssh/id_rsa
```
## Validator(s)
### Vagrant
```
vagrant ssh validator1
vagrant ssh validator2
vagrant ssh validator3
vagrant ssh validator4
```
### SSH
Note that when Vagrant maps port 22 (SSH) on the Vagrant guest (VM) to a port on
the Vagrant host (your machine - typically port 2222). The port numbers
may be different if Vagrant detects a collision (port already in use). If a
collision is detected, Vagrant assigns an available port
(i.e. 2200,2201,...,2221) and noitifies you of the collision and the unique port
mapping via stdout/stderr. This is likely a design choice by the Vagrant folks,
because `vagrant ssh <VM>` is the typical way a user will SSH to a Vagrant
managed VM.
```
ssh vagrant@127.0.0.1 -p 2200 -i ./ssh/id_rsa
ssh vagrant@127.0.0.1 -p 2201 -i ./ssh/id_rsa
ssh vagrant@127.0.0.1 -p 2202 -i ./ssh/id_rsa
ssh vagrant@127.0.0.1 -p 2203 -i ./ssh/id_rsa
```

# Aliases
Login to the client (cli1) and run `alias` to familiarize yourself with aliases
added for your convenience.
In summary:
- **cd\<REPO\>** aliases change the working directory to the \<REPO\> source
  directory mounted on the VM from the vagrant host.
- **monitor\<SUFFIX\>** aliases monitor aspects of the pool/ledger/etc;
  producing human readable tabluar output refreshed periodically.
- **reset\<SUFFIX\>** aliases reset aspects of the pool/ledger/etc.
- **run\<REPO\>** aliases run _all_ of the Chaos experiments in a repo.

# Running Experiments
See ['Executing Experiments'](https://github.com/ckochenower/indy-test-automation/blob/master/chaos/README.md#executing-experiments) for details
In summary: There are two ways to run an experiment.
1. Using run.py
   See '/vagrant/indy-test-automation/run.py --help' for details.
2. Using the scripts/run-\<EXPERIMENT\> script
   Each experiment
   ('/vagrant/\<REPO\>-test-automation/chaos/experiments/\<EXPERIMENT\>') has a
   corresponding 'run-<EXPERIMENT>' script in the 'scripts' directory.
   ('/vagrant/\<REPO\>-test-automation/chaos/scripts/run-\<EXPERIMENT\>')
   See the --help output for each 'run-<EXPERIMENT>' script for details.

# Writing Experiments
See the
[README.md](https://github.com/hyperledger/indy-test-automation/chaos/README.md)
located in the indy-test-automation/chaos directory for details.
Finding a similar experiment, copying it
(\<REPO\>/chaos/experiments/\<EXPERIMENT\>.json) and it's associated 'run' script
(\<REPO\>/chaos/scripts/run-\<EXPERIMENT\> may be a good start.

# Debugging Experiments
You can place a 'import pdb; pdb.set_trace()' anywhere in python code and the
interpreter will hault when encountered.
