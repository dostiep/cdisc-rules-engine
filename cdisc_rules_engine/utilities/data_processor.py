import asyncio
from typing import List, Optional, Set

import pandas as pd
import dask.dataframe as dd

from cdisc_rules_engine.config import config
from cdisc_rules_engine.exceptions.custom_exceptions import InvalidMatchKeyError
from cdisc_rules_engine.services.cache.cache_service_factory import CacheServiceFactory
from cdisc_rules_engine.interfaces import (
    CacheServiceInterface,
    DataServiceInterface,
)
from cdisc_rules_engine.services.data_services import (
    DataServiceFactory,
    DummyDataService,
)
from cdisc_rules_engine.utilities.utils import search_in_list_of_dicts
import os

from cdisc_rules_engine.models.dataset.dataset_interface import DatasetInterface
from cdisc_rules_engine.models.dataset.pandas_dataset import PandasDataset
from cdisc_rules_engine.models.dataset.dask_dataset import DaskDataset


class DataProcessor:
    def __init__(self, data_service=None, cache: CacheServiceInterface = None):
        self.cache = cache or CacheServiceFactory(config).get_cache_service()
        self.data_service = (
            data_service or DataServiceFactory(config, self.cache).get_data_service()
        )

    @staticmethod
    async def get_dataset_variables(study_path, dataset, data_service) -> Set:
        data = data_service.get_dataset(f"{study_path}/{dataset.get('filename')}")
        return set(data.columns)

    @staticmethod
    async def get_all_study_variables(study_path, data_service, datasets) -> Set:
        coroutines = [
            DataProcessor.get_dataset_variables(study_path, dataset, data_service)
            for dataset in datasets
        ]
        dataset_variables: List[Set] = await asyncio.gather(*coroutines)
        return set().union(*dataset_variables)

    @staticmethod
    def get_unique_record(dataframe):
        if len(dataframe.index) > 1:
            raise InvalidMatchKeyError("Match key did not return a unique record")
        return dataframe.iloc[0]

    def preprocess_relationship_dataset(
        self,
        dataset_path: str,
        # dataset: pd.DataFrame,
        dataset: DatasetInterface,
        datasets: List[dict],
    ) -> dict:
        # Get unique RDOMAINS and corresponding ID Var
        reference_data = {}
        if "RDOMAIN" in dataset.data:
            rdomains = dataset.data["RDOMAIN"].unique()
            idvar_column_values = self.get_column_values(dataset, "IDVAR").unique()
            reference_data = self.async_get_reference_data(
                dataset_path, datasets, idvar_column_values, rdomains
            )
        elif "RSUBJID" in dataset.data:
            # get USUBJID from column in DM dataset
            reference_data = self.get_column_data(
                dataset_path, datasets, ["USUBJID"], "DM"
            )
            if "USUBJID" in reference_data.get("DM", {}):
                reference_data["DM"]["RSUBJID"] = reference_data["DM"]["USUBJID"]
                del reference_data["DM"]["USUBJID"]
        return reference_data

    def get_column_values(self, dataset, column):
        if column in dataset.data:
            return dataset.data[column]
        return []

    def get_columns(self, dataset, columns):
        column_data = {}
        for column in columns:
            if column in dataset.data:
                column_data[column] = dataset.data[column].values
        return column_data

    def get_column_data(
        self, dataset_path: str, datasets: List[dict], columns: list, domain: str
    ):
        reference_data = {}
        domain_details: dict = search_in_list_of_dicts(
            datasets, lambda item: item.get("domain") == domain
        )
        if domain_details:
            data_filename = os.path.join(dataset_path, domain_details["filename"])
            new_data = self.data_service.get_dataset(dataset_name=data_filename)
            reference_data[domain] = self.get_columns(new_data, columns)
        return reference_data

    async def async_get_column_data(self, dataset_path, datasets, columns, domain):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_column_data, dataset_path, datasets, columns, domain
        )

    def async_get_reference_data(
        self, dataset_path, datasets: List[dict], columns, domains
    ):
        coroutines = [
            self.async_get_column_data(dataset_path, datasets, columns, domain)
            for domain in domains
        ]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        reference_data = {}
        data = loop.run_until_complete(asyncio.gather(*coroutines))
        for column in data:
            reference_data = {**reference_data, **column}
        return reference_data

    @staticmethod
    def filter_dataset_by_match_keys_of_other_dataset(
        # dataset: pd.DataFrame,
        dataset: DatasetInterface,
        dataset_match_keys: List[str],
        # other_dataset: pd.DataFrame,
        other_dataset: DatasetInterface,
        other_dataset_match_keys: List[str],
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        """
        Returns a DataFrame where values of match keys of
        dataset are equal to values of match keys of other dataset.
        Example:
            dataset = USUBJID  DOMAIN
                      CDISC001 AE
                      CDISC001 AE
                      CDISC009 AE
            dataset_match_keys = ["USUBJID"]
            other_dataset = USUBJID  DOMAIN
                            CDISC009 AE
            other_dataset_match_keys = ["USUBJID"]

            The result will be: USUBJID  DOMAIN
                                CDISC009 AE
        """
        dataset_w_ind = dataset.data.set_index(dataset_match_keys)
        other_dataset_w_ind = other_dataset.data.set_index(other_dataset_match_keys)
        condition = dataset_w_ind.index.isin(other_dataset_w_ind.index)
        # return dataset_w_ind.data[condition].reset_index()
        result = dataset_w_ind[condition].reset_index()
        if isinstance(dataset, DaskDataset):
            return DaskDataset(dd.from_pandas(result, npartitions=2))
        else:
            return PandasDataset(result)

    @staticmethod
    def filter_parent_dataset_by_supp_dataset(
        # parent_dataset: pd.DataFrame,
        parent_dataset: DatasetInterface,
        # supp_dataset: pd.DataFrame,
        supp_dataset: DatasetInterface,
        column_with_names: str,
        column_with_values: str,
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        """
        A wrapper function for convenient filtering of parent dataset by supp dataset.
        Does two things:
        1. Filters parent dataset by RDOMAIN column of supp dataset.
        2. Filters parent dataset by columns of supp dataset
           that describe their relation.
        """
        parent_dataset = DataProcessor.filter_parent_dataset_by_supp_dataset_rdomain(
            parent_dataset, supp_dataset
        )
        return DataProcessor.filter_dataset_by_nested_columns_of_other_dataset(
            parent_dataset, supp_dataset, column_with_names, column_with_values
        )

    @staticmethod
    def filter_parent_dataset_by_supp_dataset_rdomain(
        # parent_dataset: pd.DataFrame,
        parent_dataset: DatasetInterface,
        # supp_dataset: pd.DataFrame
        supp_dataset: DatasetInterface
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        """
        Leaves only those rows in parent dataset
        where DOMAIN is the same as RDOMAIN of supp dataset.
        """
        parent_domain_values: pd.Series = parent_dataset.data.get("DOMAIN", pd.Series())
        supp_domain_values: pd.Series = supp_dataset.data.get("RDOMAIN", pd.Series())
        if parent_domain_values.empty or supp_domain_values.empty:
            return parent_dataset

        return parent_dataset.data[parent_domain_values.isin(supp_domain_values)]

    @staticmethod
    def filter_dataset_by_nested_columns_of_other_dataset(
        # dataset: pd.DataFrame,
        dataset: DatasetInterface,
        # other_dataset: pd.DataFrame,
        other_dataset: DatasetInterface,
        column_with_names: str,
        column_with_values: str,
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        """
        other_dataset has two columns:
            1. list of column names which exist in dataset - column_with_names.
            2. list of values of the aforementioned columns - column_with_values.

        The function filters columns name of dataset by their respective column values.

        Example:
            other_dataset = IDVAR IDVARVAL
                            ECSEQ 100
                            ECSEQ 101
                            ECNUM 105
            column_with_names = "IDVAR"
            column_with_values = "IDVARVAL"

            We need to leave only those rows in dataset
            where dataset["ECSEQ"] is equal to 100 or 101
            AND dataset["ECNUM"] is equal to 105.
        """
        grouped = other_dataset.data.groupby(column_with_names, group_keys=False)

        def filter_dataset_by_group_values(group) -> pd.DataFrame:
            decimal_group_values: pd.Series = (
                group[column_with_values].astype(float).astype(str)
            )
            decimal_dataset_values: pd.Series = (
                dataset[group.name].astype(float).astype(str)
            )
            condition: pd.Series = decimal_dataset_values.isin(decimal_group_values)
            return dataset[condition]

        result = grouped.apply(lambda group: filter_dataset_by_group_values(group))
        # grouping breaks sorting, need to sort once again
        result = result.sort_values(list(grouped.groups.keys()))
        if isinstance(dataset, DaskDataset):
            return DaskDataset(dd.from_pandas(result, npartitions=2))
        else:
            return PandasDataset(result)
        # return result.data.sort_values(list(grouped.groups.keys()))

    @staticmethod
    def merge_datasets_on_relationship_columns(
        # left_dataset: pd.DataFrame,
        left_dataset: DatasetInterface,
        # right_dataset: pd.DataFrame,
        right_dataset: DatasetInterface,
        right_dataset_domain_name: str,
        column_with_names: str,
        column_with_values: str,
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        """
        Uses full join to merge given datasets on the
        columns that describe their relation.
        """
        # right dataset holds column names of left dataset.
        # all values in the column are the same
        left_ds_col_name: str = right_dataset.data[column_with_names][0]

        # convert numeric columns to one data type to avoid merging errors
        # there is no point in converting string cols since their data type is the same
        DataProcessor.cast_numeric_cols_to_same_data_type(
            right_dataset, column_with_values, left_dataset, left_ds_col_name
        )
        # return pd.merge(
        #     left=left_dataset,
        #     right=right_dataset,
        #     left_on=[left_ds_col_name],
        #     right_on=[column_with_values],
        #     how="outer",
        #     suffixes=("", f".{right_dataset_domain_name}"),
        # )
        result = pd.merge(
            left=left_dataset.data,
            right=right_dataset.data,
            left_on=[left_ds_col_name],
            right_on=[column_with_values],
            how="outer",
            suffixes=("", f".{right_dataset_domain_name}"),
        )
        if any(
            isinstance(dataset, DaskDataset)
            for dataset in [left_dataset, right_dataset]
        ):
            return DaskDataset(dd.from_pandas(result, npartitions=2))
        else:
            return PandasDataset(result)

    @staticmethod
    def merge_relationship_datasets(
        # left_dataset: pd.DataFrame,
        left_dataset: DatasetInterface,
        left_dataset_match_keys: List[str],
        # right_dataset: pd.DataFrame,
        right_dataset: DatasetInterface,
        right_dataset_match_keys: List[str],
        right_dataset_domain: dict,
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        result = DataProcessor.filter_dataset_by_match_keys_of_other_dataset(
            left_dataset,
            left_dataset_match_keys,
            right_dataset,
            right_dataset_match_keys,
        )
        result = DataProcessor.filter_parent_dataset_by_supp_dataset(
            result,
            right_dataset,
            **right_dataset_domain["relationship_columns"],
        )
        if isinstance(result, DaskDataset):
            result = DaskDataset(
                dd.from_pandas(result.data.reset_index(drop=True), npartitions=2)
            )
        else:
            result = PandasDataset(result.data.reset_index(drop=True))
        # result = result.reset_index(drop=True)
        result = DataProcessor.merge_datasets_on_relationship_columns(
            left_dataset=result,
            right_dataset=right_dataset,
            right_dataset_domain_name=right_dataset_domain.get("domain_name"),
            **right_dataset_domain["relationship_columns"],
        )
        return result

    @staticmethod
    def merge_sdtm_datasets(
        # left_dataset: pd.DataFrame,
        left_dataset: DatasetInterface,
        # right_dataset: pd.DataFrame,
        right_dataset: DatasetInterface,
        left_dataset_match_keys: List[str],
        right_dataset_match_keys: List[str],
        right_dataset_domain_name: str,
        # ) -> pd.DataFrame:
    ) -> DatasetInterface:
        result = pd.merge(
            left_dataset.data,
            right_dataset.data,
            left_on=left_dataset_match_keys,
            right_on=right_dataset_match_keys,
            suffixes=("", f".{right_dataset_domain_name}"),
        )
        # return result
        if any(
            isinstance(dataset, DaskDataset)
            for dataset in [left_dataset, right_dataset]
        ):
            return DaskDataset(dd.from_pandas(result, npartitions=2))
        else:
            return PandasDataset(result)

    @staticmethod
    def cast_numeric_cols_to_same_data_type(
        # left_dataset: pd.DataFrame,
        left_dataset: DatasetInterface,
        left_dataset_column: str,
        # right_dataset: pd.DataFrame,
        right_dataset: DatasetInterface,
        right_dataset_column: str,
    ):
        """
        Casts given columns to one data type (float)
        ONLY if they are numeric.
        Before casting, the method ensures that both of the
        columns hold numeric values and performs conversion
        only if both of them are.

        Example 1:
            left_dataset[left_dataset_column] = [1, 2, 3, 4, ]
            right_dataset[right_dataset_column] = ["1.0", "2.0", "3.0", "4.0", ]

        Example 2:
            left_dataset[left_dataset_column] = ["1", "2", "3", "4", ]
            right_dataset[right_dataset_column] = ["1.0", "2.0", "3.0", "4.0", ]

        Example 3:
            left_dataset[left_dataset_column] = ["1", "2", "3", "4", ]
            right_dataset[right_dataset_column] = [1, 2, 3, 4, ]
        """
        # check if both columns are numeric
        left_is_numeric: bool = DataProcessor.column_contains_numeric(
            left_dataset.data[left_dataset_column]
        )
        right_is_numeric: bool = DataProcessor.column_contains_numeric(
            right_dataset.data[right_dataset_column]
        )
        if left_is_numeric and right_is_numeric:
            # convert to float
            right_dataset.data[right_dataset_column] = right_dataset.data[
                right_dataset_column
            ].astype(float)
            left_dataset.data[left_dataset_column] = left_dataset.data[
                left_dataset_column
            ].astype(float)

    @staticmethod
    def column_contains_numeric(column: pd.Series) -> bool:
        if not pd.api.types.is_numeric_dtype(column):
            return column.str.replace(".", "").str.isdigit().all()
        return True

    @staticmethod
    def filter_dataset_columns_by_metadata_and_rule(
        columns: List[str],
        define_metadata: List[dict],
        library_metadata: dict,
        rule: dict,
    ) -> List[str]:
        """
        Leaves only those variables where:
            variable origin type is the same as in rule and
            variable core status is the same as in rule
        """
        targets: List[str] = []
        for column in columns:
            if DataProcessor.column_metadata_equal_to_define_and_library(
                column, define_metadata, library_metadata, rule
            ):
                targets.append(column)
        return targets

    @staticmethod
    def column_metadata_equal_to_define_and_library(
        column: str,
        define_metadata: List[dict],
        library_metadata: dict,
        rule: dict,
    ) -> bool:
        define_variable_metadata: Optional[dict] = search_in_list_of_dicts(
            define_metadata, lambda item: item.get("define_variable_name") == column
        )
        if not define_variable_metadata:
            return False
        equal_origin_type: bool = define_variable_metadata[
            "define_variable_origin_type"
        ] == rule.get("variable_origin_type")
        equal_core_status: bool = library_metadata.get(column, {}).get(
            "core"
        ) == rule.get("variable_core_status")
        return equal_core_status and equal_origin_type

    @staticmethod
    def is_dummy_data(data_service: DataServiceInterface) -> bool:
        return isinstance(data_service, DummyDataService)
