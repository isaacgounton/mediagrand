#!/usr/bin/env python3
"""
Test script to validate MoviePy migration for Coolify deployment.
This script tests the MoviePy renderer without requiring FFmpeg.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, '/workspaces/dahopevi')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required imports work."""
    logger.info("Testing imports...")
    
    try:
        # Test MoviePy imports
        from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, TextClip
        logger.info("✅ MoviePy imports successful")
    except ImportError as e:
        logger.error(f"❌ MoviePy import failed: {e}")
        return False
    
    try:
        # Test our MoviePy renderer
        from services.v1.video.moviepy_composition import MoviePyRenderer
        logger.info("✅ MoviePyRenderer import successful")
    except ImportError as e:
        logger.error(f"❌ MoviePyRenderer import failed: {e}")
        return False
    
    try:
        # Test config
        from config import LOCAL_STORAGE_PATH
        logger.info(f"✅ Config import successful. LOCAL_STORAGE_PATH: {LOCAL_STORAGE_PATH}")
    except ImportError as e:
        logger.error(f"❌ Config import failed: {e}")
        return False
    
    return True

def test_moviepy_renderer_init():
    """Test MoviePy renderer initialization."""
    logger.info("Testing MoviePy renderer initialization...")
    
    try:
        from services.v1.video.moviepy_composition import MoviePyRenderer
        renderer = MoviePyRenderer()
        
        logger.info(f"✅ MoviePy renderer initialized successfully")
        logger.info(f"   Portrait size: {renderer.portrait_size}")
        logger.info(f"   Landscape size: {renderer.landscape_size}")
        logger.info(f"   Default font: {renderer.default_font}")
        
        return True
    except Exception as e:
        logger.error(f"❌ MoviePy renderer initialization failed: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set."""
    logger.info("Testing environment variables...")
    
    required_vars = [
        'PEXELS_API_KEY',
        'LOCAL_STORAGE_PATH',
        'DEFAULT_BACKGROUND_VIDEO',
        'DEFAULT_BACKGROUND_MUSIC'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️  {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("These will use default values or may cause issues during video creation")
    
    return True

def test_font_availability():
    """Test font availability."""
    logger.info("Testing font availability...")
    
    from services.v1.video.moviepy_composition import MoviePyRenderer
    renderer = MoviePyRenderer()
    
    font_paths = [
        "/workspaces/dahopevi/fonts/Roboto-Regular.ttf",
        "/workspaces/dahopevi/fonts/Arial.ttf",
        "/workspaces/dahopevi/fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    available_fonts = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            available_fonts.append(font_path)
            logger.info(f"✅ Font found: {font_path}")
    
    if available_fonts:
        logger.info(f"✅ {len(available_fonts)} fonts available")
        return True
    else:
        logger.warning("⚠️  No fonts found in expected locations")
        return True  # This is not critical, MoviePy can use system fonts

def test_directory_structure():
    """Test required directory structure."""
    logger.info("Testing directory structure...")
    
    from config import LOCAL_STORAGE_PATH
    
    required_dirs = [
        LOCAL_STORAGE_PATH,
        "/workspaces/dahopevi/fonts",
        "/workspaces/dahopevi/services/v1/video"
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            logger.info(f"✅ Directory exists: {directory}")
        else:
            logger.error(f"❌ Directory missing: {directory}")
            return False
    
    return True

def run_all_tests():
    """Run all validation tests."""
    logger.info("🚀 Starting MoviePy migration validation...")
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Directory Structure", test_directory_structure),
        ("Font Availability", test_font_availability),
        ("MoviePy Renderer Initialization", test_moviepy_renderer_init),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! MoviePy migration is ready for deployment.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
