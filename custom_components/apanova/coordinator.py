"""
Coordinator pentru integrarea Apanova România.
"""

from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER, DEFAULT_UPDATE_INTERVAL
from .api import ApanovaApi


class ApanovaCoordinator(DataUpdateCoordinator):
    # Coordinator care gestionează actualizarea periodică a datelor

    def __init__(self, hass: HomeAssistant, city, email, password, cod_client, update_interval_min):
        # Înițializăm coordinatorul cu datele de conexiune și interval
        self._hass = hass
        self._city = city
        self._email = email
        self._password = password
        self._cod_client = cod_client
        self._api = None

        # Intervalul de actualizare
        interval = update_interval_min if update_interval_min else DEFAULT_UPDATE_INTERVAL

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval)
        )

    async def _async_update_data(self):
        # Funcția apelată la fiecare refresh
        if not self._api:
            LOGGER.debug("Creăm instanța ApanovaApi.")
            # Cream ApanovaApi cu base_url în funcție de city
            from .const import BASE_URLS
            base_url = BASE_URLS.get(self._city)
            self._api = ApanovaApi(
                base_url=base_url,
                email=self._email,
                password=self._password,
                cod_client=self._cod_client,
            )

        # Preluăm facturile
        LOGGER.debug("Începem actualizarea datelor facturilor Apanova.")
        invoices_data = await self._api.login_and_fetch_invoices()

        # Preluăm informații despre apă
        LOGGER.debug("Începem actualizarea datelor despre calitatea apei Apanova.")
        water_info = await self._api.fetch_water_info()

        # Combinăm datele
        combined_data = {
            "cod_client": self._cod_client,
            "invoices": invoices_data,  # {"invoices": [...], "cod_client": ...}
            "water_info": water_info,
        }
        return combined_data
