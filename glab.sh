#!/bin/bash

#### Fresh 
# $1 - Filename
# $2 - Project
# $3 - GPU

#### Continue
# $1 - continue
# $2 - Filename
# $3 - GPU


# Create temp file
tempfile=$(date "+%Y%m%d_%H%M_%S").tmp
args="$@"


# Check gpu usage:
GPU=$3
usage=$(nvidia-smi --id=$GPU --query-gpu='utilization.gpu' --format='csv,noheader,nounits')

#if [ $usage -gt 0 ]; then
#	echo "GPU: $GPU is already working, usage ($usage%). Exiting..."
#	exit 1
#fi

echo "Doing sim on GPU: $GPU"


# Run simulation
docker exec -i \
	hoomd_glotzerlab_1 \
	bash -c "python3 new/main.py $args" #> $tempfile
