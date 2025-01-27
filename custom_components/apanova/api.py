"""
API Manager pentru integrarea Apanova România.
"""
import json
from bs4 import BeautifulSoup
import aiohttp

from .const import LOGGER


class ApanovaApi:
    # Clasa care gestionează conexiunea la API și acțiunile de login, fetch facturi, etc.

    def __init__(self, base_url, email, password, cod_client):
        self._base_url = base_url
        self._email = email
        self._password = password
        self._cod_client = cod_client

    async def login_and_fetch_invoices(self):
        # Funcție principală pentru login și obținere facturi
        async with aiohttp.ClientSession() as session:
            headers = {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }

            # Obține tokenul CSRF
            csrf_token = await self._fetch_csrf_token(session, headers)
            # Login
            await self._login(session, headers, csrf_token)
            # Preia facturile
            invoices = await self._fetch_invoices(session, headers)
            return invoices

    async def fetch_water_info(self):
        # Preia informațiile legate de calitatea apei
        url = f"{self._base_url}/water/info"
        LOGGER.debug(f"Se încearcă preluarea datelor de apă de la: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    text_data = await response.text()
                    LOGGER.debug(f"Răspuns brut pentru water info: {text_data}")
                    data_json = json.loads(text_data)
                    return data_json
        except Exception as err:
            LOGGER.error(f"Eroare la preluarea info apă: {err}")
            return []

    async def _fetch_csrf_token(self, session, headers):
        # Preia tokenul CSRF de pe pagina de login
        login_url = f"{self._base_url}/login"
        async with session.get(login_url, headers=headers) as response:
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")
            csrf_input = soup.find("input", {"name": "csrf_anb_token"})
            if not csrf_input:
                LOGGER.error("Nu s-a găsit csrf_anb_token în pagina de login!")
                raise Exception("Nu s-a putut obține tokenul CSRF.")

            csrf_token = csrf_input["value"]
            # Trunchiem tokenul dacă este mai lung de 32 caractere
            return csrf_token[:32]

    async def _login(self, session, headers, csrf_token):
        # Efectuează login pe site
        login_url = f"{self._base_url}/cont-nou/login"
        login_data = {
            "email": self._email,
            "parola": self._password,
            "csrf_anb_token": csrf_token,
        }
        async with session.post(login_url, headers=headers, data=login_data) as response:
            if response.status != 200:
                raise Exception("Login a eșuat. Verificați datele.")

    async def _fetch_invoices(self, session, headers):
        # Preia facturile
        invoices_url = f"{self._base_url}/user/getInvoices"
        data = {"cod": self._cod_client}

        async with session.post(invoices_url, headers=headers, data=data) as response:
            content_type = response.headers.get("Content-Type", "")
            raw_response = await response.text()
            if "html" in content_type.lower() and not raw_response.strip().startswith("["):
                # Uneori răspunsul poate fi HTML în loc de JSON
                LOGGER.warning("Răspuns HTML în loc de JSON. Returnăm structura goală.")
                return {"invoices": [], "cod_client": self._cod_client}

            try:
                invoices_list = json.loads(raw_response)
                if isinstance(invoices_list, list):
                    return {"invoices": invoices_list, "cod_client": self._cod_client}
                return {"invoices": [], "cod_client": self._cod_client}
            except Exception:
                LOGGER.error("Eroare la parsarea JSON pentru facturi. Returnăm structura goală.")
                return {"invoices": [], "cod_client": self._cod_client}
