"""
Definirea senzorilor pentru integrarea Apanova România.
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType

from .const import DOMAIN, LOGGER, SENSOR_TYPES
from homeassistant.core import callback


async def async_setup_entry(hass, config_entry, async_add_entities):
    # Configurăm senzorii pe baza entry-ului și a coordinatorului
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Preluăm ultima dată (pentru water_info și facturi)
    data = coordinator.data if coordinator.data else {}
    water_info = data.get("water_info", [])
    # Extragere prime valori din water_info, dacă există
    first_entry = water_info[0] if water_info else {}
    sector = first_entry.get("sector", "Necunoscut")
    clor = first_entry.get("clor", "Necunoscut")
    ph = first_entry.get("ph", "Necunoscut")

    # Definim lista de entități
    sensors = []

    # Senzori generali de facturi
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "cod_client",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "status_factura",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "date_emitere",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "date_scadenta",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "numar_factura",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "total",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "sold",
        )
    )
    sensors.append(
        ApanovaSensor(
            coordinator,
            config_entry,
            "date_plata",
        )
    )

    # Senzori apă
    sensors.append(
        ApanovaWaterSensor(
            coordinator,
            config_entry,
            "sector",
            sector
        )
    )
    sensors.append(
        ApanovaWaterSensor(
            coordinator,
            config_entry,
            "clor",
            clor
        )
    )
    sensors.append(
        ApanovaWaterSensor(
            coordinator,
            config_entry,
            "ph",
            ph
        )
    )

    async_add_entities(sensors, update_before_add=True)


class ApanovaSensor(CoordinatorEntity, SensorEntity):
    # Senzor general pentru datele facturilor Apanova

    def __init__(self, coordinator, config_entry, sensor_type):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES.get(sensor_type, sensor_type)
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}_{config_entry.entry_id}"
        self.entity_id = f"sensor.{DOMAIN}_{sensor_type}_{config_entry.data['cod_client']}"

    @property
    def icon(self):
        # Icon personalizat
        return self._get_icon(self._sensor_type)

    @property
    def state(self):
        # Returnăm starea senzorului în funcție de tip
        data = self.coordinator.data or {}
        invoices_data = data.get("invoices", {})
        invoices_list = invoices_data.get("invoices", [])

        if self._sensor_type == "cod_client":
            return data.get("cod_client")
        elif self._sensor_type == "status_factura":
            if isinstance(invoices_list, list) and invoices_list:
                return invoices_list[0].get("SapStatus", "Necunoscut")
            else:
                return "Fără facturi"
        elif self._sensor_type == "date_emitere":
            if invoices_list:
                return invoices_list[0].get("DateIn", "Necunoscut")
        elif self._sensor_type == "date_scadenta":
            if invoices_list:
                return invoices_list[0].get("DueDate", "Necunoscut")
        elif self._sensor_type == "numar_factura":
            if invoices_list:
                return invoices_list[0].get("InvoiceNumber", "Necunoscut")
        elif self._sensor_type == "total":
            if invoices_list:
                return invoices_list[0].get("Total", "Necunoscut")
        elif self._sensor_type == "sold":
            if invoices_list:
                return invoices_list[0].get("Sold", "Necunoscut")
        elif self._sensor_type == "date_plata":
            if invoices_list:
                return invoices_list[0].get("LastPayDate", "Necunoscut")

        return None

    @property
    def extra_state_attributes(self):
        # Atribute adiționale (ex. lista de facturi)
        if self._sensor_type == "status_factura":
            data = self.coordinator.data or {}
            invoices_data = data.get("invoices", {})
            return {"invoices": invoices_data.get("invoices", [])}
        return {}

    @property
    def device_info(self):
        # Informații despre "dispozitiv" (pentru grouping în UI)
        return {
            "identifiers": {(DOMAIN, self._config_entry.data.get("cod_client", "unknown_client"))},
            "name": "Apanova România",
            "manufacturer": "Integrat de cnecrea",
            "model": "Apanova România",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def unit_of_measurement(self):
        # Unitate de măsură pentru senzorii de tip numeric
        if self._sensor_type in ["total", "sold"]:
            return "Lei"
        return None

    def _get_icon(self, sensor_type):
        # Returnăm un icon diferit în funcție de tipul senzorului
        if sensor_type == "cod_client":
            return "mdi:account"
        elif sensor_type == "status_factura":
            return "mdi:file-document"
        elif sensor_type == "date_emitere":
            return "mdi:calendar-check"
        elif sensor_type == "date_scadenta":
            return "mdi:calendar-alert"
        elif sensor_type == "numar_factura":
            return "mdi:invoice"
        elif sensor_type == "total":
            return "mdi:credit-card-outline"
        elif sensor_type == "sold":
            return "mdi:cash-multiple"
        elif sensor_type == "date_plata":
            return "mdi:calendar"
        return "mdi:help"


class ApanovaWaterSensor(CoordinatorEntity, SensorEntity):
    # Senzor special pentru datele despre apă (sector, clor, ph)

    def __init__(self, coordinator, config_entry, sensor_type, value):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._value = value
        self._attr_name = SENSOR_TYPES.get(sensor_type, sensor_type)
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}_{config_entry.entry_id}"
        self.entity_id = f"sensor.{DOMAIN}_{sensor_type}_{config_entry.data['cod_client']}"

    @property
    def state(self):
        return self._value

    @property
    def icon(self):
        return self._get_icon(self._sensor_type)

    @property
    def extra_state_attributes(self):
        return {"tip_senzor": "calitate_apă"}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.data.get("cod_client", "unknown_client"))},
            "name": "Apanova România",
            "manufacturer": "Integrat de cnecrea",
            "model": "Apanova România",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def unit_of_measurement(self):
        if self._sensor_type == "clor":
            return "mg/l"
        return None

    def _get_icon(self, sensor_type):
        if sensor_type == "sector":
            return "mdi:map"
        elif sensor_type == "clor":
            return "mdi:water-percent"
        elif sensor_type == "ph":
            return "mdi:ph"
        return "mdi:help"
