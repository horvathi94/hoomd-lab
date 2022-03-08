import sys
from src.parser import Parser
from src import md
from src.simulation import Simulation



def main(args: list) -> None:

    fname = str(args[0])
    gpu = int(args[1])
    parser = Parser(fname)
    project_name = parser.simulation.project
    if parser.simulation.is_run():
        print(f"Running sim project: {project_name} on GPU {gpu}")
    elif parser.simulation.is_continue():
        print(f"Continuing sim project: {project_name} on GPU {gpu}")
    elif parser.simulation.is_fork():
        print(f"Forking sim project: {project_name} on GPU {gpu}")
    md.mdrun(parser.simulation, gpu)



if __name__ == "__main__":

    main(sys.argv[1:])
