#!/bin/bash

display_usage() {
	echo "Usage:\t$0 <TIMEZONE> <NODEIPLIST> <NODECOUNT> <CLIENTCOUNT> <REPO>"
	echo "EXAMPLE: $0 /usr/share/zoneinfo/America/Denver 10.20.30.201,10.20.30.202,10.20.30.203,10.20.30.204 4 4 stable"
}

# if less than one argument is supplied, display usage
if [  $# -ne 5 ]
then
    display_usage
    exit 1
fi

TIMEZONE=$1
NODEIPLIST=$2
NODECOUNT=$3
CLIENTCOUNT=$4
REPO=$5

echo "TIMEZONE=${TIMEZONE}"
echo "NODEIPLIST=${NODEIPLIST}"
echo "NODECOUNT=${NODECOUNT}"
echo "CLIENTCOUNT=${CLIENTCOUNT}"
echo "REPO=${REPO}"

#--------------------------------------------------------
echo 'Setting Up Networking'
cp /vagrant/etc/hosts /etc/hosts
perl -p -i -e 's/(PasswordAuthentication\s+)yes/$1no/' /etc/ssh/sshd_config
service sshd restart

#--------------------------------------------------------
echo 'Setting up timezone'
cp $TIMEZONE /etc/localtime

#--------------------------------------------------------
echo "Installing Required Packages"
apt-get update
apt-get install -y software-properties-common python-software-properties
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
add-apt-repository "deb https://repo.sovrin.org/deb xenial ${REPO}"
add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial ${REPO}"

## Add Evernym's Root CA
#mkdir -p /usr/local/share/ca-certificates
#cat <<EOF | sudo tee /usr/local/share/ca-certificates/Evernym_Root_CA.crt
#-----BEGIN CERTIFICATE-----
#MIIFJTCCAw2gAwIBAgIUMI0Z8YSLeRq8pZks40O3Dq2m8TIwDQYJKoZIhvcNAQEL
#BQAwGjEYMBYGA1UEAxMPRXZlcm55bSBSb290IENBMB4XDTE3MTAxMTIwMTAxMFoX
#DTQ3MTAwNDIwMTAzOVowGjEYMBYGA1UEAxMPRXZlcm55bSBSb290IENBMIICIjAN
#BgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA1kjmtmMfLJfsqUNaco44N3brW8Vu
#b02lAeEwbxc65mwfAG8kAjW7kYhI/fDXFOYXUvoa3Dg7bFeEatdIjHOahZssGM27
#HsQZ4PfRhPE6HtXFszmDwXWuEekVxoyueTqL7ExnNZ+BRTXvPfm5nw1E7L3o3xHF
#GSOtWFCyHfKd1LwMKzAVSjxlawEZnfk3WK3NxrC4UYMlQaDme7m3rCMfO+KBQk69
#bFXsgn6/EihVeQ8T1+T8gogofzh5b4Z7kS6e6GMqotbGFg4agejkRVsIglSpaQLk
#2Ztn/MP1dwgyvO4uvplB4sxZSC2FhhovlwPETmbKsnpj020+m0+YU4FPKwjroMiH
#tP//YqiNKsLxtjhffW7XFToyy0qQttW5RMWnyx4MXs9Hwcy29gY1izeGMSzz3zV5
#HG8JSJikuYbYiGJRVS0egovkVjja6lrVk0Q4Hm5pbw4l7LYCd6bkDLMsRaS1QnWs
#9iz6XEf5SpIu1FuqHmlhj1ABehUyGIg5oC6egML3q78yk0mCW523qMFa9Kjnk871
#mmXSCn3p/3DCrwWYfpcibxtVaKyJj6ISYIcl+Zu65Uzmhf+nj56x3gkNgEOva7JS
#Xge+FxPxsaXBGyeSH09nNIoNmh/UucuzpNY2UyCpJuqXHtR5jaACSdsqNxG8tcDg
#K9v98D/DFiShghECAwEAAaNjMGEwDgYDVR0PAQH/BAQDAgEGMA8GA1UdEwEB/wQF
#MAMBAf8wHQYDVR0OBBYEFOrH4oUpB94gNDNqdGG92kdVZ3qkMB8GA1UdIwQYMBaA
#FOrH4oUpB94gNDNqdGG92kdVZ3qkMA0GCSqGSIb3DQEBCwUAA4ICAQCwjN3ggZ98
#BXT39fKkCX3FHb0++aFcIyMKWrcZIpYrl3GoZsNKZK4QNQ+uJOP8xmqgyrCoMfch
#VIGPQ0RDN/IzqCLhc/U3pDmk2hXa3xTxD3gpCQZ6Bz04KlcLfZd5jzbI741bVDyF
#a1n46bEyuqV4SsNJWI/FGokJCNcZH66njBQBaQAccZ7xB9vWU9yjIYtGQDDvSm6J
#SC2knrQri0vv4QLUSc1LS6AlWWSQxcCpcdO+OzIFGsf5bVmYN6J4R3COY5NyQ+yn
#pOSN2NOh5h3ZrYAxm3i4Il0orVLveVcTVDGeAgZUII4YLJi/01RHGqit3aCuApSh
#bzFTZ5FldFss+JX9iAhqpFDbHLgae0F3QmYEnGilt/PzO4j23QJo3FZKeruQLH7P
#L9aOgN6S2+Akbbm9YTc59yzU5TZMxANwTdaYFWFqk/8nKgZiBR1l8jnWTlWnm86A
#qVssH3DLKwiYrWSOHRzGuN5BmPXxxtKQJlwAXt0wJE3puUkaJSRo7CJQ3QNMoKDe
#OjzXc9WvkFIXr3Eui8UTiHB/WT7N4o8hmVN404akGfWE0YNwRVfWpjGdew6g0tZi
#lFnjUUk49av67um43JHcinT5NFPuleZzkjaL/D8ueOrjXQDy05rwVdgmw9pXog4B
#Tw6APXtEnjfD2H8HOpOX/7ef4gWK0O1Q7A==
#-----END CERTIFICATE-----
#EOF
#sudo update-ca-certificates
## Trust Evernym's GPG signing key
#curl https://repo.corp.evernym.com/repo.corp.evenym.com-sig.key | sudo apt-key add -
#add-apt-repository "deb https://repo.corp.evernym.com/deb evernym-agency-dev-ubuntu main"

apt-get update

# Indy node is needed to provide the "generate_indy_pool_transactions"
# executable used below.
# The following deps are for Chaos: python3 python3-venv libffi-dev
DEBIAN_FRONTEND=noninteractive apt-get install -y unzip make screen indy-node indy-cli libsovtoken tmux vim wget python3 python3-venv libffi-dev

# Required by generate_indy_pool_transactions script
awk '{if (index($1, "NETWORK_NAME") != 0) {print("NETWORK_NAME = \"sandbox\"")} else print($0)}' /etc/indy/indy_config.py> /tmp/indy_config.py
mv /tmp/indy_config.py /etc/indy/indy_config.py

#--------------------------------------------------------
echo 'Setup SSH and Chaos pool configuration...'
usernames=(
  "ubuntu"
  "vagrant"
)

for username in "${usernames[@]}"
do
  # Create user
  useradd ${username}

  # Setup pool directory in user's home directory
  echo 'Copy generated (by Vagrantfile) pool (pool1) directory required by Chaos experiments'
  mkdir -m 700 -p /home/${username}/pool1
  cp -rf /vagrant/pool1/* /home/${username}/pool1/
  chmod 600 /home/${username}/pool1/ssh_config
  sed -i.bak s/\<USERNAME\>/${username}/g /home/${username}/pool1/ssh_config
  chmod 644 /home/${username}/pool1/clients
  chown -R ${username} /home/${username}/pool1

  # Setup ssh
  mkdir -m 700 -p /home/${username}/.ssh
  cp -f /vagrant/ssh/id_rsa* /home/${username}/.ssh/
  cp -f /home/${username}/pool1/ssh_config /home/${username}/.ssh/config
  PUB_KEY=$(cat /home/${username}/.ssh/id_rsa.pub)
  grep -q -F "${PUB_KEY}" /home/${username}/.ssh/authorized_keys 2>/dev/null || echo "${PUB_KEY}" >> /home/${username}/.ssh/authorized_keys
  chmod 600 /home/${username}/.ssh/authorized_keys
  chown -R ${username} /home/${username} 

  # Generate the pool_transactions_genesis file
  echo 'Generating Genesis Transaction Files required by Chaos experiments for user ${username}'
  su - ${username} -c "generate_indy_pool_transactions --nodes ${NODECOUNT} --clients ${CLIENTCOUNT} --ips ${NODEIPLIST}"

  # Copy the generated pool_transactions_genesis file into the pool1 directory
  echo 'Copy the generated pool_transactions_genesis fil into /home/${username}/pool1/'
  cp -f /home/${username}/.indy-cli/networks/sandbox/pool_transactions_genesis /home/${username}/pool1/
  chmod 644 /home/${username}/pool1/pool_transactions_genesis

  # Give the user passwordless sudo
  echo "Give user ${username} passwordless sudo rights..."
  echo "${username} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/chaos_${username}

  # Must have a clone of indy-node in user's home directory (symlink is
  # sufficient). Needed for loading the cluster with traffic using the
  # indy-node/scripts/performance/perf_load/perf_processes.py script.
  echo "Creating synlink to indy-node in ${username}'s home directory..."
  ln -sf /src/indy-node /home/${username}/indy-node

  # Create a Chaos python virtualenv
  echo "Setting up Chaos python virtualenv..."
  su - ${username} -c "python3 -m venv /home/${username}/.venvs/chaostk"

  # Note: Can't activate a virtualenv and then install dependencies. Rather the
  #       pip3 and python3 executables within chaostk should be used (relative
  #       or absolute path) in order to get dependencies installed within the
  #       chaostk virtualenv.

  echo "Pre-installing all requirements. For some reason the python3 setup.py"
  echo "develop commands below don't work the same when executing from a"
  echo "vagrant init script vs. when the command is run from a shell on the VM."
  # Must install wheel first!
  echo "Installing wheel in chaostk..."
  su - ${username} -c "/home/${username}/.venvs/chaostk/bin/pip3 install wheel"

  # Force all requirements to be pip3 installed.
  echo "Preinstalling all chaosindy dependecies defined in requirements.txt and requirements-dev.txt..."
  su - ${username} -c "/home/${username}/.venvs/chaostk/bin/pip3 install $(cat /src/indy-test-automation/chaos/requirements.txt | xargs)"
  su - ${username} -c "/home/${username}/.venvs/chaostk/bin/pip3 install $(cat /src/indy-test-automation/chaos/requirements-dev.txt | xargs)"
  # Install chaosindy in the virtualenv
  echo "Installing chaosindy within chaostk virtualenv..."
  # Important - Running the python3 setup.py develop as as the given user
  #             results in a permission denied, because the
  #             indy-test-automation clone is shared from the vagrant host
  cd /src/indy-test-automation/chaos && /home/${username}/.venvs/chaostk/bin/python3 setup.py develop

  # Force all requirements to be pip3 installed.
  echo "Preinstalling all chaossovtoken dependecies defined in requirements.txt and requirements-dev.txt..."
  su - ${username} -c "/home/${username}/.venvs/chaostk/bin/pip3 install $(cat /src/sovrin-test-automation/chaos/requirements.txt | xargs)"
  su - ${username} -c "/home/${username}/.venvs/chaostk/bin/pip3 install $(cat /src/sovrin-test-automation/chaos/requirements-dev.txt | xargs)"
  # Install chaossovtoken in the virtualenv
  echo "Installing chaossovtoken within chaostk virtualenv..."
  # Important - Running the python3 setup.py develop as as the given user
  #             results in a permission denied, because the
  #             sovrin-test-automation clone is shared from the vagrant host
  cd /src/sovrin-test-automation/chaos && /home/${username}/.venvs/chaostk/bin/python3 setup.py develop

  # Enhance the .profile 
  profilefile="/home/${username}/.profile"

  # Source chaostk virtualenv on login
  echo 'source ~/.venvs/chaostk/bin/activate' >> ${profilefile}

  # Setup aliases
  # TODO: install indy-test-automation (at minimum) and create aliases for all
  #       monitor-* and reset-* scripts found in the
  #       /src/indy-test-automation/chaos/scripts. Doing so allows the repo
  #       to add/remove scripts. Aliases effectively become dynamic when
  #       provisioning on 'vagrant up' and/or 'vagrant up --provision'.

  # Aliases convenient for changing directory to chaos directory under each source repo
  repos=(
    "indy"
    "sovrin"
  )

  run_all_paths=
  for repo in "${repos[@]}"
  do
    aliasname="cd${repo}"
    if ! grep -q ${aliasname} "${profilefile}"; then
      echo alias cd${repo}="\"cd /src/${repo}-test-automation/chaos\"" >> ${profilefile}
      echo alias run${repo}="\"cd /src/indy-test-automation/chaos && ./run.py pool1 --experiments='{\\\"path\\\": [\\\"/src/${repo}-test-automation/chaos\\\"]}'\"" >> ${profilefile}
      if [ "${run_all_paths}" == "" ]
        then
          run_all_paths="\\\"/src/${repo}-test-automation/chaos\\\""
        else
          run_all_paths="${run_all_paths}, \\\"/src/${repo}-test-automation/chaos\\\""
        fi
      fi
  done

  # Add runall if not already in profilefile
  if ! grep -q "runall" "${profilefile}"
  then
    # Add runall if run_all_paths is not empty
    if [ ! -z "${run_all_paths}" ]
    then
      echo alias runall="\"cd /src/indy-test-automation/chaos && ./run.py pool1 --experiments='{\\\"path\\\": [${run_all_paths}]}'\"" >> ${profilefile}
    fi
  fi

  # Aliases convenient for monitoring pool stats using 'watch' command
  monitors=(
    "all"
    "services"
    "catchup"
    "master"
    "replicas"
  )

  for monitor in "${monitors[@]}"
  do
    aliasname="monitor${monitor}"
    if ! grep -q ${aliasname} "${profilefile}"; then
      echo alias monitor${monitor}="\"watch -n5 '/src/indy-test-automation/chaos/scripts/monitor-${monitor} 2>/dev/null'\"" >> ${profilefile}
    fi
  done

  # Aliases convenient for resetting pool stats using 'watch' command
  resets=(
    "pool"
  )

  for reset in "${resets[@]}"
  do
    aliasname="reset${reset}"
    if ! grep -q ${aliasname} "${profilefile}"; then
      echo alias reset${reset}="/src/indy-test-automation/chaos/scripts/reset-${reset}" >> ${profilefile}
    fi
  done
done

#--------------------------------------------------------
echo 'Cleaning Up'
rm /etc/update-motd.d/10-help-text
apt-get update
#DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
updatedb
