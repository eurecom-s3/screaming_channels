#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# git checkout ches20

# Profile device E in at 10cm in line of sight
#sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces 37000 --mimo ch1 profile --variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1 /tmp/ch1_37000
#sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces 37000 --mimo ch2 profile --variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1 /tmp/ch2_37000
#sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces 37000 --mimo eg profile  --variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1 /tmp/eg_37000
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces 37000 --mimo mr profile  --variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1 /tmp/mr_37000

# Profile device F at 1m in office
sc-attack --norm --data-path $TRACES_CHES20/ches20/shannon_080719/1m/switched/template_tx_500/ --start-point 800 --end-point 1100 --num-traces 10000 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/1m_10000

# to realign the pois we can correlate the trace or even do it manually
# we see a constant offset of 73
# we could also get them from another collection taken with the same
# template.npy
# for simplicity we do
cp /tmp/mr_37000/POIS.npy /tmp/1m_10000

# Attacks same device
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/55cm_parallel_attack_obstacles_tx_500/ --mimo ch1 \
--start-point 400 --end-point 630 --num-traces 1990 --bruteforce --bit-bound-end 28  attack /tmp/mr_37000 --variable p_xor_k --average-bytes; \
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/55cm_parallel_attack_obstacles_tx_500/ --mimo ch2 \
--start-point 400 --end-point 630 --num-traces 1990 --bruteforce --bit-bound-end 28  attack /tmp/mr_37000 --variable p_xor_k --average-bytes; \
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/55cm_parallel_attack_obstacles_tx_500/ --mimo eg \
--start-point 400 --end-point 630 --num-traces 1990 --bruteforce --bit-bound-end 28  attack /tmp/mr_37000 --variable p_xor_k --average-bytes; \
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/55cm_parallel_attack_obstacles_tx_500/ --mimo mr \
--start-point 400 --end-point 630 --num-traces 1990 --bruteforce --bit-bound-end 28  attack /tmp/mr_37000 --variable p_xor_k --average-bytes; \

# Attack Reuse
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/55cm_parallel_attack_obstacles_tx_500/ --mimo mr --start-point 400 --end-point 630 --num-traces 1990 --bruteforce attack /tmp/1m_10000/ --variable p_xor_k
