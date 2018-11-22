#!/bin/bash

display_usage() {
	echo -e "Usage:\t$0 <NODENAME> <NODEIP> <NODEPORT> <CLIENTIP> <CLIENTPORT> <TIMEZONE> <NODEIPLIST> <NODECOUNT> <CLIENTCOUNT> <REPO>"
	echo -e "EXAMPLE: $0 Node1 0.0.0.0 9701 0.0.0.0 9702 /usr/share/zoneinfo/America/Denver 10.20.30.201,10.20.30.202,10.20.30.203,10.20.30.204 4 4 stable"
}

# if less than one argument is supplied, display usage
if [  $# -ne 10 ]
then
    display_usage
    exit 1
fi

HOSTNAME=${1}
NODEIP=${2}
NODEPORT=${3}
CLIENTIP=${4}
CLIENTPORT=${5}
TIMEZONE=${6}
NODEIPLIST=${7}
NODECOUNT=${8}
CLIENTCOUNT=${9}
REPO=${10}

echo "HOSTNAME=$HOSTNAME"
echo "NODEIP=$NODEIP"
echo "NODEPORT=$NODEPORT"
echo "CLIENTIP=$CLIENTIP"
echo "CLIENTPORT=$CLIENTPORT"
echo "TIMEZONE=$TIMEZONE"
echo "NODEIPLIST=$NODEIPLIST"
echo "NODECOUNT=$NODECOUNT"
echo "CLIENTCOUNT=$CLIENTCOUNT"
echo "REPO=$REPO"

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
#DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y unzip make screen indy-node tmux vim wget

awk '{if (index($1, "NETWORK_NAME") != 0) {print("NETWORK_NAME =\"sandbox\"")} else print($0)}' /etc/indy/indy_config.py> /tmp/indy_config.py
mv /tmp/indy_config.py /etc/indy/indy_config.py

#--------------------------------------------------------
[[ $HOSTNAME =~ [^0-9]*([0-9]*) ]]
NODENUM=${BASH_REMATCH[1]}
echo "Setting Up $HOSTNAME as Indy Node Number $NODENUM"
echo "Node IP/PORT: $NODEIP $NODEPORT"
echo "Client IP/PORT: $CLIENTIP $CLIENTPORT"
su - indy -c "init_indy_node $HOSTNAME $NODEIP $NODEPORT $CLIENTIP $CLIENTPORT"  # set up /etc/indy/indy.env
echo "Generating indy pool transactions"
su - indy -c "generate_indy_pool_transactions --nodes ${NODECOUNT} --clients ${CLIENTCOUNT} --nodeNum $NODENUM --ips ${NODEIPLIST}"

#--------------------------------------------------------
echo 'Fixing Bugs'
echo 'Fixing indy-node init file...'
if grep -Fxq '[Install]' /etc/systemd/system/indy-node.service
then
  echo '[Install] section is present in indy-node target'
else
  perl -p -i -e 's/\\n\\n/[Install]\\nWantedBy=multi-user.target\\n/' /etc/systemd/system/indy-node.service
fi
echo 'Fixing indy_config.py file...'
if grep -Fxq 'SendMonitorStats' /etc/indy/indy_config.py
then
  echo 'SendMonitorStats is configured in indy_config.py'
else
  printf "\n%s\n" "SendMonitorStats = False" >> /etc/indy/indy_config.py
fi

#--------------------------------------------------------
echo 'Enable and start indy-node service'
systemctl start indy-node
systemctl enable indy-node
systemctl status indy-node.service

#--------------------------------------------------------
# Ensure each user in the usernames array below has the ssh key pair generated
# by the setup.sh script
echo 'Setup SSH...'
declare -a usernames=("ubuntu" "vagrant")

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
  echo "${username} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/chaos_${username}
done


#--------------------------------------------------------
echo 'Cleaning Up'
apt-get update
updatedb
