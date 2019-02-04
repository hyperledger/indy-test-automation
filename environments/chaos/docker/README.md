# Summary
This is additional dockerfiles for [indy-node docker environment](https://github.com/hyperledger/indy-node/tree/master/environment/docker/pool) which add ability to run chaos experiments on docker pool. 
To start use docker environment for chaos experiments, copy (with replacement) all files from this directory to [indy-node docker scripts](https://github.com/hyperledger/indy-node/tree/master/environment/docker/pool).

# How to start nodes
1. Generate keys for access to node containers (scripts assume that name will be `dockerkey` and that keys will be in the same folder as scripts).
```
ssh-keygen -f dockerkey
```

2. Run `pool_start.sh` as described in [indy-node repo](https://github.com/hyperledger/indy-node/tree/master/environment/docker/pool#start-pool). 

# How to start client
1. Update `config` depending of how many nodes are you planning to use (by default `pool_start.sh` will create 4 nodes, so default config contains 4 nodes only).

2. Run `client_for_pool_start.sh` to start client container and `docker exec -it indyclient bash` to obtain access to terminal inside container. 

Chaos experiments can be found at `/root/indy-test-automation/chaos` on client container.

# How to clean up
* Use `pool_stop.sh` to remove nodes containers.
* Use `client_stop.sh` to remove client containers.
* Note that cached images will be used for next runs of `pool_start.sh` and `client_for_pool_start.sh`. Use command `docker rmi $(docker images -a -q)` to remove old images and to be able to use latest versions of indy-node and libindy.