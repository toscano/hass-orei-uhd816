import asyncio
from pyOreiMatrix import OreiMatrixAPI
import logging
import sys

_LOGGER = logging.getLogger(__name__)

def MatrixChangeHandler(changedObject):
    _LOGGER.info(f"<--{changedObject}")

async def main():

    def initializeLogging():
        # root logger
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        # Create a handler that writes to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)  # Set the handler's logging level

        # Create a formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
        handler.setFormatter(formatter)

        root.addHandler(handler)


    initializeLogging()

    api = OreiMatrixAPI(host = "192.168.20.19")

    _LOGGER.info(f"Starting tests on {api.host} tcpPort:{api.tcpPort} webPort:{api.webPort}...")

    if not await api.Validate():
        exit(100)

    await api.RefreshAll()
    _LOGGER.info(f"{api}")


    _LOGGER.info("--")

    if len(await api.Inputs) < 1:
        _LOGGER.error("No Matrix Inputs found.")
        exit(200)

    #for input in await api.Inputs:
    #    _LOGGER.info(f"   {input}")

    #_LOGGER.info("--")

    if len(await api.Outputs) < 1:
        _LOGGER.error("No Matrix Outputs found.")
        exit(300)

    #for output in await api.Outputs:
    #    _LOGGER.info(f"   {output}")

    _LOGGER.info("Waiting for changes...")

    api.SubscribeToChanges(MatrixChangeHandler)
    await asyncio.sleep(60)
    api.UnsubscribeFromChanges(MatrixChangeHandler)

    _LOGGER.info("Success.")


if __name__ == "__main__":
    asyncio.run(main())