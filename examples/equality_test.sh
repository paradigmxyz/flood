#!/bin/bash

export NODE1=ip.address.1:8545
export NODE2=ip.address.2:8545

flood all node1=$NODE1 node2=$NODE2 --equality

