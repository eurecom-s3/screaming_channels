#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# Profile
sc-attack --norm --data-path $TRACES_CHES20/ches20/hwcrypto/USRP_B210/10cm/false/ --start-point 1825 --end-point 1925 --num-traces 350000 profile /tmp/ecb/hw_k --pois-algo r --num-pois 1 --variable hw_k
sc-attack --norm --data-path $TRACES_CHES20/ches20/hwcrypto/USRP_B210/10cm/false/ --start-point 1825 --end-point 1925 --num-traces 350000 profile /tmp/ecb/hw_p --pois-algo r --num-pois 1 --variable hw_p
sc-attack --norm --data-path $TRACES_CHES20/ches20/hwcrypto/USRP_B210/10cm/false/ --start-point 1825 --end-point 1925 --num-traces 350000 profile /tmp/ecb/hw_c --pois-algo r --num-pois 1 --variable hw_c

# Figure 16
python src/screamingchannels/sc-compare.py --plot --template-dir-3 /tmp/ecb/hw_c /tmp/ecb/hw_p/ /tmp/ecb/hw_k/  compare
