
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
    
    def _add_event_id(self, event_uid):
        '''
        Add tagging event to the tags in data set
        Args:
            event_uid:      Tagging event uid assigned in splash-ml
        '''
        if len(self.tags)==0:
            self.tags = [{'name': 'labelmaker', 'event_id': event_uid}]
        else:
            for cont in range(len(self.tags)):
                self.tags[cont]['event_id'] = event_uid
        pass