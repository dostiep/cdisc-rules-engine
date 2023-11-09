from cdisc_rules_engine.enums.base_enum import BaseEnum

from cdisc_rules_engine.services.data_readers.xpt_reader import XPTReader
from cdisc_rules_engine.services.data_readers.json_reader import DatasetJSONReader
from cdisc_rules_engine.services.data_readers.datasetxpt_metadata_reader import (
    DatasetXPTMetadataReader,
)
from cdisc_rules_engine.services.data_readers.datasetjson_metadata_reader import (
    DatasetJSONMetadataReader,
)


class DataFormatTypes(BaseEnum):
    XPT = [XPTReader, DatasetXPTMetadataReader]
    JSON = [DatasetJSONReader, DatasetJSONMetadataReader]
