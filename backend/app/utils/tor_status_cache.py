

import threading
import time
from typing import Dict, Any, Optional
from loguru import logger

from app.utils.tor_check import check_tor_connectivity


class TorStatusCache:
    
    
    def __init__(self):
        
        self._lock = threading.RLock()
        self._status: Dict[str, Any] = {
            "status": "disconnected",
            "is_tor": False,
            "ip": None,
            "response_time_ms": None,
            "error": None,
            "host": "unknown",
            "port": 9050,
            "last_updated": None,
            "last_check_attempt": None,
        }
        self._is_checking = False
        self._check_lock = threading.Lock()
    
    def get_status(self) -> Dict[str, Any]:
        
        with self._lock:

            return self._status.copy()
    
    def update_status(self, status: Dict[str, Any]) -> None:
        
        with self._lock:
            self._status.update(status)
            self._status["last_updated"] = time.time()
            logger.debug(f"Tor status cache updated: {status.get('status')}")
    
    def update_status_async(self) -> None:
        

        if not self._check_lock.acquire(blocking=False):
            logger.debug("Tor status check already in progress, skipping")
            return
        
        try:
            self._is_checking = True
            self._status["last_check_attempt"] = time.time()
            
            logger.debug("Starting background Tor connectivity check")
            status = check_tor_connectivity()
            self.update_status(status)
            
        except Exception as e:
            logger.error(f"Error updating Tor status cache: {e}", exc_info=True)

            with self._lock:
                self._status["status"] = "error"
                self._status["error"] = f"Check failed: {str(e)}"
                self._status["last_updated"] = time.time()
        finally:
            self._is_checking = False
            self._check_lock.release()
    
    def is_stale(self, max_age_seconds: int = 60) -> bool:
        
        with self._lock:
            if self._status["last_updated"] is None:
                return True
            age = time.time() - self._status["last_updated"]
            return age > max_age_seconds
    
    def is_checking(self) -> bool:
        
        return self._is_checking



_tor_status_cache: Optional[TorStatusCache] = None
_cache_lock = threading.Lock()


def get_tor_status_cache() -> TorStatusCache:
    
    global _tor_status_cache
    if _tor_status_cache is None:
        with _cache_lock:
            if _tor_status_cache is None:
                _tor_status_cache = TorStatusCache()
                logger.info("Tor status cache initialized")
    return _tor_status_cache




