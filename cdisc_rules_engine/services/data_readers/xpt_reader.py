from io import BytesIO


import pyreadstat
import datetime
import sys

import pandas as pd
import dask.dataframe as dd

from cdisc_rules_engine.interfaces import (
    DataReaderInterface,
)


class XPTReader(DataReaderInterface):
    def read(self, data):
        df = pd.read_sas(BytesIO(data), format="xport", encoding="utf-8")
        df = self._format_floats(df)
        return df

    """
    def from_file(self, file_path):
        df = pd.read_sas(file_path, format="xport", encoding="utf-8")
        df = self._format_floats(df)
        return df
    """

    def from_file(self, file_path):

        print(datetime.datetime.now())

        print(file_path)

        # df, _ = pyreadstat.pyreadstat.read_file_multiprocessing(pyreadstat.read_xport,
        # file_path, num_processes=4, num_rows=3488000)
        df = dd.from_pandas(pyreadstat.read_xport(file_path)[0])
        print(df.head())

        df = self._format_floats(df)

        print(datetime.datetime.now())
        sys.exit(0)

        return df

    def _format_floats(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe.applymap(lambda x: round(x, 15) if isinstance(x, float) else x)
