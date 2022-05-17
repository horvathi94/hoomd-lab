# HOOMD-lab 

Run simulations on HOOM-blue [[1]](#1) trough the use of *yaml* files. 


## Create Docker image

The customized version of the HOOMD-blue Docker can be created from the *Dockerfile* in the project, using the `docker build` command. Extras in this image:
- a group named *hoomd* is added with GID=1011 (change this in line 4)
- Python *dataclasses* package is installed


## Usage

After deploying the container use the `glab.sh` script to interact with it. There are two main commands:
- **check**: show GPU usages of the system
- **run**: run simulaitons from the specified *yaml* file

After executing the run command the parameters from the *yaml* file will be passed to the glotzeerlab container and the simulation run. Output from the container will be saved into the *simulations* directory. For each simulation three files are created:
-	a *.yaml* file, which contains all parameters of the simulation (the purpose of this file is to save simulation parameters for later use).
-	a *.gsd* file, which contains the trajectory of the system
-	a *.log* file, which contains some macromolecular properties of the system, logged by the HOOMD-blue software. These are: *potential energy*, *translational kinetic energy* and *rotational kinetic energy*.

The created files are named using the following convention:
<project-name>_<date-of-start>_<time-of-start>

**Important!**
The **project_name** parameter should be given at the start of each clean run and fork run *yaml* file. This parameter is important to help destinguish between your projects.



### YAML files:

The *yaml* files describe the particles, rigid bodies, unit cell, interactions and simulation parameters of the simulation, these are illustarted in the example configuration files in the *showcase/examples* directory.

There are three types of **actions** that can be run by the program, these are:
1. Clean run (keyword: **run**, this is the default value): This is a clean run, with the system being initialized from scratch with random placement of the rigid bodies.
2. Continue run (keyword: **continue**): This command is designed to continue an existing run from a specified frame.
3. Fork run (keyword: **fork**): This command is designed to continue from an existing simulation frame, but with changed simulation parameters.

Specify the **action** keyword at top level in the *yaml* file. For continued and forked runs the **base** keyword must be given, this describes the *yaml* file in the *simulations* directory from, which simulation should be continued or forked, as well as the index of the frame from which the new simulation should be started.
For more details on other parameters check the example files.


### Simulations:

The MD simulations are run roughly by:
- creating and writing the output *yaml*, with start date and start time set to the execution of the run command
- initializing HOOMD context on a free GPU: `hoomd.context.initialize(--gpu=<free-gpu>)`
- defining particles, rigid bodies and the simulation cell, given in the *yaml* file
- defining inter-particle interactions, given in the *yaml* file
- defining PPPM [[2]](#2) parameters (these are: Nx=64, Ny=64, Nz=64, order=4, rcut=6, alpha=0)
- defining integrator (Langevin integrator: `hoomd.md.integrate.langevin`) on rigid bodies and solvents
- defining data to be dumped to the log and trajectory file.
- running the simulation



### Refernces

<a id="1">[1]</a>
J. A. Anderson, J. Glaser, and S. C. Glotzer. HOOMD-blue: A Python package for high-performance molecular dynamics and hard particle Monte Carlo simulations. Computational Materials Science 173: 109363, Feb 2020. 10.1016/j.commatsci.2019.109363
<a id="2">[2]</a>
D. N. LeBard, B. G. Levine, P. Mertmann, S. A. Barr, A. Jusufi, S. Sanders, M. L. Klein, and A. Z. Panagiotopoulos. Self-assembly of coarse-grained ionic surfactants accelerated by graphics processing units. Soft Matter 8: 2385-2397, 2012. 10.1039/c1sm06787g
