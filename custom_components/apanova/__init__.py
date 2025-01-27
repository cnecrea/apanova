"""Inițializarea integrării Apanova România."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER, CONF_CITY, CONF_EMAIL, CONF_PASSWORD, CONF_COD_CLIENT, CONF_UPDATE_INTERVAL
from .coordinator import ApanovaCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    # Configurează integrarea Apanova dintr-un config entry
    LOGGER.debug("Se inițializează Apanova România...")

    city = config_entry.data[CONF_CITY]
    email = config_entry.data[CONF_EMAIL]
    password = config_entry.data[CONF_PASSWORD]
    cod_client = config_entry.data[CONF_COD_CLIENT]
    update_interval = config_entry.options.get(CONF_UPDATE_INTERVAL)

    # Creăm coordinatorul
    coordinator = ApanovaCoordinator(
        hass,
        city,
        email,
        password,
        cod_client,
        update_interval
    )
    # Primul refresh
    await coordinator.async_config_entry_first_refresh()

    # Stocăm coordinatorul pentru acces în alte fișiere
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # Încărcăm platformele (sensor)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    # Descărcăm o config entry
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok
