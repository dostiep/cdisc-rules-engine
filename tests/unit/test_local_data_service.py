import os
from unittest.mock import MagicMock

import pandas as pd
import pytest
from cdisc_rules_engine.config.config import ConfigService

from cdisc_rules_engine.services.data_services import LocalDataService
from unittest.mock import Mock, patch
from cdisc_rules_engine.models.dataset.pandas_dataset import PandasDataset


def test_read_metadata():
    """
    Unit test for read_data method.
    """
    dataset_path = f"{os.path.dirname(__file__)}/../resources/test_dataset.xpt"
    data_service = LocalDataService(MagicMock(), MagicMock(), MagicMock())
    metadata = data_service.read_metadata(dataset_path)
    assert "file_metadata" in metadata
    assert metadata["file_metadata"].get("name") == "test_dataset.xpt"
    assert metadata["file_metadata"].get("size") == 823120
    assert "contents_metadata" in metadata
    assert "variable_labels" in metadata["contents_metadata"]
    assert "variable_formats" in metadata["contents_metadata"]
    assert "variable_name_to_label_map" in metadata["contents_metadata"]
    assert "variable_name_to_size_map" in metadata["contents_metadata"]
    assert "number_of_variables" in metadata["contents_metadata"]
    assert "dataset_label" in metadata["contents_metadata"]
    assert "domain_name" in metadata["contents_metadata"]
    assert "dataset_modification_date" in metadata["contents_metadata"]


@pytest.mark.parametrize(
    "files, expected_result",
    [
        (["test_dataset.xpt", "test_defineV21-SDTM.xml"], True),
        (["nope.xpt"], False),
    ],
)
def test_has_all_files(files, expected_result):
    directory = f"{os.path.dirname(__file__)}/../resources"
    data_service = LocalDataService(MagicMock(), MagicMock(), MagicMock())
    assert data_service.has_all_files(directory, files) == expected_result


def test_get_dataset():
    dataset_path = f"{os.path.dirname(__file__)}/../resources/test_dataset.xpt"
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    data_service = LocalDataService.get_instance(
        config=ConfigService(), cache_service=mock_cache
    )
    data = data_service.get_dataset(dataset_name=dataset_path)
    assert isinstance(data, PandasDataset)


def test_get_variables_metdata():
    dataset_path = f"{os.path.dirname(__file__)}/../resources/test_adam_dataset.xpt"
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    data_service = LocalDataService.get_instance(
        config=ConfigService(), cache_service=mock_cache
    )
    data = data_service.get_variables_metadata(dataset_name=dataset_path)
    assert isinstance(data, pd.DataFrame)
    expected_keys = [
        "variable_name",
        "variable_format",
        "variable_order_number",
        "variable_data_type",
        "variable_label",
    ]
    for key in expected_keys:
        assert key in data


@pytest.mark.parametrize(
    "file_size, available_memory, expected_library",
    [
        (1, 100 * 1024 * 1024, "PandasDataset"),
        (100, 10 * 1024 * 1024, "DaskDataset"),
        (70, 100 * 1024 * 1024, "PandasDataset"),
        (70.1, 100 * 1024 * 1024, "DaskDataset"),
    ],
)
def test_choose_library(file_size, available_memory, expected_library):
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    data_service = LocalDataService.get_instance(
        config=ConfigService(), cache_service=mock_cache
    )
    mock_virtual_memory = Mock()
    mock_virtual_memory.available = available_memory
    dataset_path = f"{os.path.dirname(__file__)}/../resources/test_adam_dataset.xpt"
    data = pd.read_sas(dataset_path, format="xport", encoding="utf-8")

    with patch("psutil.virtual_memory", return_value=mock_virtual_memory):
        library = data_service.choose_library(data, file_size).__class__.__name__
        assert library == expected_library
