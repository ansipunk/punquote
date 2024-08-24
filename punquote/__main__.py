import mode

from . import app

if __name__ == "__main__":
    worker = mode.Worker(
        app.PunquoteService(),
        loglevel="INFO",
    )

    worker.execute_from_commandline()
