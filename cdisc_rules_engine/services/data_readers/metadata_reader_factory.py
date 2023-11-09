from typing import Type

from cdisc_rules_engine.interfaces.metadata_reader_interface import (
    MetadataReaderInterface,
)
from cdisc_rules_engine.interfaces.factory_interface import FactoryInterface
from cdisc_rules_engine.enums.dataformat_types import DataFormatTypes


class MetadataReaderFactory(FactoryInterface):
    def __init__(self, service_name: str = None):
        self._default_service_name = service_name

    @classmethod
    def register_service(cls, name: str, service: Type[MetadataReaderInterface]):
        """
        Registers a new service in the DataFormatTypes enum.
        """
        if not name:
            raise ValueError("Service name must not be empty!")
        if not issubclass(service, MetadataReaderInterface):
            raise TypeError("Implementation of MetadataReaderInterface required!")
        for format_type in DataFormatTypes:
            if format_type.name == name:
                format_type.value[1] = service
                return
        raise ValueError(f"Service name '{name}' is not in DataFormatTypes")

    def get_service(self, name: str = None, **kwargs) -> MetadataReaderInterface:
        """
        Get an instance of the service that matches the searched implementation.
        """
        service_name = name or self._default_service_name
        for format_type in DataFormatTypes:
            if format_type.name == service_name:
                return format_type.value[1]()

        raise ValueError(
            f"Service name must be in {[f.name for f in DataFormatTypes]},"
            f"given service name is {service_name}"
        )
