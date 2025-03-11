import asyncio
from pyOreiMatrix import OreiMatrixAPI
import logging
import sys

_LOGGER = logging.getLogger(__name__)

def MatrixChangeHandler(changedObject):
    _LOGGER.info(f"CHANGE: {changedObject}")

async def wait_for_true(condition_func, check_interval=0.1, timeout=None):
    start_time = asyncio.get_event_loop().time()
    while True:
        if condition_func():
            return True
        if timeout is not None and (asyncio.get_event_loop().time() - start_time) > timeout:
            return False
        await asyncio.sleep(check_interval)

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

    _LOGGER.info(f"Starting tests on {api.host}...")

    if not await api.Validate():
        exit(100)

    await api.RefreshAll()
    _LOGGER.info(f"{api}")
    _LOGGER.info(f"{api.InputNames!r}")

    api.SubscribeToChanges(MatrixChangeHandler)


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
    api.PowerOn()
    if not await wait_for_true(lambda: api.power, timeout=10):
        _LOGGER.error("Power on failed.")
        exit(400)

    #await asyncio.sleep(3)

    api.PanelLockOn()
    if not await wait_for_true(lambda: api.panel_lock, timeout=10):
        _LOGGER.error("LockOn failed.")
        exit(400)

    api.PanelLockOff()
    if not await wait_for_true(lambda: not api.panel_lock, timeout=10):
        _LOGGER.error("LockOff failed.")
        exit(400)

    api.BeepOn()
    if not await wait_for_true(lambda: api.beep, timeout=10):
        _LOGGER.error("BeepOn failed.")
        exit(400)

    api.BeepOff()
    if not await wait_for_true(lambda: not api.beep, timeout=10):
        _LOGGER.error("BeepOff failed.")
        exit(400)


    _LOGGER.info("Waiting for changes...")


    await asyncio.sleep(20)


    api.PowerOff()
    if not await wait_for_true(lambda: not api.power, timeout=10):
        _LOGGER.error("Power off failed.")
        exit(400)

    api.UnsubscribeFromChanges(MatrixChangeHandler)

    _LOGGER.info("Success.")


if __name__ == "__main__":
    asyncio.run(main())