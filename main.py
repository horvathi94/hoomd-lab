import sys
from src.parser import Parser
from src import md
from src.simulation import Simulation



def main(args: list) -> None:

    fname = str(args[0])
    gpu = int(args[1])
    parser = Parser(fname)
    if parser.simulation.is_run():
        print(f"Running sim project: {sim.project} on GPU {gpu}")
    elif parser.simulation.is_continue():
        print(f"Continuing sim project: {sim.project} on GPU {gpu}")
    elif parser.simulation.is_fork():
        print(f"Forking sim project: {sim.project} on GPU {gpu}")
    md_continue.run(sim, gpu)



if __name__ == "__main__":

    main(sys.argv[1:])
