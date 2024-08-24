import mode
import uvloop

from . import app

if __name__ == "__main__":
    uvloop.install()

    worker = mode.Worker(
        app.PunquoteService(),
        loglevel="INFO",
    )

    worker.execute_from_commandline()
