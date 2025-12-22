"""Serialization utilities for DSA structures.

This module provides serialization and deserialization utilities for custom
DSA structures, supporting both JSON and pickle formats with optional compression.

This module does not use custom DSA concepts from app.core.dsa, but provides
serialization support for DSA structures.
"""

import json
import pickle
import gzip
from pathlib import Path
from typing import Any, Type, Union
from datetime import datetime


class Serializer:
    @staticmethod
    def to_json(obj: Any, pretty: bool = False) -> str:
        """Serialize an object to JSON string.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            obj: The object to serialize
            pretty: Whether to format JSON with indentation (default: False)
        
        Returns:
            JSON string representation of the object
        
        Raises:
            TypeError: If object contains non-serializable types
        """
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
        """Deserialize a JSON string to a Python object.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            json_str: The JSON string to deserialize
        
        Returns:
            Python object deserialized from JSON
        """
        return json.loads(json_str)
    
    @staticmethod
    def save_json(obj: Any, path: Union[str, Path], compress: bool = False):
        """Save an object as JSON to a file.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            obj: The object to serialize and save
            path: File path where JSON will be saved
            compress: Whether to compress the file with gzip (default: False)
        """
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
        """Load a JSON file and deserialize it to a Python object.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            path: File path to the JSON file (supports .json and .json.gz)
        
        Returns:
            Python object deserialized from JSON
        """
        path = Path(path)
        
        if path.suffix == '.gz':
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    @staticmethod
    def to_pickle(obj: Any) -> bytes:
        """Serialize an object to pickle bytes.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            obj: The object to serialize
        
        Returns:
            Pickle bytes representation of the object
        """
        return pickle.dumps(obj)
    
    @staticmethod
    def from_pickle(data: bytes) -> Any:
        """Deserialize pickle bytes to a Python object.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            data: The pickle bytes to deserialize
        
        Returns:
            Python object deserialized from pickle
        """
        return pickle.loads(data)
    
    @staticmethod
    def save_pickle(obj: Any, path: Union[str, Path], compress: bool = False):
        """Save an object as pickle to a file.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            obj: The object to serialize and save
            path: File path where pickle will be saved
            compress: Whether to compress the file with gzip (default: False)
        """
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
        """Load a pickle file and deserialize it to a Python object.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            path: File path to the pickle file (supports .pkl and .pkl.gz)
        
        Returns:
            Python object deserialized from pickle
        """
        path = Path(path)
        
        if path.suffix == '.gz':
            with gzip.open(path, 'rb') as f:
                return pickle.load(f)
        else:
            with open(path, 'rb') as f:
                return pickle.load(f)
    
    @staticmethod
    def serialize_dsa(structure: Any, format: str = 'json') -> Union[str, bytes]:
        """Serialize a DSA structure to JSON or pickle format.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            structure: The DSA structure to serialize (must have to_dict() or to_list() method)
            format: Serialization format, either 'json' or 'pickle' (default: 'json')
        
        Returns:
            JSON string if format is 'json', pickle bytes if format is 'pickle'
        """
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
        """Deserialize data to a DSA structure.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            data: JSON string or pickle bytes to deserialize
            dsa_class: The DSA class to deserialize into (must have from_dict() or from_list() method)
            format: Deserialization format, either 'json' or 'pickle' (default: 'json')
        
        Returns:
            Instance of dsa_class deserialized from data
        """
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


