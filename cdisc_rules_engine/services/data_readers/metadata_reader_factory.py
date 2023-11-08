from typing import Type

from cdisc_rules_engine.interfaces.metadata_reader_interface import (
    MetadataReaderInterface,
)
from cdisc_rules_engine.interfaces.factory_interface import FactoryInterface

from cdisc_rules_engine.services.data_readers.datasetxpt_metadata_reader import (
    DatasetXPTMetadataReader,
)
from cdisc_rules_engine.services.data_readers.datasetjson_metadata_reader import (
    DatasetJSONMetadataReader,
)


class MetadataReaderFactory(FactoryInterface):
    _metadata_reader_map = {
        "XPT": DatasetXPTMetadataReader,
        "JSON": DatasetJSONMetadataReader,
    }

    def __init__(self, service_name: str = None):
        self._default_service_name = service_name

    @classmethod
    def register_service(cls, name: str, service: Type[MetadataReaderInterface]):
        """
        Registers a new service in internal _service_map
        """
        if not name:
            raise ValueError("Service name must not be empty!")
        if not issubclass(service, MetadataReaderInterface):
            raise TypeError("Implementation of DataReaderInterface required!")
        cls._metadata_reader_map[name] = service

    def get_service(self, name: str = None, **kwargs) -> MetadataReaderInterface:
        """
        Get instance of service that matches searched implementation
        """
        service_name = name or self._default_service_name
        if service_name in self._metadata_reader_map:
            return self._metadata_reader_map[service_name]()
        raise ValueError(
            f"Service name must be in {list(self._metadata_reader_map.keys())}, "
            f"given service name is {service_name}"
        )
