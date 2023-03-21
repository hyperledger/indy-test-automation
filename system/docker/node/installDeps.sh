#!/bin/bash
apt-get update -y
if [[ "${CALL_FROM_NODE}" == "\"yes\"" ]]; then
    echo "node get Deps"
    bash ./getDepsNode.sh ${EXTENTION_DEB}
fi

if [[ "${CALL_FROM_EXTENTION}" == "\"yes\"" ]]; then
    echo "sovrin get Deps"
    bash ./getDeps.sh ${EXTENTION_DEB}
fi

aptStr=$(cat /tmp/aptStr)
echo "Installing dependancies:"
echo "${aptStr}"
echo
apt install -y $(pwd)/${EXTENTION_DEB} ${aptStr}
ln -s /usr/lib/ursa/libursa.so /usr/lib/libursa.so