#!/bin/bash

export TEST_DATA_DIR=/path/to/some/output/dir
export NODE1=username@ip.address.1:localhost:8545
export NODE2=username@ip.address.2:localhost:8545

#
# # run tests
#

flood eth_call \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_call \
    -r 1024 2048 4096 8192 16384

flood eth_getBalance \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getBalance \
    -d 1 \
    -r 1024 2048 4096 8192 16384

flood eth_getBlockByNumber \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getBlockByNumber \
    -r 1024 2048 4096 8192 16384

flood eth_getCode \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getCode \
    -r 1024 2048 4096 8192 16384

flood eth_getLogs \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getLogs \
    -r 64 128 256 512 1024

flood eth_getStorageAt \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getStorageAt \
    -r 1024 2048 4096 8192 16384

flood eth_getTransactionByHash \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getTransactionByHash \
    -r 1024 2048 4096 8192 16384

flood eth_getTransactionCount \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getTransactionCount \
    -r 2048 4096 8192 16384 32768

flood eth_getTransactionReceipt \
    node1=$NODE1 \
    node2=$NODE2 \
    --output $TEST_DATA_DIR/eth_getTransactionReceipt \
    -r 1024 2048 4096 8192 16384

#
# # generate report
#

cd $TEST_DATA_DIR

flood report \
    $TEST_DATA_DIR/eth_call \
    $TEST_DATA_DIR/eth_getBalance \
    $TEST_DATA_DIR/eth_getBlockByNumber \
    $TEST_DATA_DIR/eth_getCode \
    $TEST_DATA_DIR/eth_getLogs \
    $TEST_DATA_DIR/eth_getStorageAt \
    $TEST_DATA_DIR/eth_getTransactionByHash \
    $TEST_DATA_DIR/eth_getTransactionCount \
    $TEST_DATA_DIR/eth_getTransactionReceipt

