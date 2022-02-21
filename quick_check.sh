#!/bin/bash

IFS="," read -ra current_files < ./current_files.txt


for gpu_index in $(seq 0 5)
do
	usage=$(nvidia-smi --id=$gpu_index --query-gpu='utilization.gpu' --format='csv,noheader,nounits')

	if [[ $1 == "free" ]]; then

		# Check free GPUs

		if [[ $usage -lt 10 ]]; then
			echo "$gpu_index"
		fi


	elif [[ $1 == "finished" ]]; then

		# List finished files

		if [[ $usage -lt 10 ]]; then
			echo "$gpu_index: `basename ${current_files[$gpu_index]}`"
		fi

	else 

		# Basic command

		echo "GPU $gpu_index usage: $usage, working on: `basename ${current_files[$gpu_index]}`"
	fi


done
