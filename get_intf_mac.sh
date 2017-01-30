#!/bin/bash

docker exec $1 ip addr show $2 | grep ether | awk '{print $2}'