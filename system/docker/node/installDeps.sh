#!/bin/bash
apt-get update -y

echo "Getting the top level dependencies for ${EXTENTION_DEB} ..."
MAX_DEPENDANCY_DEPTH=0 bash ./getDeps.sh ${EXTENTION_DEB}

aptStr=$(cat /tmp/aptStr)
echo "======================================================================="
echo "Installing the following dependancies along with ${EXTENTION_DEB}:"
echo "-----------------------------------------------------------------------"
echo "${aptStr}"
echo "======================================================================="
echo
apt install -y $(pwd)/${EXTENTION_DEB} ${aptStr}
if [ -f "/usr/lib/ursa/libursa.so" ]; then
  ln -s /usr/lib/ursa/libursa.so /usr/lib/libursa.so
fi
