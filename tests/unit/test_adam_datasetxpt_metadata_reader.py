"""
This module contains unit tests for Adam DatasetMetadataReader class.
"""
import os

from cdisc_rules_engine.services.data_readers.datasetxpt_metadata_reader import (
    DatasetXPTMetadataReader,
)


def test_read_metadata():
    """
    Unit test for function read.
    Loads test .xpt file and extracts metadata.
    """
    test_dataset_path: str = (
        f"{os.path.dirname(__file__)}/../resources/test_adam_dataset.xpt"
    )
    reader = DatasetXPTMetadataReader()
    metadata: dict = reader.read(
        file_path=test_dataset_path, file_name="test_adam_dataset.xpt"
    )
    assert metadata["adam_info"] == {
        "categorization_scheme": {"CRIT1": 1},
        "w_indexes": {"R2BASE": 2},
        "period": {},
        "selection_algorithm": {},
    }
