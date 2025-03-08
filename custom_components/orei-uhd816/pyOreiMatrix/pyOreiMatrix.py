import asyncio
import aiohttp
import json
import logging
from pyOreiMatrixEnums import EDID
import queue
import time

_LOGGER = logging.getLogger(__name__)

REQ_GET_NETWORK = {"comhead":"get network","language":0}
REQ_GET_INPUTS  = {"comhead":"get input status","language":0}
REQ_GET_OUTPUTS = {"comhead":"get output status","language":0}
REQ_GET_SYSTEM  = {"comhead":"get system status","language":0}

SUPPORTED_MODELS = ['HDP-MXB88D70M']

class MatrixInput:
    __api = None
    __id: int
    __name: str
    __active: bool
    __visible: bool
    __edid: EDID

    def __init__(self, api, id: int, name: str, active: bool, visible: bool, edid: EDID):
        self.__api = api
        self.__id = id
        self.__name = name
        self.__active = active
        self.__visible = visible
        self.__edid = edid

    def __str__(self):
        return f"MatrixInput(id={self.__id} name='{self.__name}', active={self.__active}, visible={self.__visible}, edid={self.__edid.describe})"

    def __repr__(self):
        return f"MatrixInput(id={self.__id} name='{self.__name}', active={self.__active}, visible={self.__visible}, edid={self.__edid.describe})"


class MatrixOutput:
    __api = None
    __id: int
    __name: str
    __sourceId: int
    __visible: bool
    __connected: bool

    def __init__(self, api, id: int, name: str, sourceId: int, visible: bool, connected: bool):
        self.__api = api
        self.__id = id
        self.__name = name
        self.__sourceId = sourceId
        self.__visible = visible
        self.__connected = connected

    def __str__(self):
        return f"MatrixOutput(id={self.__id} name='{self.__name}', sourceId={self.__sourceId}, visible={self.__visible}, connected={self.__connected})"

    def __repr__(self):
        return f"MatrixOutput(id={self.__id} name='{self.__name}', sourceId={self.__sourceId}, visible={self.__visible}, connected={self.__connected})"



class OreiMatrixAPI:
    __host: str
    __tcpPort: int
    __webPort: int
    __maxRetries: int
    __inputs: list[MatrixInput]
    __outputs: list[MatrixOutput]
    __power: bool
    __beep: bool
    __panel_lock: bool
    __callbacks: list[callable]
    __tcpSendQueue: queue.Queue
    __tcpRecvBuffer: str
    __tcpDisconnect: bool

    def __init__(self, host: str, webPort: int = 80) -> None:
        self.__model = None
        self.__host = host
        self.__tcpPort = 8000 # Updated from default to actual in Validate
        self.__webPort = webPort
        self.__maxRetries = 3
        self.__inputs = None
        self.__outputs = None
        self.__power = False
        self.__beep = False
        self.__panel_lock = False
        self.__callbacks = []
        self.__tcpSendQueue = queue.Queue()
        self.__tcpRecvBuffer = ""
        self.__tcpDisconnect = True

    @property
    def model(self) -> int:
        return self.__model

    @property
    def host(self) -> int:
        return self.__host

    @property
    def tcpPort(self) -> int:
        return self.__tcpPort

    @property
    def webPort(self) -> int:
        return self.__webPort

    @property
    def power(self) -> bool:
        return self.__power

    @property
    def lock(self) -> bool:
        return self.__lock

    @property
    def beep(self) -> bool:
        return self.__beep



    async def Validate(self) -> bool:
        data = await self.__web_cmd(REQ_GET_NETWORK)
        if data is None:
            _LOGGER.error(f"Matrix not found at {self.host}:{self.webPort}.")
            return False

        if "tcpport" not in data:
            _LOGGER.warning(f"Could not determine matrix tcpPort='{self.__tcpPort}'. Continuing.")

        if "model" not in data or data["model"] not in SUPPORTED_MODELS:
            if "model" in data:
                self.__model = data["model"]

            _LOGGER.error(f"Unsupported matrix model='{self.model}'.")
            return False

        self.__tcpPort = data["tcpport"]
        self.__model = data["model"]

        return True

    async def RefreshInputs(self) -> None:
        data = await self.__web_cmd(REQ_GET_INPUTS)
        rVal = []

        if data is None or "edid" not in data or "inactive" not in data or "inname" not in data:
            return rVal

        idx = 0
        allDefaultNames = True
        while allDefaultNames and idx < len(data["inname"]):
            if not data["inname"][idx] == f"Input{idx+1}":
                allDefaultNames = False
            idx+=1

        idx= 0
        for name in data["inname"]:
            hasDefaultName =  name == f"Input{idx+1}"
            active = data["inactive"][idx]==1
            visible = (allDefaultNames or not hasDefaultName)
            edid = EDID(data["edid"][idx])

            rVal.append(MatrixInput(self, idx+1, name, active, visible, edid ))
            idx+=1

        self.__inputs = rVal

        for input in self.__inputs:
            self.__NotifySubscribers(input)

    async def RefreshOutputs(self) -> None:
        data = await self.__web_cmd(REQ_GET_OUTPUTS)
        rVal = []

        if data is None or "name" not in data or "allsource" not in data or "allconnect" not in data:
            return rVal

        idx = 0
        allDefaultNames = True
        while allDefaultNames and idx < len(data["name"]):
            if not data["name"][idx] == f"Input{idx+1}":
                allDefaultNames = False
            idx+=1

        idx= 0
        for name in data["name"]:
            hasDefaultName =  name == f"hdmioutput{idx+1}"

            sourceId = data["allsource"][idx]
            visible = (allDefaultNames or not hasDefaultName)

            connected = data["allconnect"][idx]==1
            if "allhdbtconnect" in data:
                connected = connected or (data["allhdbtconnect"][idx]==1)

            rVal.append(MatrixOutput(self, idx+1, name, sourceId, visible, connected ))
            idx+=1

        self.__outputs = rVal

        for output in self.__outputs:
            self.__NotifySubscribers(output)


    async def RefreshConfig(self) -> None:
        data = await self.__web_cmd(REQ_GET_SYSTEM)

        if data is None:
            return

        if "lock" in data:
            self.__update_panel_lock( data["lock"]==1)

        if "beep" in data:
            self.__update_beep( data["beep"]==1)


    async def RefreshAll(self) -> None:
        await asyncio.gather(self.RefreshInputs(), self.RefreshOutputs(), self.RefreshConfig())

    @property
    async def Inputs(self) -> list[MatrixInput]:
        if self.__inputs is None:
            await self.RefreshInputs()

        return self.__inputs

    @property
    async def Outputs(self) -> list[MatrixOutput]:
        if self.__outputs is None:
            await self.RefreshOutputs()

        return self.__outputs

    def SubscribeToChanges(self, callback) -> None:
        self.__callbacks.append(callback)

        if len(self.__callbacks) == 1:
            asyncio.create_task( self.__Connect_via_tcp() )

    def UnsubscribeFromChanges(self, callback) -> None:
        self.__callbacks.remove(callback)

        if len(self.__callbacks) == 0:
            asyncio.create_task( self.__Disconnect_tcp() )

    async def __Connect_via_tcp(self) -> None:
        retry_delay = 5
        self.__tcpDisconnect = False

        while not self.__tcpDisconnect:
            try:
                _LOGGER.info(f"TCP:Connecting to {self.__host}:{self.__tcpPort}")
                reader, writer = await asyncio.open_connection(self.__host, self.__tcpPort)
            except (ConnectionRefusedError, OSError) as e:
                _LOGGER.info(f"TCP:Connection failed: {e}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                await self.__Handle_tcp_connection(reader, writer)

                if not self.__tcpDisconnect:
                    _LOGGER.info(f"TCP:Reconnecting to {self.__host}:{self.__tcpPort} in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

    def __TcpSend(self, m: str) -> None:
        self.__tcpSendQueue.put(f"{m}!\r\n")

    def __TcpReceive(self, m: str)-> None:

        delim = '\r\n'
        delimLen = len(delim)

        if len(self.__tcpRecvBuffer)>0:
            m = self.__tcpRecvBuffer + m
            self.__tcpRecvBuffer = ""

        index = m.rfind(delim)

        if index < len(m)-delimLen:
            self.__tcpRecvBuffer = m[index+delimLen:]
            m = m[:index]

        lines = m.split(delim)

        for line in lines:
            if len(line) > 0:
                _LOGGER.debug(f"TCP:<--{line!r}")

    async def __Handle_tcp_connection(self, reader, writer):
        while self.__tcpSendQueue.qsize() > 0:
            self.__tcpSendQueue.get()

        self.__tcpRecvBuffer = ""

        lastReceived = time.time()
        heartbeat = 0
        self.__TcpSend("r status")

        addr = writer.get_extra_info('peername')
        _LOGGER.info(f"TCP:Connected by {addr!r}")
        try:
            while not self.__tcpDisconnect:

                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.5)

                    if not data:
                        break

                    heartbeat = 0
                    lastReceived = time.time()

                    message = data.decode()
                    self.__TcpReceive(message)

                except TimeoutError:
                    pass

                now = time.time()

                if heartbeat > 2:
                    _LOGGER.warning("Missed HEARTBEAT")
                    break
                elif now - lastReceived > 10:
                    if heartbeat == 0:
                        self.__TcpSend("r power")
                        lastReceived = now
                    heartbeat += 1

                while self.__tcpSendQueue.qsize() > 0:
                    data = self.__tcpSendQueue.get()
                    _LOGGER.debug(f"TCP:-->{data!r}")
                    writer.write( data.encode() )
                    await writer.drain()

        except Exception as e:
            _LOGGER.info(f"TCP:Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            _LOGGER.info(f"TCP:Disconnected from {addr!r}")

    async def __Disconnect_tcp(self) -> None:
        _LOGGER.info(f"TCP:Disconnecting from {self.__host}:{self.__tcpPort}")
        while self.__tcpSendQueue.qsize() > 0:
            self.__tcpSendQueue.get()

        self.__tcpRecvBuffer = ""
        self.__tcpDisconnect = True

    def __NotifySubscribers(self, changed_object) -> None:
        for s in self.__callbacks:
            s(changed_object)

    def __update_power(self, newVal: bool) -> None:
        if not self.__power == newVal:
            self.__power = newVal
            self.__NotifySubscribers(self)

    def __update_panel_lock(self, newVal: bool) -> None:
        if not self.__panel_lock == newVal:
            self.__panel_lock = newVal
            self.__NotifySubscribers(self)

    def __update_beep(self, newVal: bool) -> None:
        if not self.__beep == newVal:
            self.__beep = newVal
            self.__NotifySubscribers(self)

    async def __web_cmd(self, cmd):
        url =  f"http://{self.__host}/cgi-bin/instr"

        for i in range(self.__maxRetries):

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=cmd, headers={"Accept": "application/json"}) as response:

                        status = response.status

                        if status == 200:
                            # I know this is weird but our server responds
                            # ContentType = 'text/plain' so we can't use await response.json()
                            textVal = await response.text(encoding="utf-8")
                            jsonObj = json.loads(textVal)

                            if "power" in jsonObj:
                                self.__update_power(jsonObj["power"]==1)

                            return jsonObj

                        _LOGGER.warning(f"Received STATUS={status} while POSTING {cmd} to {url}")

                        if i < self.__maxRetries - 1:
                            asyncio.sleep(0.5)
                        else:
                            _LOGGER.error(f"Failed to connect to the Matrix after {self.__maxRetries} attempts")

            except Exception as e:
                _LOGGER.error(f"Error connecting to the Matrix: {e}")

        return None

    def __str__(self):
        return f"api: model={self.model} tcpPort:{self.tcpPort} power:{self.__power} lock:{self.__panel_lock} beep:{self.__beep}"

    def __repr__(self):
        return f"api: model={self.model} tcpPort:{self.tcpPort} power:{self.__power} lock:{self.__panel_lock} beep:{self.__beep}"
