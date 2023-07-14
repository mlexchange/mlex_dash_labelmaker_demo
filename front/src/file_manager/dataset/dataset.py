class Dataset:
    def __init__(self, uri, file_type, location='local', tags=[]):
        self.uri = uri
        self.type = file_type
        self.tags = tags
        pass