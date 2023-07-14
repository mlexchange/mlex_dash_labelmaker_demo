
class Dataset:
    def __init__(self, uri, type='local', tags=[]):
        '''
        Base class for data set schema definition
        Args:
            uri:        URI of the data set
            data_type:   local or tiled
            tags:       List of tags assigned to the data set
        '''
        self.uri = uri
        self.type = type
        self.tags = tags
        pass