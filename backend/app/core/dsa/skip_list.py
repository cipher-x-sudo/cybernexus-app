import random
from typing import Any, Optional, List, Tuple, Generator
from dataclasses import dataclass, field


@dataclass
class SkipListNode:
    key: Any
    value: Any
    forward: List[Optional["SkipListNode"]] = field(default_factory=list)
    
    def __init__(self, key: Any, value: Any, level: int):
        self.key = key
        self.value = value
        self.forward = [None] * (level + 1)


class SkipList:
    
    MAX_LEVEL = 32
    P = 0.5
    
    def __init__(self):
        self._header = SkipListNode(None, None, self.MAX_LEVEL)
        self._level = 0
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: Any) -> bool:
        return self.search(key) is not None
    
    def __iter__(self) -> Generator[Tuple[Any, Any], None, None]:
        node = self._header.forward[0]
        while node:
            yield (node.key, node.value)
            node = node.forward[0]
    
    def _random_level(self) -> int:
        level = 0
        while random.random() < self.P and level < self.MAX_LEVEL:
            level += 1
        return level
    
    def _compare(self, a: Any, b: Any) -> int:
        if a < b:
            return -1
        elif a > b:
            return 1
        return 0
    
    def insert(self, key: Any, value: Any = None) -> bool:
        if value is None:
            value = key
        
        update = [None] * (self.MAX_LEVEL + 1)
        current = self._header
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, key) < 0):
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            current.value = value
            return False
        
        new_level = self._random_level()
        
        if new_level > self._level:
            for i in range(self._level + 1, new_level + 1):
                update[i] = self._header
            self._level = new_level
        
        new_node = SkipListNode(key, value, new_level)
        
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        
        self._size += 1
        return True
    
    def search(self, key: Any) -> Optional[Any]:
        current = self._header
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, key) < 0):
                current = current.forward[i]
        
        current = current.forward[0]
        
        if current and current.key == key:
            return current.value
        return None
    
    def delete(self, key: Any) -> bool:
        update = [None] * (self.MAX_LEVEL + 1)
        current = self._header
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, key) < 0):
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            for i in range(self._level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            
            while self._level > 0 and not self._header.forward[self._level]:
                self._level -= 1
            
            self._size -= 1
            return True
        
        return False
    
    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        results = []
        current = self._header
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, low) < 0):
                current = current.forward[i]
        
        current = current.forward[0]
        
        while current and self._compare(current.key, high) <= 0:
            results.append((current.key, current.value))
            current = current.forward[0]
        
        return results
    
    def floor(self, key: Any) -> Optional[Tuple[Any, Any]]:
        current = self._header
        result = None
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, key) <= 0):
                current = current.forward[i]
                result = (current.key, current.value)
        
        return result
    
    def ceiling(self, key: Any) -> Optional[Tuple[Any, Any]]:
        current = self._header
        
        for i in range(self._level, -1, -1):
            while (current.forward[i] and 
                   self._compare(current.forward[i].key, key) < 0):
                current = current.forward[i]
        
        current = current.forward[0]
        
        if current:
            return (current.key, current.value)
        return None
    
    def minimum(self) -> Optional[Tuple[Any, Any]]:
        if self._header.forward[0]:
            node = self._header.forward[0]
            return (node.key, node.value)
        return None
    
    def maximum(self) -> Optional[Tuple[Any, Any]]:
        current = self._header
        
        for i in range(self._level, -1, -1):
            while current.forward[i]:
                current = current.forward[i]
        
        if current != self._header:
            return (current.key, current.value)
        return None
    
    def clear(self):
        self._header = SkipListNode(None, None, self.MAX_LEVEL)
        self._level = 0
        self._size = 0
    
    def to_list(self) -> List[Tuple[Any, Any]]:
        return list(self)
    
    @classmethod
    def from_list(cls, items: List[Tuple[Any, Any]]) -> "SkipList":
        skip_list = cls()
        for key, value in items:
            skip_list.insert(key, value)
        return skip_list
    
    def stats(self) -> dict:
        level_counts = [0] * (self._level + 1)
        
        node = self._header.forward[0]
        while node:
            for i in range(len(node.forward)):
                if node.forward[i]:
                    level_counts[i] += 1
            node = node.forward[0]
        
        return {
            "size": self._size,
            "max_level": self._level,
            "level_distribution": level_counts
        }


