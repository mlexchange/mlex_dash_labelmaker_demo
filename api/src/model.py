from enum import Enum
from pydantic import BaseModel
from typing import Optional, List


DEFAULT_UID = "425f6781-e42b-23e2-a341-2431564214523"


class FileType(str, Enum):
    uri = "uri"
    dir = "dir"


class Location(str, Enum):
    splash = "splash"
    local = "local"
    
class OperationType(str, Enum):
    import_dataset = 'import_dataset'
    export_dataset = 'export_dataset'


class DataPath(BaseModel):
    file_path: List[str]
    file_type: FileType
    where: Location


class Dataset(BaseModel):
  uid: str = DEFAULT_UID
  user_id: Optional[str]
  operation_type: OperationType
  datapath: DataPath
  filenames: List[str]