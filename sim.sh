#!/bin/bash

############ Run simulations with HOOMD-blue on GPUs ################

GPU_COUNT=`nvidia-smi --list-gpus | wc -l`
FREE_GPUS=()
GPU_USAGES=()
CONTAINER_NAME="hoomd-sim"
CURRENT_FILES="./simulations/current_files.txt"


if [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
	echo Main command to run HOOMD simulations from yaml files.
	echo
	echo Usage: ./sim.sh [command]
	echo 
	echo Commands:
	echo  - check   Check GPU usage
	echo  - run     Run simulation
	echo
	echo Note: the simulated project names are written to current_files.txt.
fi


if [[ $GPU_COUNT -lt 1 ]]; then
	echo NVIDIA GPU required to run simulations, but none were detected on the system.
	exit 5
fi



function check_gpus() {
	
	if [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
		echo Check status of GPUs.
		echo 
		echo Usage: ./glab.sh check [commnad]
		echo 
		echo Commands:
		echo  - all       List all info
		echo  - finished  List finsihed tasks
	fi


	#IFS="," read -ra current_files < ./current_files.txt
	IFS="," read -ra current_files < $CURRENT_FILES

	if [[ $# -eq 0 ]]; then
		task="all"
	else
		task=$1
	fi


	if [[ $task == "all" ]]; then

		for (( i=0; i<GPU_COUNT; i++ ));
		do
			
			fname="File name was not found in current_files.txt"
			if [[ ! -z ${current_files[$i]} ]]; then
				fname=`basename ${current_files[$i]}`
			fi

			status_msg="working on"
			if [ "${GPU_USAGES[$i]}" == 0 ]; then
				status_msg="finished"
			fi
			echo GPU $i usage: ${GPU_USAGES[$i]}%, $status_msg: $fname
		done
	
	fi


	if [[ $task == "finished" ]]; then

		for (( i=0; i<GPU_COUNT; i++ ));
		do
			if [[ "${GPU_USAGES[$i]}" -eq 0 ]]; then
				echo GPU $i finished: `basename ${current_files[$i]}`
			fi
		done;

	fi

}


# --- Verify GPUs
for gpu in $(seq 0 $(($GPU_COUNT-1)))
do 
	u=$(nvidia-smi --id=$gpu --query-gpu="utilization.gpu" --format="csv,noheader,nounits")
	GPU_USAGES+=( $u )
	if [ $u -eq 0 ]; then
		FREE_GPUS+=( $gpu )
	fi
done


if [[ $1 == "check" ]]; then
	shift;
	check_gpus "$@";
	exit 0
fi


if [[ $1 == "run" ]]; then

	shift 1
	if [ $# -ne 1 ]; then
		echo Invalid usage of command, please reference --help.
		exit 10
	fi

	if [ "${#FREE_GPUS[@]}" -eq 0 ]; then
		echo There is no GPU available to carry out computations.
		exit 1
	fi

	gpu="${FREE_GPUS[0]}"
	echo Will use GPU: $gpu


	docker exec -i \
		$CONTAINER_NAME \
		bash -c "python3 ./main.py $1 $gpu"

	exit 0

fi

echo "Command $1 not recognized. Type --help for help."
exit 100
