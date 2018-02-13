class AbstractLookup:
    """
    Abstract (parent) class for lookup realization.
    """
    def __init__(self, data):
        self.__lookup = {}
        if isinstance(data, list):
            for record in data:
                key = self.key(record)
                self.__lookup[key] = self.val(record)

    def key(self, record):
        """
        For override.
        Should return record key to lookup with.

        :param record: Dataset to extract key.
        :return: Any object to use as key.
        """
        return None

    def val(self, record):
        """
        For override.
        Should return record data to store.

        :param record: Dataset to extract data.
        :return: Dict of data.
        """
        return {}

    def get(self, key):
        return self.__lookup[int(key)]
