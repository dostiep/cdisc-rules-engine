from io import BytesIO

import pandas as pd
import dask.dataframe as dd

from cdisc_rules_engine.interfaces import (
    DataReaderInterface,
)

from typing import Union
from cdisc_rules_engine.models.dataset.pandas_dataset import PandasDataset
from cdisc_rules_engine.models.dataset.dask_dataset import DaskDataset

# from cdisc_rules_engine.models.dataset.dataset_interface import DatasetInterface


class XPTReader(DataReaderInterface):
    def read(self, data):
        df = pd.read_sas(BytesIO(data), format="xport", encoding="utf-8")
        df = self._format_floats(df)
        return df

    def from_file(self, file_path, library) -> Union[PandasDataset, DaskDataset]:
        if library == "PandasDataset":
            df = PandasDataset(
                data=pd.read_sas(file_path, format="xport", encoding="utf-8")
            )
        elif library == "DaskDataset":
            df = DaskDataset(
                dd.from_pandas(
                    pd.read_sas(file_path, format="xport", encoding="utf-8")
                ),
                npartitions=2,
            )
        df._data = self._format_floats(df)

        return df

    def _format_floats(
        self, dataframe: Union[PandasDataset, DaskDataset]
    ) -> Union[PandasDataset, DaskDataset]:
        return dataframe._data.applymap(
            lambda x: round(x, 15) if isinstance(x, float) else x
        )
