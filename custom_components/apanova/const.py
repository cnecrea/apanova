"""Constante pentru integrarea Apanova România."""
import logging

DOMAIN = "apanova"

# Chei pentru configurare
CONF_CITY = "city"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_COD_CLIENT = "cod_client"
CONF_UPDATE_INTERVAL = "update_interval"

# Opțiuni pentru filială
CITY_BUCURESTI = "București"
CITY_PLOIESTI = "Ploiești"

# URL-urile de bază pentru cele două filiale
BASE_URLS = {
    CITY_BUCURESTI: "https://www.apanovabucuresti.ro",
    CITY_PLOIESTI: "https://www.apanova-ploiesti.ro",
}

# Numiri senzori
SENSOR_TYPES = {
    "cod_client": "Cod client",
    "status_factura": "Status factură",
    "date_emitere": "Dată emitere",
    "date_scadenta": "Dată scadență",
    "numar_factura": "Număr factură",
    "total": "Total",
    "sold": "Sold",
    "date_plata": "Dată plată",
    "sector": "Sector",
    "clor": "Clor",
    "ph": "pH",
}

# Altele
DEFAULT_UPDATE_INTERVAL = 5  # minute
DEFAULT_NAME = "Apanova"

# Logger pentru întreaga integrare
LOGGER = logging.getLogger(__package__)
