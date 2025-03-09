import asyncio
import aiohttp
import json
import logging
from pyOreiMatrixEnums import EDID, SystemPowerState
import queue
import time

_LOGGER = logging.getLogger(__name__)

REQ_GET_STATUS  = {"comhead":"get status","language":0}
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
    __inputId: int
    __visible: bool
    __active: bool

    def __init__(self, api, id: int, name: str, inputId: int, visible: bool, active: bool):
        self.__api = api
        self.__id = id
        self.__name = name
        self.__inputId = inputId
        self.__visible = visible
        self.__active = active

    def __str__(self):
        return f"MatrixOutput(id={self.__id} name='{self.__name}', inputId={self.__inputId}, visible={self.__visible}, active={self.__active})"

    def __repr__(self):
        return f"MatrixOutput(id={self.__id} name='{self.__name}', inputId={self.__inputId}, visible={self.__visible}, active={self.__active})"



class OreiMatrixAPI:
    __maxRetries: int
    __model: str
    __macAddress: str
    __host: str
    __tcpPort: int
    __power: SystemPowerState
    __beep: bool
    __panel_lock: bool
    __ipMode : str
    __ipAddress: str
    __subnetMask: str
    __ipGateway: str
    __firmware: str
    __connected: bool

    __inputs: list[MatrixInput]
    __outputs: list[MatrixOutput]

    __callbacks: list[callable]
    __tcpSendQueue: queue.Queue
    __tcpRecvBuffer: str
    __tcpDisconnect: bool




    def __init__(self, host: str) -> None:
        self.__maxRetries = 3
        self.__model = None
        self.__macAddress = None
        self.__host = host
        self.__tcpPort = 8000 # Updated from default to actual in Validate
        self.__power = SystemPowerState.Off
        self.__beep = False
        self.__panel_lock = False
        self.__ipMode  = ""
        self.__ipAddress = ""
        self.__subnetMask = ""
        self.__ipGateway = ""
        self.__firmware = ""
        self.__connected = False

        self.__inputs = None
        self.__outputs = None

        self.__callbacks = []
        self.__tcpSendQueue = queue.Queue()
        self.__tcpRecvBuffer = ""
        self.__tcpDisconnect = True

    @property
    def model(self) -> str:
        return self.__model

    def __set_model(self, newVal: str) -> None:
        if not self.__model == newVal:
            _LOGGER.info(f"model changing from {self.__model!r} to {newVal!r}.")
            self.__model = newVal
            self.__NotifySubscribers(self)

    @property
    def macAddress(self) -> str:
        return self.__macAddress

    def __set_macAddress(self, newVal: str) -> None:
        if not self.__macAddress == newVal:
            _LOGGER.info(f"macAddress changing from {self.__macAddress!r} to {newVal!r}.")
            self.__macAddress = newVal
            self.__NotifySubscribers(self)

    @property
    def host(self) -> str:
        return self.__host

    def __set_host(self, newVal: str) -> None:
        if not self.__host == newVal:
            _LOGGER.info(f"host changing from {self.__host!r} to {newVal!r}.")
            self.__host = newVal
            self.__NotifySubscribers(self)

    @property
    def tcpPort(self) -> int:
        return self.__tcpPort

    def __set_tcpPort(self, newVal: int) -> None:
        if not self.__tcpPort == newVal:
            _LOGGER.info(f"tcpPort changing from {self.__tcpPort!r} to {newVal!r}.")
            self.__tcpPort = newVal
            self.__NotifySubscribers(self)

    @property
    def power(self) -> bool:
        return self.__power == SystemPowerState.On

    def __set_power(self, newVal: SystemPowerState) -> None:
        if not self.__power == newVal:
            _LOGGER.info(f"Power changing from {self.__power.name} to !r{newVal.name!r}.")
            self.__power = newVal
            self.__NotifySubscribers(self)

    @property
    def beep(self) -> bool:
        return self.__beep

    def __set_beep(self, newVal: bool) -> None:
        if not self.__beep == newVal:
            _LOGGER.info(f"Beep changing from {self.__beep!r} to {newVal!r}.")
            self.__beep = newVal
            self.__NotifySubscribers(self)

    @property
    def panel_lock(self) -> bool:
        return self.__lock

    def __set_panel_lock(self, newVal: bool) -> None:
        if not self.__panel_lock == newVal:
            _LOGGER.info(f"Lock changing from {self.__panel_lock!r} to {newVal!r}.")
            self.__panel_lock = newVal
            self.__NotifySubscribers(self)

    @property
    def ipMode(self) -> str:
        return self.__ipMode

    def __set_ipMode(self, newVal: str) -> None:
        if not self.__ipMode == newVal:
            _LOGGER.info(f"ipMode changing from {self.__ipMode!r} to {newVal!r}.")
            self.__ipMode = newVal
            self.__NotifySubscribers(self)

    @property
    def ipAddress(self) -> str:
        return self.__ipAddress

    def __set_ipAddress(self, newVal: str) -> None:
        if not self.__ipAddress == newVal:
            _LOGGER.info(f"ipAddress changing from {self.__ipAddress!r} to {newVal!r}.")
            self.__ipAddress = newVal
            self.__NotifySubscribers(self)

    @property
    def subnetMask(self) -> str:
        return self.__subnetMask

    def __set_subnetMask(self, newVal: str) -> None:
        if not self.__subnetMask == newVal:
            _LOGGER.info(f"subnetMask changing from {self.__subnetMask!r} to {newVal!r}.")
            self.__subnetMask = newVal
            self.__NotifySubscribers(self)

    @property
    def ipGateway(self) -> str:
        return self.__ipGateway

    def __set_ipGateway(self, newVal: str) -> None:
        if not self.__ipGateway == newVal:
            _LOGGER.info(f"ipGateway changing from {self.__ipGateway!r} to {newVal!r}.")
            self.__ipGateway = newVal
            self.__NotifySubscribers(self)

    @property
    def firmware(self) -> str:
        return self.__firmware

    def __set_firmware(self, newVal: str) -> None:
        if not self.__firmware == newVal:
            _LOGGER.info(f"firmware changing from {self.__firmware!r} to {newVal!r}.")
            self.__firmware = newVal
            self.__NotifySubscribers(self)

    @property
    def connected(self) -> bool:
        return self.__connected

    def __set_connected(self, newVal: str) -> None:
        if not self.__connected == newVal:
            _LOGGER.info(f"connected changing from {self.__connected!r} to {newVal!r}.")
            self.__connected = newVal
            self.__NotifySubscribers(self)


    def __SetInputProperty(self, inputId: int, name: str, val) -> bool:
        _LOGGER.debug(f"Setting Input[{inputId}] {name}={val}")
        return True

    def __SetOutputProperty(self, outputId: int, name: str, val) -> bool:
        _LOGGER.debug(f"Setting Output[{outputId}] {name}={val}")
        return True

    async def Validate(self) -> bool:
        data = await self.__web_cmd(REQ_GET_STATUS)
        if data is None:
            _LOGGER.error(f"Matrix status not found at {self.host}:{self.webPort}.")
            return False

        if "macaddress" not in data:
            _LOGGER.error("Could not determine matrix MAC address.")
            return False
        else:
            self.__set_macAddress(data["macaddress"])

        if "model" in data:
            self.__set_model(data["model"])

        data = await self.__web_cmd(REQ_GET_NETWORK)
        if data is None:
            _LOGGER.error(f"Matrix not found at {self.host}:{self.webPort}.")
            return False

        if "tcpport" not in data:
            _LOGGER.warning(f"Could not determine matrix tcpPort='{self.__tcpPort}'. Continuing with default.")
        else:
            self.__set_tcpPort(data["tcpport"])

        if "model" in data:
            self.__set_model(data["model"])

        if self.__model not in SUPPORTED_MODELS:
            _LOGGER.error(f"Unsupported matrix model='{self.model}'.")
            return False

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

            inputId = data["allsource"][idx]
            visible = (allDefaultNames or not hasDefaultName)

            connected = data["allconnect"][idx]==1
            if "allhdbtconnect" in data:
                connected = connected or (data["allhdbtconnect"][idx]==1)

            rVal.append(MatrixOutput(self, idx+1, name, inputId, visible, connected ))
            idx+=1

        self.__outputs = rVal

        for output in self.__outputs:
            self.__NotifySubscribers(output)


    async def RefreshConfig(self) -> None:
        data = await self.__web_cmd(REQ_GET_SYSTEM)

        if data is None:
            return

        if "lock" in data:
            self.__set_panel_lock( data["lock"]==1)

        if "beep" in data:
            self.__set_beep( data["beep"]==1)


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
                _LOGGER.debug(f"TCP:Connecting to {self.__host}:{self.__tcpPort}")
                reader, writer = await asyncio.open_connection(self.__host, self.__tcpPort)
            except (ConnectionRefusedError, OSError) as e:
                _LOGGER.info(f"TCP:Connection failed: {e}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                await self.__Handle_tcp_connection(reader, writer)

                if not self.__tcpDisconnect:
                    _LOGGER.info(f"TCP:Connection broken: Retrying in {retry_delay} seconds...")
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
                self.__TcpProcessMessage(line)

    def __TcpProcessMessage(self, line:str) ->None:
        didSetProperty = False
        ignored = False

        splits = line.split()

        # Get the Weirdo out of the way
        # input 1 edid: 4K2K60_444,HD Audio 7.1 HDR
        if len(splits) >= 4 and splits[0] == "input" and splits[2] == "edid:":
            inputId = int(splits[1])
            didSetProperty = self.__SetInputProperty( inputId, "edid", line[14:])

        elif len(splits) == 1:
            # IP:192.168.20.19
            if splits[0].startswith("IP:"):
                didSetProperty = True
                self.__set_ipAddress( splits[0][3:])
            # Gateway:192.168.20.1
            elif splits[0].startswith("Gateway:"):
                didSetProperty = True
                self.__set_ipGateway(splits[0][8:])
            elif line == "E00":
                ignored = True

        elif len(splits) == 2:
            # power on
            if splits[0] == "power" and splits[1] == "on":
                didSetProperty = True
                self.__set_power(SystemPowerState.On)
            # power off
            elif splits[0] == "power" and splits[1] == "off":
                didSetProperty = True
                self.__set_power(SystemPowerState.Off)
            # beep off
            elif splits[0] == "beep":
                didSetProperty = True
                self.__set_beep( splits[1]=="on" )
            # Panel Lock
            elif splits[0] == "Panel":
                didSetProperty = True
                self.__set_panel_lock(splits[1]=="Lock")
            # Subnet Mask:255.255.255.0
            elif splits[0] == "Subnet":
                didSetProperty = True
                self.__set_subnetMask(splits[1][5:])
            # Safe to ignore
            #   TCP/IP port=8000
            #   Telnet port=23
            #   Mac address:6C:DF:FB:04:79:9E
            elif splits[0] in ['TCP/IP', 'Telnet', 'Mac'] and \
                (splits[1].startswith('port') or splits[1].startswith('address')):
                ignored = True
            # System Initializing...
            elif line == "System Initializing...":
                self.__set_power( SystemPowerState.Booting )
                didSetProperty = True
            # Initialization Finished!
            elif line == "Initialization Finished!":
                self.__set_power( SystemPowerState.On )
                didSetProperty = True

        elif len(splits) == 3:
            # IP Mode: DHCP
            if splits[0] == "IP" and splits[1] == "Mode:":
                didSetProperty = True
                self.__set_ipMode(splits[2])
            # FW version 1.08.16
            elif line.startswith("FW version"):
                didSetProperty = True
                self.__set_firmware(line[11:])

        elif len(splits) == 4:
            # hdmi input 1: connect
            if splits[0] == "hdmi" and splits[1] == "input" and \
               splits[3] in ['connect', 'disconnect']:
                inputId = int(splits[2][0:1])
                didSetProperty = self.__SetInputProperty( inputId, "active", splits[3]=="connect")
            # hdmi output 1: disconnect
            # cat  output 1: disconnect
            elif splits[0] in ["hdmi", "cat"] and splits[1] == "output" and \
                 splits[3] in ['connect', 'disconnect']:
                outputId = int(splits[2][0:1])
                didSetProperty = self.__SetOutputProperty( outputId, "active", splits[3]=="connect")

        elif len(splits) == 5:
            # input 4 -> output 1
            if splits[0] == "input" and splits[2] == "->" and splits[3] == "output":
                inputId = int(splits[1])
                outputId = int(splits[4])
                didSetProperty = self.__SetOutputProperty( outputId, "inputId", inputId)
            # Get the unit all status:
            elif line == "Get the unit all status:":
                ignored = True

        # Output Stuff
        if not ignored and not didSetProperty:
            _LOGGER.info(f"TCP:<--{line!r}")

    async def __Handle_tcp_connection(self, reader, writer):
        while self.__tcpSendQueue.qsize() > 0:
            self.__tcpSendQueue.get()

        self.__tcpRecvBuffer = ""

        lastReceived = time.time()
        heartbeat = 0
        self.__TcpSend("r status")

        addr = writer.get_extra_info('peername')
        _LOGGER.info(f"TCP:Connected to {addr!r}")
        self.__set_connected(True)
        try:
            while not self.__tcpDisconnect:

                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.1)

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
                    _LOGGER.warning("TCP:Missed HEARTBEAT")
                    self.__set_connected(False)
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
            self.__set_connected(False)

    async def __Disconnect_tcp(self) -> None:
        _LOGGER.debug(f"TCP:Disconnecting from {self.__host}:{self.__tcpPort}")
        while self.__tcpSendQueue.qsize() > 0:
            self.__tcpSendQueue.get()

        self.__tcpRecvBuffer = ""
        self.__tcpDisconnect = True

    def __NotifySubscribers(self, changed_object) -> None:
        for s in self.__callbacks:
            s(changed_object)

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
                                if jsonObj["power"]==1:
                                    self.__set_power(SystemPowerState.On)
                                else:
                                    self.__set_power(SystemPowerState.Off)

                            return jsonObj
                        else:
                            _LOGGER.warning(f"HTTP:Received STATUS={status} while POSTING {cmd} to {url}")

                            if i < self.__maxRetries - 1:
                                asyncio.sleep(0.5)
                            else:
                                _LOGGER.error(f"HTTP:Failed to connect to the Matrix after {self.__maxRetries} attempts")

            except Exception as e:
                _LOGGER.warning(f"HTTP:Error connecting to the Matrix: try={i} req={cmd} err={e!r}")

        return None

    def __str__(self):
        return f"api: MAC={self.macAddress} model={self.model} tcpPort:{self.tcpPort} power:{self.__power.name} lock:{self.__panel_lock} beep:{self.__beep}"

    def __repr__(self):
        return f"api: MAC={self.macAddress} model={self.model} tcpPort:{self.tcpPort} power:{self.__power.name} lock:{self.__panel_lock} beep:{self.__beep}"
