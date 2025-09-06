#!/usr/bin/env python3
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_imports():
    """Check that all required packages are available"""
    required_packages = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask CORS'),
        ('requests', 'Requests'),
        ('dotenv', 'Python Dotenv'),
        ('werkzeug', 'Werkzeug'),
        ('json', 'JSON'),
        ('os', 'OS'),
        ('logging', 'Logging')
    ]
    
    missing = []
    for package, name in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {name} is available")
        except ImportError as e:
            logger.error(f"✗ {name} is not available: {e}")
            missing.append(name)
    
    if missing:
        logger.error(f"\nMissing packages: {', '.join(missing)}")
        logger.error("\nPlease install missing packages using:")
        logger.error("pip install -r requirements.txt")
        sys.exit(1)
    else:
        logger.info("\nAll required packages are available!")

def check_tts_config():
    """Check TTS configuration"""
    try:
        from config.config import TTS_SERVER_URL
        logger.info(f"✓ TTS Server URL is configured: {TTS_SERVER_URL}")
    except (ImportError, AttributeError):
        logger.error("✗ TTS Server URL is not configured in config.py")
        sys.exit(1)

def main():
    """Run all environment checks"""
    logger.info("Checking Python environment...")
    check_imports()
    check_tts_config()

if __name__ == "__main__":
    main()
