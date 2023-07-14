import base64, io

from tiled.client import from_uri
from tiled.client.node import Node

from file_manager.dataset.dataset import Dataset


class TiledDataset(Dataset):
    def __init__(self, uri, type='tiled', tags=[]):
        super().__init__(uri, type, tags)
        pass

    def read_data(self):
        rawBytes = io.BytesIO()
        tiled_data = from_uri(self.uri)
        img = tiled_data.export(rawBytes, format='jpeg')
        rawBytes.seek(0)                    # return to the start of the file
        img = base64.b64encode(rawBytes.read())
        return f'data:image/jpeg;base64,{img.decode("utf-8")}', self.uri #.split('/')[-1]

    @staticmethod
    def browse_data(tiled_uri, browse_format, tiled_uris=[], tiled_client=None):
        if not tiled_client:
            tiled_client = from_uri(tiled_uri)
        if isinstance(tiled_client, Node):
            nodes = list(tiled_client)
            for node in nodes:
                mod_tiled_uri = TiledDataset.update_tiled_uri(tiled_uri, node)
                if browse_format != '**/' and isinstance(tiled_client[node], Node):
                    TiledDataset.browse_data(mod_tiled_uri, browse_format, tiled_uris,
                                            tiled_client=tiled_client[node])
                else:
                    tiled_uris.append(mod_tiled_uri)
        else:
            tiled_uris.append(tiled_uri)
        return tiled_uris
    
    @staticmethod
    def update_tiled_uri(tiled_uri, node):
        if '/api/v1/node/metadata' in tiled_uri:
            return f'{tiled_uri}/{node}'
        else:
            return f'{tiled_uri}/api/v1/node/metadata/{node}'
