"""Platform for media_player integration."""
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState
    #REMOVE ATTR_TO_PROPERTY
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo


from .pyOreiMatrix import OreiMatrixAPI, MatrixOutput, MatrixInput
from .const import DOMAIN, MANUFACTURER

LOGGER = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Add media_players for passed config_entry in HA."""
    LOGGER.debug("Adding media_player entities.")

    client: OreiMatrixAPI = hass.data[DOMAIN][entry.entry_id]

    new_devices = []

    for output in await client.Outputs:
        # we skip video outputs that have the default name UNLESS they all have the default name
        LOGGER.debug(f"Found output[{output.Id}] Name={output.Name} Visible={output.IsVisible}.")
        if output.IsVisible:
            new_devices.append( HassMatrixOutput(hass, entry, client, output) )

    if new_devices:
        async_add_entities(new_devices)


class HassMatrixOutput(MediaPlayerEntity):
    """Our Media Player"""
    _output: MatrixOutput

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, controller: OreiMatrixAPI, output: MatrixOutput):
        """Initialize our Media Player"""
        self._hass = hass
        self._controller = controller
        self._output = output
        self._extra_attributes = {}

        self._name = f"{output.Name} HDMI"

        self._attr_unique_id = f"{entry.unique_id}_{output.Id:02d}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            manufacturer=MANUFACTURER,
            model=self._controller.model,
            name=entry.data[CONF_NAME],
            sw_version=self._controller.firmware,
        )

        controller.SubscribeToChanges(self.MatrixChangeHandler)

    def MatrixChangeHandler(self, changedObject):
        if (type(changedObject) is OreiMatrixAPI) or \
           (type(changedObject) is MatrixOutput and changedObject.Id==self._output.Id) or \
           (type(changedObject) is MatrixInput and changedObject.Id==self._output.InputId):
            # LOGGER.debug(f"UPDATE:{self._name} due to {changedObject}")
            self.update_ha()

    def update_ha(self):
        try:
            input: MatrixInput = self._controller.GetInput(self._output.InputId)
            self._attr_app_name = input.Name

            self.schedule_update_ha_state()
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.debug(f"State update failed. {error}")

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        if self._controller.IsConnected:
            return "mdi:video-switch"
        else:
            return "mdi:video-switch-outline"

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self._controller.power:
            return MediaPlayerState.ON
        else:
            return MediaPlayerState.OFF

    @property
    def available(self) -> bool:
        """Return if the media player is available."""
        return True

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return MediaPlayerEntityFeature.SELECT_SOURCE \
                | MediaPlayerEntityFeature.TURN_ON \
                | MediaPlayerEntityFeature.TURN_OFF \
                | MediaPlayerEntityFeature.VOLUME_MUTE \
                | MediaPlayerEntityFeature.VOLUME_SET # Silly but we need this for mute

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self._controller.GetInput( self._output.InputId ).Name

    @property
    def source_list(self):
        # List of available input sources.
        return self._controller.GetInputNames()

    @property
    def volume_level(self) -> float | None:
        self._attr_volume_level = 1.0
        return self._attr_volume_level

    @property
    def is_volume_muted(self) -> bool | None:
        # Boolean if volume is currently muted.
        self._attr_is_volume_muted = not self._output.StreamEnabled
        return self._attr_is_volume_muted

    async def async_select_source(self, source):
        # Select input source.
        names = self._controller.GetInputNames(all=True)
        index = names.index(source)+1

        self._output.CmdSelectInput(index)

    async def async_turn_on(self):
        self._controller.CmdPowerOn()

    async def async_turn_off(self):
        self._controller.CmdPowerOff()

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        input: MatrixInput = self._controller.GetInput(self._output.InputId)

        self._attr_app_name = input.Name

        if self._controller.power:
            self._extra_attributes['input_id']=input.Id
            self._extra_attributes['input_has_signal']= input.IsActive
            self._extra_attributes['output_has_link'] = self._output.HasLink
            self._extra_attributes['output_cable_type'] = self._output.Cable
        else:
            self._extra_attributes['input_id']=0
            self._extra_attributes['input_has_signal']= False
            self._extra_attributes['output_has_link'] = False
            self._extra_attributes['output_cable_type']=""

        # Useful for making sensors
        return self._extra_attributes

    async def async_mute_volume(self, mute: bool) -> None:
        """Engage AVR mute."""
        self._output.CmdSetOutputStream(not mute)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set AVR volume (0 to 1)."""
        LOGGER.debug("Volume is only here to support Mute.")
        self._attr_volume_level = 1.0
