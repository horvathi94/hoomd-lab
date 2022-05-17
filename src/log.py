from .utils import LOG_FILE

def log_current_file(fname: str, gpu: int) -> None:

    with open(LOG_FILE, "r") as log:
        raw = log.read()
    files = raw.split(",")
    files[gpu] = fname
    with open(LOG_FILE, "w") as log:
        log.write(",".join(files))
