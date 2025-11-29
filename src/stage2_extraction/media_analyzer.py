"""
Media Analyzer - Image and Video Analysis for Misinformation Detection
"""
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime
from pathlib import Path
import hashlib

# Image processing
from PIL import Image
import imagehash
import cv2
import numpy as np

# OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# HTTP
import aiohttp

from ..models.content import MediaAnalysis, MediaType

logger = structlog.get_logger(__name__)


class MediaAnalyzer:
    """Analyze images and videos for misinformation detection"""

    def __init__(self, cache_dir: str = "./data/media_cache"):
        """
        Initialize media analyzer

        Args:
            cache_dir: Directory to cache downloaded media
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_media(
        self,
        media_url: str,
        perform_reverse_search: bool = True,
        extract_text: bool = True
    ) -> MediaAnalysis:
        """
        Analyze image or video from URL

        Args:
            media_url: URL of media to analyze
            perform_reverse_search: Whether to do reverse image search
            extract_text: Whether to extract text via OCR

        Returns:
            MediaAnalysis object
        """
        logger.info("Analyzing media", url=media_url[:100])

        # Determine media type
        media_type = self._detect_media_type(media_url)

        # Download media
        local_path = await self._download_media(media_url)

        if not local_path:
            logger.error("Failed to download media", url=media_url)
            return MediaAnalysis(
                media_url=media_url,
                media_type=media_type
            )

        analysis = MediaAnalysis(
            media_url=media_url,
            media_type=media_type,
            analysis_timestamp=datetime.utcnow()
        )

        # Analyze based on type
        if media_type == MediaType.IMAGE:
            analysis = await self._analyze_image(local_path, analysis, perform_reverse_search, extract_text)
        elif media_type == MediaType.VIDEO:
            analysis = await self._analyze_video(local_path, analysis)

        return analysis

    def _detect_media_type(self, url: str) -> MediaType:
        """Detect media type from URL"""
        url_lower = url.lower()

        video_exts = ['.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        audio_exts = ['.mp3', '.wav', '.ogg', '.m4a']

        for ext in video_exts:
            if ext in url_lower:
                return MediaType.VIDEO

        for ext in image_exts:
            if ext in url_lower:
                return MediaType.IMAGE

        for ext in audio_exts:
            if ext in url_lower:
                return MediaType.AUDIO

        # Default to image if unclear
        return MediaType.IMAGE

    async def _download_media(self, url: str) -> Optional[Path]:
        """Download media to cache"""
        try:
            # Generate cache filename
            url_hash = hashlib.md5(url.encode()).hexdigest()
            ext = Path(url).suffix or '.jpg'
            cache_path = self.cache_dir / f"{url_hash}{ext}"

            # Return if already cached
            if cache_path.exists():
                logger.info("Using cached media", path=str(cache_path))
                return cache_path

            # Download
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        cache_path.write_bytes(content)
                        logger.info("Media downloaded", url=url[:100], size=len(content))
                        return cache_path
                    else:
                        logger.error("Download failed", status=response.status, url=url[:100])
                        return None

        except Exception as e:
            logger.error("Media download error", error=str(e), url=url[:100])
            return None

    async def _analyze_image(
        self,
        image_path: Path,
        analysis: MediaAnalysis,
        perform_reverse_search: bool,
        extract_text: bool
    ) -> MediaAnalysis:
        """Analyze image file"""

        try:
            # Open image
            img = Image.open(image_path)

            # Extract metadata (EXIF)
            metadata = self._extract_image_metadata(img)
            analysis.metadata = metadata

            # Compute perceptual hash
            img_hash = imagehash.average_hash(img)
            analysis.metadata['perceptual_hash'] = str(img_hash)

            # Reverse image search
            if perform_reverse_search:
                reverse_results = await self._reverse_image_search(image_path, str(img_hash))
                analysis.reverse_search_results = reverse_results

                # Find earliest occurrence
                if reverse_results:
                    earliest = min(
                        (r for r in reverse_results if r.get('date')),
                        key=lambda x: x.get('date', datetime.max),
                        default=None
                    )
                    if earliest and earliest.get('date'):
                        analysis.earliest_occurrence = earliest['date']

            # OCR text extraction
            if extract_text and TESSERACT_AVAILABLE:
                ocr_text = self._extract_text_from_image(image_path)
                analysis.ocr_text = ocr_text

            # Object detection (basic - detect if image has people)
            objects = self._detect_objects(img)
            analysis.detected_objects = objects

            logger.info(
                "Image analyzed",
                has_text=bool(analysis.ocr_text),
                objects_count=len(objects),
                reverse_results=len(analysis.reverse_search_results)
            )

        except Exception as e:
            logger.error("Image analysis failed", error=str(e))
            analysis.metadata['error'] = str(e)

        return analysis

    async def _analyze_video(
        self,
        video_path: Path,
        analysis: MediaAnalysis
    ) -> MediaAnalysis:
        """Analyze video file"""

        try:
            # Open video
            cap = cv2.VideoCapture(str(video_path))

            if not cap.isOpened():
                logger.error("Failed to open video", path=str(video_path))
                return analysis

            # Extract video metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            analysis.metadata = {
                'fps': fps,
                'frame_count': frame_count,
                'duration_seconds': duration,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }

            # Extract keyframes for analysis
            keyframes = self._extract_keyframes(cap, max_frames=5)

            # Analyze keyframes
            for i, frame in enumerate(keyframes):
                # Save keyframe as image
                frame_path = self.cache_dir / f"frame_{video_path.stem}_{i}.jpg"
                cv2.imwrite(str(frame_path), frame)

                # Detect objects in frame
                objects = self._detect_objects_cv(frame)
                if objects:
                    analysis.detected_objects.extend(objects)

            # Remove duplicates
            analysis.detected_objects = list(set(analysis.detected_objects))

            cap.release()

            logger.info(
                "Video analyzed",
                duration=duration,
                frames=frame_count,
                objects=len(analysis.detected_objects)
            )

        except Exception as e:
            logger.error("Video analysis failed", error=str(e))
            analysis.metadata['error'] = str(e)

        return analysis

    def _extract_image_metadata(self, img: Image) -> Dict[str, Any]:
        """Extract EXIF and other metadata from image"""
        metadata = {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height
        }

        # EXIF data
        try:
            exif = img._getexif()
            if exif:
                from PIL.ExifTags import TAGS

                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[f'exif_{tag}'] = str(value)

        except Exception:
            pass

        return metadata

    async def _reverse_image_search(
        self,
        image_path: Path,
        image_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Perform reverse image search to find earliest occurrence

        Note: This is a simplified implementation.
        In production, integrate with:
        - Google Images API
        - TinEye API
        - Yandex Images API
        """
        results = []

        # For now, return empty results
        # TODO: Implement actual reverse search API integration
        logger.info("Reverse image search (placeholder)", hash=image_hash)

        return results

    def _extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            if not TESSERACT_AVAILABLE:
                return ""

            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()

        except Exception as e:
            logger.error("OCR failed", error=str(e))
            return ""

    def _detect_objects(self, img: Image) -> List[str]:
        """
        Detect objects in image (basic implementation)

        For production, use:
        - YOLOv8
        - CLIP
        - Google Vision API
        """
        objects = []

        # Convert to numpy array
        img_array = np.array(img)

        # Basic detection: check if image likely contains faces
        # (This is a placeholder - use proper face detection in production)
        if self._has_skin_tones(img_array):
            objects.append("person")

        return objects

    def _detect_objects_cv(self, frame: np.ndarray) -> List[str]:
        """Detect objects in video frame using OpenCV"""
        objects = []

        # Basic detection
        if self._has_skin_tones(frame):
            objects.append("person")

        return objects

    def _has_skin_tones(self, img_array: np.ndarray) -> bool:
        """
        Simple heuristic to detect if image contains skin tones
        (placeholder for actual face/person detection)
        """
        try:
            # Convert to HSV
            if len(img_array.shape) == 3:
                if img_array.shape[2] == 3:
                    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
                elif img_array.shape[2] == 4:
                    rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
                else:
                    return False

                # Skin tone range in HSV
                lower_skin = np.array([0, 20, 70], dtype=np.uint8)
                upper_skin = np.array([20, 255, 255], dtype=np.uint8)

                # Create mask
                mask = cv2.inRange(hsv, lower_skin, upper_skin)

                # Check if significant skin tone pixels
                skin_ratio = np.sum(mask > 0) / mask.size
                return skin_ratio > 0.1

        except Exception:
            pass

        return False

    def _extract_keyframes(
        self,
        cap: cv2.VideoCapture,
        max_frames: int = 5
    ) -> List[np.ndarray]:
        """Extract keyframes from video"""
        frames = []
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count <= max_frames:
            # Extract all frames
            indices = range(frame_count)
        else:
            # Sample evenly
            step = frame_count // max_frames
            indices = range(0, frame_count, step)[:max_frames]

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        return frames

    async def batch_analyze(
        self,
        media_urls: List[str]
    ) -> List[MediaAnalysis]:
        """Analyze multiple media URLs in parallel"""
        tasks = [
            self.analyze_media(url)
            for url in media_urls
        ]
        return await asyncio.gather(*tasks)


# Helper function for quick media analysis
async def analyze_media_url(url: str) -> MediaAnalysis:
    """Quick helper to analyze a single media URL"""
    analyzer = MediaAnalyzer()
    return await analyzer.analyze_media(url)
