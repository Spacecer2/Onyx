"""
Vision analysis and object detection for JARVIS
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BasicVisionAnalyzer:
    """Basic computer vision analysis without deep learning models"""
    
    def __init__(self):
        # Initialize OpenCV classifiers
        self.face_cascade = None
        self.eye_cascade = None
        self._load_classifiers()
    
    def _load_classifiers(self):
        """Load OpenCV Haar cascade classifiers"""
        try:
            # Try to load face cascade
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if Path(face_cascade_path).exists():
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
                logger.info("Face detection classifier loaded")
            
            # Try to load eye cascade
            eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
            if Path(eye_cascade_path).exists():
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                logger.info("Eye detection classifier loaded")
                
        except Exception as e:
            logger.warning(f"Could not load OpenCV classifiers: {e}")
    
    def analyze_image(self, image: np.ndarray) -> Dict:
        """Perform comprehensive image analysis"""
        analysis = {
            "basic_stats": self._get_basic_stats(image),
            "color_analysis": self._analyze_colors(image),
            "edge_analysis": self._analyze_edges(image),
            "face_detection": self._detect_faces(image),
            "motion_analysis": None,  # Would need previous frame
            "objects": self._detect_basic_objects(image)
        }
        
        return analysis
    
    def _get_basic_stats(self, image: np.ndarray) -> Dict:
        """Get basic image statistics"""
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        # Convert to grayscale for brightness analysis
        if channels == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        return {
            "dimensions": (width, height),
            "channels": channels,
            "brightness": float(brightness),
            "contrast": float(contrast),
            "total_pixels": width * height
        }
    
    def _analyze_colors(self, image: np.ndarray) -> Dict:
        """Analyze color distribution in the image"""
        if len(image.shape) != 3:
            return {"error": "Not a color image"}
        
        # Split into BGR channels
        b, g, r = cv2.split(image)
        
        # Calculate average colors
        avg_colors = {
            "red": float(np.mean(r)),
            "green": float(np.mean(g)),
            "blue": float(np.mean(b))
        }
        
        # Determine dominant color
        dominant = max(avg_colors.items(), key=lambda x: x[1])
        
        # Calculate color histogram
        hist_r = cv2.calcHist([r], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([g], [0], None, [256], [0, 256])
        hist_b = cv2.calcHist([b], [0], None, [256], [0, 256])
        
        return {
            "average_colors": avg_colors,
            "dominant_color": dominant[0],
            "dominant_value": dominant[1],
            "color_variance": {
                "red": float(np.var(r)),
                "green": float(np.var(g)),
                "blue": float(np.var(b))
            }
        }
    
    def _analyze_edges(self, image: np.ndarray) -> Dict:
        """Analyze edges and shapes in the image"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect edges using Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Count edge pixels
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_density = edge_pixels / total_pixels
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contours
        large_contours = [c for c in contours if cv2.contourArea(c) > 100]
        
        return {
            "edge_density": float(edge_density),
            "total_contours": len(contours),
            "large_contours": len(large_contours),
            "complexity": "high" if edge_density > 0.1 else "medium" if edge_density > 0.05 else "low"
        }
    
    def _detect_faces(self, image: np.ndarray) -> Dict:
        """Detect faces in the image"""
        if self.face_cascade is None:
            return {"error": "Face detection not available"}
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        face_info = []
        for (x, y, w, h) in faces:
            face_info.append({
                "position": (int(x), int(y)),
                "size": (int(w), int(h)),
                "center": (int(x + w/2), int(y + h/2))
            })
            
            # Try to detect eyes within the face
            if self.eye_cascade is not None:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                face_info[-1]["eyes_detected"] = len(eyes)
        
        return {
            "faces_detected": len(faces),
            "faces": face_info
        }
    
    def _detect_basic_objects(self, image: np.ndarray) -> Dict:
        """Detect basic geometric objects and patterns"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        objects = {
            "rectangles": 0,
            "circles": 0,
            "triangles": 0,
            "other_shapes": 0
        }
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Skip very small contours
                continue
            
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Classify based on number of vertices
            vertices = len(approx)
            
            if vertices == 3:
                objects["triangles"] += 1
            elif vertices == 4:
                # Check if it's roughly rectangular
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h
                if 0.7 <= aspect_ratio <= 1.3:  # Roughly square
                    objects["rectangles"] += 1
                else:
                    objects["rectangles"] += 1
            elif vertices > 8:
                # Might be a circle
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.7:
                        objects["circles"] += 1
                    else:
                        objects["other_shapes"] += 1
            else:
                objects["other_shapes"] += 1
        
        return objects
    
    def generate_description(self, analysis: Dict) -> str:
        """Generate a natural language description of the analysis"""
        descriptions = []
        
        # Basic stats
        stats = analysis.get("basic_stats", {})
        if stats:
            width, height = stats.get("dimensions", (0, 0))
            brightness = stats.get("brightness", 0)
            
            if brightness < 50:
                lighting = "very dark"
            elif brightness < 100:
                lighting = "dark"
            elif brightness < 150:
                lighting = "moderately lit"
            elif brightness < 200:
                lighting = "bright"
            else:
                lighting = "very bright"
            
            descriptions.append(f"The image is {width}x{height} pixels and appears {lighting}")
        
        # Color analysis
        colors = analysis.get("color_analysis", {})
        if colors and "dominant_color" in colors:
            dominant = colors["dominant_color"]
            descriptions.append(f"with a {dominant} tint")
        
        # Face detection
        faces = analysis.get("face_detection", {})
        if faces and faces.get("faces_detected", 0) > 0:
            face_count = faces["faces_detected"]
            if face_count == 1:
                descriptions.append("I can see 1 person's face")
            else:
                descriptions.append(f"I can see {face_count} people's faces")
        
        # Objects
        objects = analysis.get("objects", {})
        if objects:
            shape_counts = []
            for shape, count in objects.items():
                if count > 0:
                    shape_counts.append(f"{count} {shape}")
            
            if shape_counts:
                descriptions.append(f"I detected {', '.join(shape_counts)}")
        
        # Edge analysis
        edges = analysis.get("edge_analysis", {})
        if edges:
            complexity = edges.get("complexity", "unknown")
            descriptions.append(f"The scene has {complexity} visual complexity")
        
        if not descriptions:
            return "I can see an image, but I'm having trouble analyzing its contents."
        
        return ". ".join(descriptions) + "."

class VisionAnalysisManager:
    """High-level vision analysis management"""
    
    def __init__(self):
        self.analyzer = BasicVisionAnalyzer()
    
    def analyze_current_view(self, image: np.ndarray) -> str:
        """Analyze the current camera view and return description"""
        try:
            analysis = self.analyzer.analyze_image(image)
            description = self.analyzer.generate_description(analysis)
            return description
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return "I'm having trouble analyzing the current view."
    
    def get_detailed_analysis(self, image: np.ndarray) -> Dict:
        """Get detailed technical analysis"""
        return self.analyzer.analyze_image(image)
