import hashlib


def calculate_md5(data):
    m = hashlib.md5()
    m.update(data.encode())
    return m.hexdigest()
