class DataFetchError(Exception):
    """something error when fetch"""


class IPBlockError(Exception):
    """fetch so fast that the server block us ip"""