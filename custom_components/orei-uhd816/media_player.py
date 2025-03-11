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


from .pyOreiMatrix import OreiMatrixAPI, MatrixOutput
from .const import DOMAIN, MANUFACTURER

LOGGER = logging.getLogger(__package__)

VIDEO_MODES = ["AUTO", "BYPASS", "4K->2K", "2K->4K", "HDBT C Mode"]
AUDIO_DELAYS = ["0ms","90ms","180ms","270ms","360ms","450ms","540ms","630ms"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Add media_players for passed config_entry in HA."""
    LOGGER.debug("Adding media_player entities.")

    client: OreiMatrixAPI = hass.data[DOMAIN][entry.entry_id]

    new_devices = []

    for output in await client.Outputs:
        # we skip video outputs without a name or those whose name starts with a dot (.)
        LOGGER.debug(f"Found output[{output.Id}] Name={output.Name} Visible={output.IsVisible}.")
        if output.IsVisible:
            new_devices.append( HassMatrixOutput(hass, entry, client, output) )

    if new_devices:
        async_add_entities(new_devices)


class HassMatrixOutput(MediaPlayerEntity):
    """Our Media Player"""

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

        self.update_ha()

    def update_ha(self):
        try:
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
                | MediaPlayerEntityFeature.VOLUME_SET

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self._controller.GetInput( self._output.InputId ).Name

    @property
    def source_list(self):
        # List of available input sources.
        # TODO
        return self._controller.GetInputNames()

'''
    async def async_select_source(self, source):
        # Select input source.
        index = self._controller.video_inputs.index(source)+1
        await self._controller.async_send(f"SET OUT{self._index} {self._output_type}S IN{index}")

    async def async_turn_on(self):
        # Turn the media player on.
        await self._controller.async_send(f"SET OUT{self._index} STREAM ON")

        # Reset our input signal please
        if self._sourceIndex != -1:
            await self._controller.async_send(f"A00 SET IN{self._sourceIndex} RST")

    async def async_turn_off(self):
        await self._controller.async_send(f"SET OUT{self._index} STREAM OFF")

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        self._attr_app_name = output.

        if self._isOn:
            self._extra_attributes['input_index']=self._sourceIndex+1
            self._extra_attributes['input_has_signal']= (self._controller._inputSignals[self._sourceIndex]==1)
        else:
            self._extra_attributes['input_index']=0
            self._extra_attributes['input_has_signal']= False

        # Useful for making sensors
        return self._extra_attributes'

    async def async_mute_volume(self, mute: bool) -> None:
        """Engage AVR mute."""
        LOGGER.error(f"MUTE ME {mute}")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set AVR volume (0 to 1)."""
        LOGGER.error(f"VOLUME ME {volume}")

'''
