"""
ConfigFlow și OptionsFlow pentru integrarea Apanova România.
"""
import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CITY,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_COD_CLIENT,
    CONF_UPDATE_INTERVAL,
    CITY_BUCURESTI,
    CITY_PLOIESTI,
    BASE_URLS,
    LOGGER,
    DEFAULT_UPDATE_INTERVAL,
)

@config_entries.HANDLERS.register(DOMAIN)
class ApanovaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Pas inițial de configurare
        errors = {}
        if user_input is not None:
            city = user_input[CONF_CITY]
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            cod_client = user_input[CONF_COD_CLIENT]
            update_interval = user_input.get(CONF_UPDATE_INTERVAL)

            # Validare minimală
            if not BASE_URLS.get(city):
                errors["base"] = "city_invalid"

            if not errors:
                # Încercăm validarea de credențiale
                valid = await self._test_credentials(city, email, password, cod_client)
                if valid:
                    return self.async_create_entry(
                        title=f"Apanova - {city.capitalize()}",
                        data={
                            CONF_CITY: city,
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                            CONF_COD_CLIENT: cod_client,
                        },
                        options={
                            CONF_UPDATE_INTERVAL: update_interval or DEFAULT_UPDATE_INTERVAL
                        },
                    )
                else:
                    errors["base"] = "connection_failed"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CITY, default=CITY_BUCURESTI): vol.In(
                    [CITY_BUCURESTI, CITY_PLOIESTI]
                ),
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_COD_CLIENT): cv.string,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def async_step_import(self, user_input=None):
        # Pentru import YAML (dacă este cazul)
        return await self.async_step_user(user_input)

    async def async_step_options(self, user_input=None):
        # Nu se folosește direct, ci se intră prin async_get_options_flow
        pass

    async def _test_credentials(self, city, email, password, cod_client) -> bool:
        # Testăm datele introduse
        import requests
        from bs4 import BeautifulSoup

        base_url = BASE_URLS.get(city)
        if not base_url:
            return False

        session = requests.Session()
        try:
            # Obținem tokenul CSRF
            login_url = f"{base_url}/login"
            response = session.get(login_url)
            if response.status_code != 200:
                LOGGER.error("Nu am reușit să accesăm pagina de login.")
                return False

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_input = soup.find("input", {"name": "csrf_anb_token"})
            if not csrf_input:
                LOGGER.error("Nu am găsit csrf_anb_token pe pagina de login.")
                return False

            csrf_token = csrf_input["value"][:32]

            # Login propriu-zis
            login_post_url = f"{base_url}/cont-nou/login"
            login_data = {
                "email": email,
                "parola": password,
                "csrf_anb_token": csrf_token,
            }
            login_response = session.post(login_post_url, data=login_data)
            if login_response.status_code != 200:
                LOGGER.error("Login a eșuat (HTTP != 200).")
                return False

            # Verificăm cod_client
            cod_client_url = f"{base_url}/user/getCoduriClient"
            cod_client_response = session.post(cod_client_url, data={"cod": cod_client})
            if cod_client_response.status_code != 200:
                LOGGER.error("Cod client invalid sau conexiune eșuată (HTTP != 200).")
                return False

            return True
        except Exception as e:
            LOGGER.error(f"Eroare la validarea credențialelor: {e}")
            return False

    def async_get_options_flow(self, config_entry):
        # Returnăm fluxul de opțiuni
        return ApanovaOptionsFlowHandler(config_entry)


class ApanovaOptionsFlowHandler(config_entries.OptionsFlow):
    # Flux de opțiuni pentru a modifica update_interval ulterior
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            if update_interval < 1:
                errors["base"] = "interval_too_low"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_UPDATE_INTERVAL: update_interval}
                )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
