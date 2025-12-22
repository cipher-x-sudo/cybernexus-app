"""Visual similarity analysis service.

This module provides image comparison and similarity analysis using PIL and scikit-image.
Does not use custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import base64
from io import BytesIO

try:
    from PIL import Image
    from PIL import ImageStat
    import imagehash
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    Image = None
    imagehash = None

try:
    import numpy as np
    from skimage.metrics import structural_similarity as ssim
    HAS_SSIM = True
except (ImportError, ValueError):
    HAS_SSIM = False
    ssim = None
    np = None

from loguru import logger


class VisualSimilarityService:
    def __init__(self):
        if not HAS_DEPS:
            logger.warning("[VisualSimilarity] Missing dependencies (PIL, imagehash, scikit-image). Some features will be disabled.")
        self._known_screenshots: Dict[str, bytes] = {}
    
    def add_reference_image(self, identifier: str, image_data: bytes):
        """Add a reference image for comparison.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            identifier: Unique identifier for the reference image
            image_data: Raw image bytes
        """
        self._known_screenshots[identifier] = image_data
    
    def calculate_perceptual_hash(self, image_data: bytes) -> Optional[str]:
        """Calculate perceptual hash for an image.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            image_data: Raw image bytes
        
        Returns:
            Perceptual hash string if successful, None if dependencies are missing or on error
        """
        if not HAS_DEPS:
            return None
        
        try:
            image = Image.open(BytesIO(image_data))
            phash = imagehash.average_hash(image)
            return str(phash)
        except Exception as e:
            logger.error(f"[VisualSimilarity] Error calculating perceptual hash: {e}")
            return None
    
    def calculate_ssim(
        self,
        image1_data: bytes,
        image2_data: bytes
    ) -> Optional[float]:
        """Calculate Structural Similarity Index (SSIM) between two images.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            image1_data: Raw bytes of the first image
            image2_data: Raw bytes of the second image
        
        Returns:
            SSIM score between 0 and 1 if successful, None if dependencies are missing or on error
        """
        if not HAS_DEPS or not HAS_SSIM:
            return None
        
        try:
            if not np:
                return None
                
            img1 = Image.open(BytesIO(image1_data))
            img2 = Image.open(BytesIO(image2_data))
            
            img1 = img1.convert('L').resize((256, 256))
            img2 = img2.convert('L').resize((256, 256))
            
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            similarity = ssim(arr1, arr2, data_range=255)
            return float(similarity)
        except Exception as e:
            logger.error(f"[VisualSimilarity] Error calculating SSIM: {e}")
            return None
    
    def compare_images(
        self,
        image1_data: bytes,
        image2_data: bytes
    ) -> Dict[str, Any]:
        """Compare two images using perceptual hash and SSIM.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            image1_data: Raw bytes of the first image
            image2_data: Raw bytes of the second image
        
        Returns:
            Dictionary containing similarity scores and comparison results
        """
        result = {
            'perceptual_hash_similarity': None,
            'ssim_score': None,
            'overall_similarity': 0.0,
            'is_similar': False
        }
        
        if not HAS_DEPS:
            return result
        
        try:
            hash1 = self.calculate_perceptual_hash(image1_data)
            hash2 = self.calculate_perceptual_hash(image2_data)
            
            if hash1 and hash2:
                hamming_distance = imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)
                perceptual_similarity = max(0, 100 - (hamming_distance / 64.0 * 100))
                result['perceptual_hash_similarity'] = perceptual_similarity
            
            ssim_score = self.calculate_ssim(image1_data, image2_data)
            if ssim_score is not None:
                result['ssim_score'] = ssim_score
                ssim_similarity = ssim_score * 100
            else:
                ssim_similarity = 0
            
            if result['perceptual_hash_similarity'] is not None:
                if ssim_score is not None:
                    overall = (result['perceptual_hash_similarity'] * 0.4 + ssim_similarity * 0.6)
                else:
                    overall = result['perceptual_hash_similarity']
            else:
                overall = ssim_similarity if ssim_score is not None else 0
            
            result['overall_similarity'] = round(overall, 2)
            result['is_similar'] = result['overall_similarity'] > 70.0
            
        except Exception as e:
            logger.error(f"[VisualSimilarity] Error comparing images: {e}")
        
        return result
    
    def compare_against_references(
        self,
        image_data: bytes,
        threshold: float = 70.0
    ) -> List[Dict[str, Any]]:
        """Compare an image against all reference images.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            image_data: Raw bytes of the image to compare
            threshold: Minimum similarity score to consider a match (default: 70.0)
        
        Returns:
            List of match dictionaries sorted by similarity (highest first)
        """
        matches = []
        
        for identifier, ref_image_data in self._known_screenshots.items():
            comparison = self.compare_images(image_data, ref_image_data)
            
            if comparison['overall_similarity'] >= threshold:
                matches.append({
                    'identifier': identifier,
                    'similarity': comparison['overall_similarity'],
                    'perceptual_hash_similarity': comparison['perceptual_hash_similarity'],
                    'ssim_score': comparison['ssim_score']
                })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def decode_base64_image(self, base64_string: str) -> Optional[bytes]:
        """Decode a base64-encoded image string to bytes.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            base64_string: Base64-encoded image string (may include data URI prefix)
        
        Returns:
            Decoded image bytes if successful, None on error
        """
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            return base64.b64decode(base64_string)
        except Exception as e:
            logger.error(f"[VisualSimilarity] Error decoding base64 image: {e}")
            return None


_visual_similarity_service: Optional[VisualSimilarityService] = None


def get_visual_similarity_service() -> VisualSimilarityService:
    global _visual_similarity_service
    if _visual_similarity_service is None:
        _visual_similarity_service = VisualSimilarityService()
    return _visual_similarity_service

