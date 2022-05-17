#!/bin/bash

### Build docker image from Dockerfile

HOOMD_GID=1011

docker build \
	--tag hoomd-lab \
	--build-arg HOOMD_GID=$HOOMD_GID . 
