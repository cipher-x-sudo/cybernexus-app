"""
Visual Similarity Service

Provides image comparison and similarity detection using perceptual hashing
and structural similarity metrics.
"""

import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import base64
from io import BytesIO
import numpy as np

try:
    from PIL import Image
    from PIL import ImageStat
    import imagehash
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    Image = None
    imagehash = None

# Try to import scikit-image separately to avoid breaking if it has compatibility issues
try:
    from skimage.metrics import structural_similarity as ssim
    HAS_SSIM = True
except (ImportError, ValueError):
    # ValueError can occur with numpy compatibility issues
    HAS_SSIM = False
    ssim = None

from loguru import logger


class VisualSimilarityService:
    """
    Service for comparing images and detecting visual similarity.
    
    Features:
    - Perceptual hashing for fast similarity detection
    - SSIM (Structural Similarity Index) for detailed comparison
    - Screenshot comparison against known malicious sites
    - Similarity scoring (0-100)
    """
    
    def __init__(self):
        if not HAS_DEPS:
            logger.warning("[VisualSimilarity] Missing dependencies (PIL, imagehash, scikit-image). Some features will be disabled.")
        self._known_screenshots: Dict[str, bytes] = {}
    
    def add_reference_image(self, identifier: str, image_data: bytes):
        """Add a reference image for comparison"""
        self._known_screenshots[identifier] = image_data
    
    def calculate_perceptual_hash(self, image_data: bytes) -> Optional[str]:
        """
        Calculate perceptual hash of an image.
        
        Args:
            image_data: Image bytes (PNG, JPEG, etc.)
        
        Returns:
            Perceptual hash string or None if error
        """
        if not HAS_DEPS:
            return None
        
        try:
            image = Image.open(BytesIO(image_data))
            # Use average hash for better performance
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
        """
        Calculate SSIM (Structural Similarity Index) between two images.
        
        Args:
            image1_data: First image bytes
            image2_data: Second image bytes
        
        Returns:
            SSIM score (0-1, higher is more similar) or None if error
        """
        if not HAS_DEPS or not HAS_SSIM:
            return None
        
        try:
            # Load images
            img1 = Image.open(BytesIO(image1_data))
            img2 = Image.open(BytesIO(image2_data))
            
            # Convert to grayscale and resize to same size
            img1 = img1.convert('L').resize((256, 256))
            img2 = img2.convert('L').resize((256, 256))
            
            # Convert to numpy arrays
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Calculate SSIM
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
        """
        Compare two images using multiple methods.
        
        Args:
            image1_data: First image bytes
            image2_data: Second image bytes
        
        Returns:
            Dictionary with comparison results:
                - perceptual_hash_similarity: Hamming distance between hashes
                - ssim_score: SSIM similarity score (0-1)
                - overall_similarity: Combined similarity score (0-100)
                - is_similar: Boolean indicating if images are similar (>70%)
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
            # Calculate perceptual hashes
            hash1 = self.calculate_perceptual_hash(image1_data)
            hash2 = self.calculate_perceptual_hash(image2_data)
            
            if hash1 and hash2:
                # Calculate Hamming distance
                hamming_distance = imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)
                # Convert to similarity (0-100, higher is more similar)
                # Max distance is 64 for average hash
                perceptual_similarity = max(0, 100 - (hamming_distance / 64.0 * 100))
                result['perceptual_hash_similarity'] = perceptual_similarity
            
            # Calculate SSIM (if available)
            ssim_score = self.calculate_ssim(image1_data, image2_data)
            if ssim_score is not None:
                result['ssim_score'] = ssim_score
                ssim_similarity = ssim_score * 100  # Convert to 0-100 scale
            else:
                ssim_similarity = 0
            
            # Calculate overall similarity (weighted average)
            # If SSIM is not available, use only perceptual hash
            if result['perceptual_hash_similarity'] is not None:
                if ssim_score is not None:
                    overall = (result['perceptual_hash_similarity'] * 0.4 + ssim_similarity * 0.6)
                else:
                    # Fallback to perceptual hash only if SSIM unavailable
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
        """
        Compare an image against all known reference images.
        
        Args:
            image_data: Image bytes to compare
            threshold: Minimum similarity threshold (0-100)
        
        Returns:
            List of matches with similarity scores
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
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def decode_base64_image(self, base64_string: str) -> Optional[bytes]:
        """Decode base64 encoded image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            return base64.b64decode(base64_string)
        except Exception as e:
            logger.error(f"[VisualSimilarity] Error decoding base64 image: {e}")
            return None


# Global instance
_visual_similarity_service: Optional[VisualSimilarityService] = None


def get_visual_similarity_service() -> VisualSimilarityService:
    """Get global visual similarity service instance"""
    global _visual_similarity_service
    if _visual_similarity_service is None:
        _visual_similarity_service = VisualSimilarityService()
    return _visual_similarity_service

