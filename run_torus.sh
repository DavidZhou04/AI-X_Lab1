#!/bin/bash

# gem5 可执行文件路径
GEM5=./build/NULL/gem5.opt
# 配置脚本
CONFIG=configs/example/garnet_synth_traffic.py

# 输出结果存放目录
OUTDIR=results_torus_escape

mkdir -p $OUTDIR

# 从 0.01 到 0.50，步长 0.01
for rate in $(seq 0.01 0.01 0.50); do
    echo "Running injection rate = $rate"

    # 为每个 rate 创建单独目录
    RUN_DIR=$OUTDIR/inj_${rate}
    mkdir -p $RUN_DIR

    $GEM5 \
        --outdir=$RUN_DIR \
        $CONFIG \
        --network=garnet --num-cpus=64 --num-dirs=64 \
        --topology=Torus_Escape --mesh-rows=4 --mesh-depth=4 \
        --inj-vnet=0 --synthetic=uniform_random \
        --sim-cycles=10000 --injectionrate=$rate \
        --routing-algorithm=4
done
