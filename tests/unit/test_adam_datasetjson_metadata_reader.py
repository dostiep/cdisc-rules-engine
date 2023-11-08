"""
This module contains unit tests for Adam DatasetJSONMetadataReader class.
"""
import os

from cdisc_rules_engine.services.data_readers.datasetjson_metadata_reader import (
    DatasetJSONMetadataReader,
)


def test_read_metadata():
    """
    Unit test for function read.
    Loads test .json file and extracts metadata.
    """
    test_dataset_path: str = (
        f"{os.path.dirname(__file__)}/../resources/test_adam_dataset.json"
    )

    reader = DatasetJSONMetadataReader()
    metadata: dict = reader.read(
        file_path=test_dataset_path, file_name="test_adam_dataset.json"
    )
    assert metadata["adam_info"] == {
        "categorization_scheme": {
            "AGEGR1": 1,
            "AGEGR1N": 1,
            "PARCAT1": 1,
            "SHIFT1": 1,
            "SHIFT1N": 1,
            "CRIT1": 1,
        },
        "w_indexes": {"R2A1LO": 2, "R2A1HI": 2},
        "period": {},
        "selection_algorithm": {},
    }
