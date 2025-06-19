#!/usr/bin/env python3
"""
Check if Playwright browsers are installed and install them if missing.
This script provides a safety net for Playwright browser installation.
"""

import subprocess
import sys
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_playwright_browsers():
    """Check if Playwright browsers are installed and install them if missing."""
    try:
        # Try to import playwright
        from playwright.sync_api import sync_playwright
        
        # Test if chromium is available
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                logger.info("Playwright Chromium browser is available and working.")
                return True
            except Exception as e:
                logger.warning(f"Playwright Chromium browser test failed: {e}")
                return False
                
    except ImportError as e:
        logger.error(f"Playwright not installed: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers."""
    try:
        logger.info("Installing Playwright browsers...")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("Playwright browsers installed successfully.")
            return True
        else:
            logger.error(f"Failed to install Playwright browsers: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Playwright browser installation timed out.")
        return False
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {e}")
        return False

def main():
    """Main function to check and install Playwright browsers if needed."""
    logger.info("Checking Playwright browser installation...")
    
    if check_playwright_browsers():
        logger.info("Playwright browsers are ready.")
        sys.exit(0)
    
    logger.info("Playwright browsers not found or not working. Installing...")
    
    if install_playwright_browsers():
        # Double-check after installation
        if check_playwright_browsers():
            logger.info("Playwright browsers installed and verified successfully.")
            sys.exit(0)
        else:
            logger.error("Playwright browsers installation verification failed.")
            sys.exit(1)
    else:
        logger.error("Failed to install Playwright browsers.")
        sys.exit(1)

if __name__ == "__main__":
    main()