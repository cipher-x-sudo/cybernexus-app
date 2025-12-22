import json
import pickle
import gzip
from pathlib import Path
from typing import Any, Type, Union
from datetime import datetime


class Serializer:
    @staticmethod
    def to_json(obj: Any, pretty: bool = False) -> str:
        def default_serializer(o):
            if hasattr(o, 'to_dict'):
                return o.to_dict()
            elif isinstance(o, datetime):
                return o.isoformat()
            elif isinstance(o, set):
                return list(o)
            elif isinstance(o, bytes):
                return o.decode('utf-8', errors='replace')
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        
        if pretty:
            return json.dumps(obj, default=default_serializer, indent=2, sort_keys=True)
        return json.dumps(obj, default=default_serializer)
    
    @staticmethod
    def from_json(json_str: str) -> Any:
        return json.loads(json_str)
    
    @staticmethod
    def save_json(obj: Any, path: Union[str, Path], compress: bool = False):
        path = Path(path)
        json_str = Serializer.to_json(obj, pretty=not compress)
        
        if compress:
            path = path.with_suffix('.json.gz')
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_str)
    
    @staticmethod
    def load_json(path: Union[str, Path]) -> Any:
        path = Path(path)
        
        if path.suffix == '.gz':
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    @staticmethod
    def to_pickle(obj: Any) -> bytes:
        return pickle.dumps(obj)
    
    @staticmethod
    def from_pickle(data: bytes) -> Any:
        return pickle.loads(data)
    
    @staticmethod
    def save_pickle(obj: Any, path: Union[str, Path], compress: bool = False):
        path = Path(path)
        data = pickle.dumps(obj)
        
        if compress:
            path = path.with_suffix('.pkl.gz')
            with gzip.open(path, 'wb') as f:
                f.write(data)
        else:
            with open(path, 'wb') as f:
                f.write(data)
    
    @staticmethod
    def load_pickle(path: Union[str, Path]) -> Any:
        path = Path(path)
        
        if path.suffix == '.gz':
            with gzip.open(path, 'rb') as f:
                return pickle.load(f)
        else:
            with open(path, 'rb') as f:
                return pickle.load(f)
    
    @staticmethod
    def serialize_dsa(structure: Any, format: str = 'json') -> Union[str, bytes]:
        if hasattr(structure, 'to_dict'):
            data = structure.to_dict()
        elif hasattr(structure, 'to_list'):
            data = structure.to_list()
        else:
            data = structure
        
        if format == 'json':
            return Serializer.to_json(data)
        else:
            return Serializer.to_pickle(data)
    
    @staticmethod
    def deserialize_dsa(data: Union[str, bytes], dsa_class: Type, format: str = 'json') -> Any:
        if format == 'json':
            parsed = Serializer.from_json(data) if isinstance(data, str) else data
        else:
            parsed = Serializer.from_pickle(data) if isinstance(data, bytes) else data
        
        if hasattr(dsa_class, 'from_dict'):
            return dsa_class.from_dict(parsed)
        elif hasattr(dsa_class, 'from_list'):
            return dsa_class.from_list(parsed)
        else:
            return parsed


