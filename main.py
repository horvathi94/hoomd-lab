import sys
from src.parser import Parser
from src import md_run
from src import md_continue
from src import md_fork
from src.simulation import Simulation


def run(sim: Simulation, gpu: int) -> None:
    print(f"Running sim project: {sim.project} on GPU {gpu}")
    md_run.run(sim, gpu)


def continue_run(sim: Simulation, gpu: int) -> None:
    print(f"Continuing sim project: {sim.project} on GPU {gpu}")
    md_continue.run(sim, gpu)


def fork_run(sim: Simulation, gpu: int) -> None:
    print(f"Forking sim project: {sim.project} on GPU {gpu}")
    md_fork.run(sim, gpu)



def main(args: list) -> None:

    fname = str(args[0])
    gpu = int(args[1])
    parser = Parser(fname)
    if parser.simulation.is_run():
        run(parser.simulation, gpu)
        return
    if parser.simulation.is_continue():
        continue_run(parser.simulation, gpu)
        return
    if parser.simulation.is_fork():
        fork_run(parser.simulation, gpu)
        return



if __name__ == "__main__":

    main(sys.argv[1:])
