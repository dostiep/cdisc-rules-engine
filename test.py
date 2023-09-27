# import os
import pandas as pd
import pyreadstat
import datetime

# import time
# import json
# import jsonschema

import dask.dataframe as dd


"""
file = "C:\\Users\\U062293\\OneDrive - UCB\\Documents\\GitHub\\Examples\\sdtm\\ae.xpt"

_, meta = pyreadstat.read_xport(file, metadataonly=True)
df, _ = pyreadstat.read_xport(file, usecols=["STUDYID","DOMAIN"])

def _extract_domain_name(df):
    if "DOMAIN" in df.columns:
        return df.iloc[0]["DOMAIN"]
    else:
        return None

domain =  _extract_domain_name(df)

print(domain)

_metadata_container = {
"variable_labels": meta.column_labels,
"variable_names": meta.column_names,
"variable_formats":
[value if value != 'NULL' else '' for value in meta.original_variable_types.values()],
"variable_name_to_label_map": meta.variable_value_labels,
"variable_name_to_data_type_map": meta.readstat_variable_types,
"variable_name_to_size_map": meta.variable_storage_width,
"number_of_variables": meta.number_columns,
"dataset_label": meta.file_label,
"dataset_length": df.shape[0],
"domain_name": None,
"dataset_name": meta.table_name,
"dataset_modification_date": None

}

print(_metadata_container)
"""
import multiprocessing

num_processes = multiprocessing.cpu_count()

if __name__ == "__main__":

    file = "..\\Examples\\sdtmshort\\xx.xpt"

    print(datetime.datetime.now())

    df = dd.from_pandas(pyreadstat.read_xport(file)[0], npartitions=2)

    # df, _ = pyreadstat.pyreadstat.read_file_multiprocessing(pyreadstat.read_xport,
    # file, num_processes=num_processes, num_rows=3488000)

    print(df.head())

    print(datetime.datetime.now())

    print(datetime.datetime.now())

    df = dd.from_pandas(
        pd.read_sas(file, format="xport", encoding="utf-8"), npartitions=2
    )

    print(df.head())

    print(datetime.datetime.now())
