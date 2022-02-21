import sys
from src.parser import Parser, ContParser
from src import run
from src import run_continue


def runmd(args: list) -> None:
    filename, project, gpu = args
    parser = Parser(filename, project)
    sim = parser.read()
    run.run(sim, int(gpu))


def continue_run(args: list) -> None:

    filename, gpu = args
    parser = ContParser(filename)
    sim = parser.read_simulation()
    run_continue.run(sim, int(gpu))



def test(args: list) -> None:
    filename = args[0]
    parser = Parser(filename, "test")
    sim = parser.read()
    for rbdata in sim.rigidbodies:
        rb = rbdata["rb"]
        print(rb.label)
        print(rb)
        print("-"*80)


def main(args: list) -> None:

    if args[0] == "continue":
        continue_run(args[1:])
        return
    if args[0] == "test":
        test(args[1:])
        return
    runmd(args)


if __name__ == "__main__":

    main(sys.argv[1:])
