from abc import ABC


class MetadataReaderInterface(ABC):
    """
    Interface for reading metadata from different file types into pandas dataframes
    """

    def __init__(self):
        pass

    def read(self, file_path: str, file_name: str):
        """
        Function for reading data from a specific file type and returning a
        pandas dataframe of the data.
        """
        raise NotImplementedError
