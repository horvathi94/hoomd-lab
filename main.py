import sys
from src.parser import Parser
from src import run
from src import run_continue

"""
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

"""

def test(args: list) -> None:
    print(f"\nRunning test....")
    filename = args[0]
    parser = Parser(filename)
    print(parser)



def main(args: list) -> None:

    print(args)
    return
    if args[0] == "continue":
        continue_run(args[1:])
        return
    if args[0] == "test":
        test(args[1:])
        return
    runmd(args)


if __name__ == "__main__":

    main(sys.argv[1:])
