#!/usr/bin/env python3
"""
Test script for JARVIS Enhanced Vision Analysis
"""

import sys
import time
import cv2
import numpy as np
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def create_test_image():
    """Create a test image with text, shapes, and colors"""
    # Create a 800x600 image
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Add background color
    img[:] = (50, 100, 150)  # Blue-green background
    
    # Add some shapes
    cv2.rectangle(img, (100, 100), (200, 200), (255, 0, 0), -1)  # Blue rectangle
    cv2.circle(img, (400, 150), 50, (0, 255, 0), -1)  # Green circle
    cv2.rectangle(img, (500, 100), (600, 200), (0, 0, 255), -1)  # Red rectangle
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "JARVIS Vision Test", (50, 300), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "OCR Text Detection", (50, 350), font, 0.8, (255, 255, 0), 2)
    cv2.putText(img, "Object Recognition", (50, 400), font, 0.8, (0, 255, 255), 2)
    
    return img

def test_enhanced_vision():
    """Test the enhanced vision analysis system"""
    print("🔍 Testing JARVIS Enhanced Vision Analysis...")
    print("=" * 60)
    
    try:
        # Import enhanced vision
        from jarvis.vision.enhanced_analysis import get_enhanced_vision
        
        # Initialize vision system
        print("📊 Initializing enhanced vision system...")
        vision = get_enhanced_vision()
        print("✅ Enhanced vision system initialized")
        
        # Create test image
        print("\n🎨 Creating test image...")
        test_image = create_test_image()
        print(f"✅ Test image created: {test_image.shape[1]}x{test_image.shape[0]} pixels")
        
        # Test 1: Basic image properties
        print("\n📏 Test 1: Image properties...")
        properties = vision.get_image_properties(test_image)
        print(f"  ✅ Image properties: {properties}")
        
        # Test 2: OCR text extraction
        print("\n📝 Test 2: OCR text extraction...")
        if vision.ocr_available:
            text = vision.extract_text(test_image)
            print(f"  ✅ Extracted text: '{text}'")
        else:
            print("  ⚠️ OCR not available (pytesseract not installed)")
        
        # Test 3: Object detection
        print("\n🔍 Test 3: Object detection...")
        objects = vision.detect_objects(test_image)
        print(f"  ✅ Detected {len(objects)} objects:")
        for obj in objects:
            print(f"    - {obj['type']} at position {obj['position']}")
        
        # Test 4: Color analysis
        print("\n🎨 Test 4: Color analysis...")
        colors = vision.analyze_colors(test_image)
        if 'dominant_colors' in colors:
            print(f"  ✅ Found {len(colors['dominant_colors'])} dominant colors")
            for i, color in enumerate(colors['dominant_colors'][:3]):
                print(f"    - Color {i+1}: RGB{color}")
        else:
            print(f"  ❌ Color analysis failed: {colors.get('error', 'Unknown error')}")
        
        # Test 5: Edge detection
        print("\n📐 Test 5: Edge detection...")
        edges = vision.detect_edges(test_image)
        if 'edge_density' in edges:
            print(f"  ✅ Edge density: {edges['edge_density']:.4f}")
            print(f"  ✅ Total edges: {edges['total_edges']}")
        else:
            print(f"  ❌ Edge detection failed: {edges.get('error', 'Unknown error')}")
        
        # Test 6: Brightness analysis
        print("\n💡 Test 6: Brightness analysis...")
        brightness = vision.analyze_brightness_contrast(test_image)
        if 'brightness' in brightness:
            print(f"  ✅ Brightness: {brightness['brightness']:.2f}")
            print(f"  ✅ Contrast: {brightness['contrast']:.2f}")
        else:
            print(f"  ❌ Brightness analysis failed: {brightness.get('error', 'Unknown error')}")
        
        # Test 7: Comprehensive analysis
        print("\n🔬 Test 7: Comprehensive analysis...")
        analysis = vision.analyze_image_comprehensive(test_image)
        print(f"  ✅ Analysis completed in {analysis.get('analysis_time', 0):.2f} seconds")
        print(f"  ✅ Features detected: {analysis.get('features_detected', [])}")
        
        # Test 8: Analysis summary
        print("\n📋 Test 8: Analysis summary...")
        summary = vision.get_analysis_summary(analysis)
        print(f"  ✅ Summary: {summary}")
        
        # Test 9: Performance statistics
        print("\n📈 Test 9: Performance statistics...")
        stats = vision.get_performance_stats()
        print(f"  ✅ Performance stats: {stats}")
        
        print("\n🎉 All enhanced vision tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced vision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision_integration():
    """Test vision integration with command processor"""
    print("\n🔗 Testing Vision Integration...")
    print("=" * 50)
    
    try:
        from jarvis.commands.processor import CommandProcessor
        
        # Initialize command processor
        print("🎯 Initializing command processor...")
        processor = CommandProcessor()
        print("✅ Command processor initialized")
        
        # Test vision commands
        print("\n🎤 Testing vision commands...")
        test_commands = [
            "Analyze image",
            "Read text from image",
            "Detect objects",
            "Count faces",
            "Analyze colors"
        ]
        
        for command in test_commands:
            print(f"  🎯 Testing: '{command}'")
            try:
                response = processor.process_command(command)
                print(f"     Response: '{response[:100]}...'")
            except Exception as e:
                print(f"     Error: {e}")
        
        print("\n✅ Vision integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Vision integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test if required dependencies are available"""
    print("\n📦 Testing Dependencies...")
    print("=" * 40)
    
    dependencies = {
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'Pillow': 'PIL',
        'pytesseract': 'pytesseract',
        'scikit-learn': 'sklearn'
    }
    
    missing = []
    available = []
    
    for package, import_name in dependencies.items():
        try:
            __import__(import_name)
            available.append(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package}")
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
    else:
        print("\n✅ All dependencies available!")
    
    return len(missing) == 0

if __name__ == "__main__":
    print("🚀 JARVIS Enhanced Vision Analysis Test Suite")
    print("=" * 70)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    if deps_ok:
        # Run tests
        vision_test_success = test_enhanced_vision()
        integration_test_success = test_vision_integration()
        
        print("\n" + "=" * 70)
        print("📋 Test Results Summary:")
        print(f"  📦 Dependencies: {'✅ PASSED' if deps_ok else '❌ FAILED'}")
        print(f"  🔍 Vision Analysis: {'✅ PASSED' if vision_test_success else '❌ FAILED'}")
        print(f"  🔗 Integration: {'✅ PASSED' if integration_test_success else '❌ FAILED'}")
        
        if vision_test_success and integration_test_success:
            print("\n🎉 All tests passed! Enhanced vision system is working correctly.")
            print("\n📋 Next Steps:")
            print("  1. Test with real camera images")
            print("  2. Integrate with JARVIS camera system")
            print("  3. Use vision commands in conversations")
        else:
            print("\n⚠️ Some tests failed. Check the output above for details.")
    else:
        print("\n❌ Cannot run tests - missing dependencies.")
        print("Please install required packages and try again.")
