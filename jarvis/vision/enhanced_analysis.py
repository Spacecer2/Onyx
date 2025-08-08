"""
JARVIS Enhanced Vision Analysis - OCR, Object Detection, and Image Analysis
"""

import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, Any, Optional, List, Tuple
import base64
import io
import os
import time

# Try to import OCR libraries
try:
    import pytesseract
    OCR_AVAILABLE = True
    # Set tesseract path for different systems
    if os.path.exists('/usr/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    elif os.path.exists('/usr/local/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None

logger = logging.getLogger(__name__)

class EnhancedVisionAnalysis:
    """Advanced vision analysis with OCR, object detection, and image processing"""
    
    def __init__(self):
        self.ocr_available = OCR_AVAILABLE
        self.face_cascade = None
        self.eye_cascade = None
        self._load_cascades()
        
        # Performance tracking
        self.analysis_times = []
        
        logger.info(f"Enhanced Vision Analysis initialized - OCR: {'Available' if OCR_AVAILABLE else 'Not available'}")
    
    def _load_cascades(self):
        """Load OpenCV cascade classifiers for face and object detection"""
        try:
            # Load face detection cascade
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(face_cascade_path):
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # Load eye detection cascade
            eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
            if os.path.exists(eye_cascade_path):
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                
            logger.info("Cascade classifiers loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load cascade classifiers: {e}")
    
    def analyze_image_comprehensive(self, image_data: np.ndarray, 
                                  include_ocr: bool = True,
                                  include_objects: bool = True,
                                  include_faces: bool = True,
                                  include_colors: bool = True) -> Dict[str, Any]:
        """Comprehensive image analysis with multiple detection methods"""
        start_time = time.time()
        
        analysis = {
            'image_properties': self.get_image_properties(image_data),
            'analysis_time': 0,
            'features_detected': []
        }
        
        try:
            # OCR Analysis
            if include_ocr and self.ocr_available:
                ocr_result = self.extract_text(image_data)
                analysis['text_content'] = ocr_result
                if ocr_result and ocr_result.strip():
                    analysis['features_detected'].append('text')
            
            # Object Detection
            if include_objects:
                objects_result = self.detect_objects(image_data)
                analysis['objects_detected'] = objects_result
                if objects_result:
                    analysis['features_detected'].append('objects')
            
            # Face Detection
            if include_faces and self.face_cascade is not None:
                faces_result = self.detect_faces(image_data)
                analysis['faces_detected'] = faces_result
                if faces_result['count'] > 0:
                    analysis['features_detected'].append('faces')
            
            # Color Analysis
            if include_colors:
                colors_result = self.analyze_colors(image_data)
                analysis['color_analysis'] = colors_result
                analysis['features_detected'].append('colors')
            
            # Edge Detection
            edges_result = self.detect_edges(image_data)
            analysis['edge_analysis'] = edges_result
            
            # Brightness and Contrast
            brightness_result = self.analyze_brightness_contrast(image_data)
            analysis['brightness_analysis'] = brightness_result
            
            analysis['analysis_time'] = time.time() - start_time
            self.analysis_times.append(analysis['analysis_time'])
            
            logger.info(f"Image analysis completed in {analysis['analysis_time']:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def extract_text(self, image_data: np.ndarray) -> str:
        """Extract text from image using OCR"""
        if not self.ocr_available:
            return "OCR not available"
        
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(image_data)
            
            # Extract text with different configurations
            text_results = []
            
            # Standard OCR
            text = pytesseract.image_to_string(pil_image)
            if text.strip():
                text_results.append(text.strip())
            
            # OCR with different PSM modes for better accuracy
            for psm in [6, 7, 8]:  # Different page segmentation modes
                try:
                    text = pytesseract.image_to_string(pil_image, config=f'--psm {psm}')
                    if text.strip() and text.strip() not in text_results:
                        text_results.append(text.strip())
                except:
                    continue
            
            # Combine results and clean up
            combined_text = '\n'.join(text_results)
            return self._clean_ocr_text(combined_text)
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return f"OCR Error: {str(e)}"
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean and format OCR text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common OCR artifacts
        text = text.replace('|', 'I')  # Common OCR mistake
        text = text.replace('0', 'O')  # In some contexts
        
        return text.strip()
    
    def detect_objects(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in image using contour analysis and shape detection"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            objects = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small objects
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate shape properties
                    perimeter = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                    
                    # Determine shape type
                    shape_type = self._classify_shape(len(approx), area, w/h)
                    
                    objects.append({
                        'id': i,
                        'type': shape_type,
                        'area': area,
                        'position': {'x': x, 'y': y, 'width': w, 'height': h},
                        'corners': len(approx)
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def _classify_shape(self, corners: int, area: float, aspect_ratio: float) -> str:
        """Classify shape based on corner count and properties"""
        if corners == 3:
            return "triangle"
        elif corners == 4:
            if 0.8 <= aspect_ratio <= 1.2:
                return "square"
            else:
                return "rectangle"
        elif corners == 5:
            return "pentagon"
        elif corners == 6:
            return "hexagon"
        elif corners > 6:
            if aspect_ratio > 2:
                return "line"
            else:
                return "circle"
        else:
            return "unknown"
    
    def detect_faces(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Detect faces and facial features"""
        try:
            gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = []
            if self.face_cascade:
                face_rects = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in face_rects:
                    face_info = {
                        'position': {'x': x, 'y': y, 'width': w, 'height': h},
                        'eyes': []
                    }
                    
                    # Detect eyes within face region
                    if self.eye_cascade:
                        roi_gray = gray[y:y+h, x:x+w]
                        eyes = self.eye_cascade.detectMultiScale(roi_gray)
                        
                        for (ex, ey, ew, eh) in eyes:
                            face_info['eyes'].append({
                                'x': ex, 'y': ey, 'width': ew, 'height': eh
                            })
                    
                    faces.append(face_info)
            
            return {
                'count': len(faces),
                'faces': faces
            }
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return {'count': 0, 'faces': [], 'error': str(e)}
    
    def analyze_colors(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Analyze dominant colors and color distribution"""
        try:
            # Reshape image to 2D array
            pixels = image_data.reshape(-1, 3)
            
            # Calculate mean color
            mean_color = np.mean(pixels, axis=0)
            
            # Calculate color variance
            color_variance = np.var(pixels, axis=0)
            
            # Find dominant colors using k-means clustering
            from sklearn.cluster import KMeans
            try:
                kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
                kmeans.fit(pixels)
                dominant_colors = kmeans.cluster_centers_.astype(int)
                color_counts = np.bincount(kmeans.labels_)
                
                # Sort by frequency
                sorted_indices = np.argsort(color_counts)[::-1]
                dominant_colors = dominant_colors[sorted_indices]
                color_percentages = (color_counts[sorted_indices] / len(pixels)) * 100
                
            except ImportError:
                # Fallback if sklearn is not available
                dominant_colors = [mean_color.astype(int)]
                color_percentages = [100]
            
            return {
                'dominant_colors': dominant_colors.tolist(),
                'color_percentages': color_percentages.tolist(),
                'mean_color': mean_color.tolist(),
                'brightness': np.mean(mean_color),
                'color_variance': color_variance.tolist(),
                'saturation': self._calculate_saturation(image_data)
            }
            
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_saturation(self, image_data: np.ndarray) -> float:
        """Calculate average saturation of the image"""
        try:
            hsv = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1]
            return np.mean(saturation)
        except:
            return 0.0
    
    def detect_edges(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Detect edges and analyze edge patterns"""
        try:
            gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            
            # Apply different edge detection methods
            edges_canny = cv2.Canny(gray, 50, 150)
            edges_sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            edges_sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate edge statistics
            edge_density = np.sum(edges_canny > 0) / edges_canny.size
            
            return {
                'edge_density': edge_density,
                'horizontal_edges': np.mean(np.abs(edges_sobel_x)),
                'vertical_edges': np.mean(np.abs(edges_sobel_y)),
                'total_edges': np.sum(edges_canny > 0)
            }
            
        except Exception as e:
            logger.error(f"Edge detection failed: {e}")
            return {'error': str(e)}
    
    def analyze_brightness_contrast(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Analyze brightness and contrast of the image"""
        try:
            gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Calculate contrast (standard deviation)
            contrast = np.std(gray)
            
            # Calculate histogram
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            return {
                'brightness': brightness,
                'contrast': contrast,
                'min_value': np.min(gray),
                'max_value': np.max(gray),
                'dynamic_range': np.max(gray) - np.min(gray)
            }
            
        except Exception as e:
            logger.error(f"Brightness analysis failed: {e}")
            return {'error': str(e)}
    
    def get_image_properties(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Get basic image properties"""
        height, width = image_data.shape[:2]
        channels = image_data.shape[2] if len(image_data.shape) > 2 else 1
        
        return {
            'width': width,
            'height': height,
            'channels': channels,
            'aspect_ratio': width / height,
            'total_pixels': width * height,
            'file_size_estimate': width * height * channels
        }
    
    def get_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        summary_parts = []
        
        # Image properties
        props = analysis.get('image_properties', {})
        summary_parts.append(f"Image size: {props.get('width', 0)}x{props.get('height', 0)} pixels")
        
        # Text content
        if 'text_content' in analysis and analysis['text_content']:
            text = analysis['text_content']
            if len(text) > 100:
                text = text[:100] + "..."
            summary_parts.append(f"Text detected: {text}")
        
        # Objects
        objects = analysis.get('objects_detected', [])
        if objects:
            object_types = [obj['type'] for obj in objects]
            summary_parts.append(f"Objects found: {len(objects)} ({', '.join(set(object_types))})")
        
        # Faces
        faces = analysis.get('faces_detected', {})
        if faces.get('count', 0) > 0:
            summary_parts.append(f"Faces detected: {faces['count']}")
        
        # Colors
        colors = analysis.get('color_analysis', {})
        if 'dominant_colors' in colors:
            summary_parts.append(f"Dominant colors: {len(colors['dominant_colors'])} detected")
        
        # Performance
        analysis_time = analysis.get('analysis_time', 0)
        summary_parts.append(f"Analysis completed in {analysis_time:.2f} seconds")
        
        return " | ".join(summary_parts)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the vision analysis"""
        if not self.analysis_times:
            return {'average_time': 0, 'total_analyses': 0}
        
        return {
            'average_time': np.mean(self.analysis_times),
            'min_time': np.min(self.analysis_times),
            'max_time': np.max(self.analysis_times),
            'total_analyses': len(self.analysis_times),
            'recent_times': self.analysis_times[-10:]  # Last 10 analyses
        }

# Global instance
_enhanced_vision = None

def get_enhanced_vision() -> EnhancedVisionAnalysis:
    """Get the global enhanced vision analysis instance"""
    global _enhanced_vision
    if _enhanced_vision is None:
        _enhanced_vision = EnhancedVisionAnalysis()
    return _enhanced_vision
