class FileTooLargeError(Exception):
    """
    文件太大
    """
    pass

class UnsupportedFileFormatError(Exception):
    """
    不支持的图片格式
    """
    pass