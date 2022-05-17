#!/bin/bash

############ Initialize container and build image if necessary ################

HOOMD_GID=1011
IMAGE_NAME="hoomd-lab"
CONTAINER_NAME="hoomd-sim"


if [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
	echo Start hoomd-lab container to run simulations.
	echo Build Docker image if necessary.
	echo
	echo Usage: 
	echo ./container.sh          - to run container.
	echo ./container.sh build    - to build image and run container.

fi

is_build=false
is_init=true


if [[ $# -eq 1 ]] && [[ $1 == "build" ]]; then
	echo Building image...

	docker build \
		--tag $IMAGE_NAME \
		--build-arg HOOMD_GID=$HOOMD_GID . 
fi


mkdir -p simulations


echo Spinning up container...
docker run -d \
	--name $CONTAINER_NAME \
	--volume simulations:/hoomd-examples/workdir/simulations \
	$IMAGE_NAME






