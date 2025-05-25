#!/usr/bin/env python3
"""
DahoPevi API Startup Validation Script

This script validates the environment and configuration before starting the application
to prevent runtime crashes and provide helpful error messages.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_required_environment_variables():
    """Check that all required environment variables are set."""
    logger.info("Checking required environment variables...")
    
    required_vars = {
        'API_KEY': 'API authentication key',
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        return False
    
    logger.info("✓ All required environment variables are set")
    return True

def check_optional_services():
    """Check optional services and warn if they're not configured."""
    logger.info("Checking optional services...")
    
    # Video search APIs
    pexels_key = os.getenv('PEXELS_API_KEY')
    pixabay_key = os.getenv('PIXABAY_API_KEY')
    
    if not pexels_key and not pixabay_key:
        logger.warning("⚠ No video search APIs configured (PEXELS_API_KEY, PIXABAY_API_KEY)")
        logger.warning("  Background video search will be unavailable - using default videos only")
    elif not pexels_key:
        logger.warning("⚠ PEXELS_API_KEY not configured - Pexels video search unavailable")
    elif not pixabay_key:
        logger.warning("⚠ PIXABAY_API_KEY not configured - Pixabay video search unavailable")
    else:
        logger.info("✓ Video search APIs configured")
    
    # Cloud storage
    gcp_configured = bool(os.getenv('GCP_BUCKET_NAME')) and bool(os.getenv('GCP_SA_CREDENTIALS'))
    s3_configured = bool(os.getenv('S3_ENDPOINT_URL')) and bool(os.getenv('S3_ACCESS_KEY'))
    
    if not gcp_configured and not s3_configured:
        logger.warning("⚠ No cloud storage configured - files will be stored locally")
        logger.warning("  For production, configure either GCP or S3 storage")
    elif gcp_configured:
        logger.info("✓ Google Cloud Storage configured")
    elif s3_configured:
        logger.info("✓ S3-compatible storage configured")

def check_directories():
    """Check that required directories exist and are writable."""
    logger.info("Checking directories...")
    
    storage_path = os.getenv('LOCAL_STORAGE_PATH', '/tmp')
    required_dirs = [
        storage_path,
        f"{storage_path}/assets",
        f"{storage_path}/music",
        f"{storage_path}/jobs"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = path / '.write_test'
            test_file.touch()
            test_file.unlink()
            logger.info(f"✓ Directory {dir_path} exists and is writable")
        except Exception as e:
            logger.error(f"✗ Cannot create or write to directory {dir_path}: {e}")
            return False
    
    return True

def check_placeholder_assets():
    """Check that placeholder assets exist."""
    logger.info("Checking placeholder assets...")
    
    storage_path = os.getenv('LOCAL_STORAGE_PATH', '/tmp')
    placeholder_video = os.getenv('DEFAULT_PLACEHOLDER_VIDEO', f'{storage_path}/assets/placeholder.mp4')
    placeholder_music = os.getenv('DEFAULT_BACKGROUND_MUSIC', f'{storage_path}/music/default.wav')
    
    assets_ok = True
    
    if not os.path.exists(placeholder_video):
        logger.warning(f"⚠ Placeholder video not found: {placeholder_video}")
        logger.warning("  Run 'python scripts/create_placeholders.py' to create it")
        assets_ok = False
    else:
        logger.info(f"✓ Placeholder video exists: {placeholder_video}")
    
    if not os.path.exists(placeholder_music):
        logger.warning(f"⚠ Placeholder music not found: {placeholder_music}")
        logger.warning("  Run 'python scripts/create_placeholders.py' to create it")
        assets_ok = False
    else:
        logger.info(f"✓ Placeholder music exists: {placeholder_music}")
    
    return assets_ok

def check_python_dependencies():
    """Check that critical Python dependencies are available."""
    logger.info("Checking Python dependencies...")
    
    critical_modules = [
        ('flask', 'Flask web framework'),
        ('whisper', 'OpenAI Whisper for transcription'),
        ('torch', 'PyTorch for ML models'),
        ('ffmpeg', 'FFmpeg Python bindings'),
        ('requests', 'HTTP client library'),
        ('PIL', 'Pillow image processing'),
    ]
    
    missing_modules = []
    for module, description in critical_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module} ({description})")
        except ImportError:
            missing_modules.append(f"{module} ({description})")
    
    if missing_modules:
        logger.error("Missing critical Python dependencies:")
        for module in missing_modules:
            logger.error(f"  - {module}")
        logger.error("Run 'pip install -r requirements.txt' to install dependencies")
        return False
    
    return True

def check_system_commands():
    """Check that required system commands are available."""
    logger.info("Checking system commands...")
    
    required_commands = [
        ('ffmpeg', 'FFmpeg for video processing'),
        ('ffprobe', 'FFprobe for media analysis'),
    ]
    
    missing_commands = []
    for cmd, description in required_commands:
        if not os.system(f"which {cmd} > /dev/null 2>&1") == 0:
            # Windows compatibility
            if os.name == 'nt':
                if not os.system(f"where {cmd} > nul 2>&1") == 0:
                    missing_commands.append(f"{cmd} ({description})")
            else:
                missing_commands.append(f"{cmd} ({description})")
        else:
            logger.info(f"✓ {cmd} ({description})")
    
    if missing_commands:
        logger.error("Missing required system commands:")
        for cmd in missing_commands:
            logger.error(f"  - {cmd}")
        return False
    
    return True

def create_health_check_endpoint_test():
    """Test that the application can start without crashing."""
    logger.info("Testing application startup...")
    
    try:
        # Import the app to test for import errors
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app import create_app
        
        app = create_app()
        logger.info("✓ Application imports successfully")
        
        # Test basic configuration
        with app.app_context():
            from config import API_KEY, LOCAL_STORAGE_PATH
            logger.info("✓ Configuration loads successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Application startup test failed: {e}")
        return False

def main():
    """Main validation function."""
    logger.info("DahoPevi API Startup Validation")
    logger.info("=" * 40)
    
    checks = [
        ("Environment Variables", check_required_environment_variables),
        ("Optional Services", check_optional_services),
        ("Directories", check_directories),
        ("Placeholder Assets", check_placeholder_assets),
        ("Python Dependencies", check_python_dependencies),
        ("System Commands", check_system_commands),
        ("Application Startup", create_health_check_endpoint_test),
    ]
    
    failed_checks = []
    warning_checks = []
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} ---")
        try:
            result = check_func()
            if result is False:
                failed_checks.append(check_name)
            elif result is None:  # Warnings only
                warning_checks.append(check_name)
        except Exception as e:
            logger.error(f"Error during {check_name}: {e}")
            failed_checks.append(check_name)
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 40)
    
    if failed_checks:
        logger.error(f"✗ {len(failed_checks)} critical issues found:")
        for check in failed_checks:
            logger.error(f"  - {check}")
        logger.error("\nPlease fix these issues before starting the application.")
        return 1
    
    if warning_checks:
        logger.warning(f"⚠ {len(warning_checks)} warnings (non-critical):")
        for check in warning_checks:
            logger.warning(f"  - {check}")
    
    logger.info("✓ All critical checks passed!")
    logger.info("The application should start successfully.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
