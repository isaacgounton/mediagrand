#!/usr/bin/env python3
"""
Test script to verify the concatenate fix for local file paths.
"""

import os
import tempfile
import sys
sys.path.append('/workspaces/dahopevi')

from services.v1.video.concatenate import process_video_concatenate

def test_concatenate_with_local_files():
    """Test concatenation with local file paths instead of URLs."""
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some dummy video file paths
        test_file1 = os.path.join(temp_dir, "test1.mp4")
        test_file2 = os.path.join(temp_dir, "test2.mp4")
        
        # Create empty files to simulate video files
        with open(test_file1, 'w') as f:
            f.write("dummy video content 1")
        with open(test_file2, 'w') as f:
            f.write("dummy video content 2")
        
        # Test the function with local file paths
        media_urls = [
            {"video_url": test_file1},
            {"video_url": test_file2}
        ]
        
        try:
            # This should not raise an exception about missing URL schemes
            result = process_video_concatenate(media_urls, "test_job_123")
            print(f"Test passed! Function executed without URL scheme error.")
            print(f"Result: {result}")
            
            # Clean up result file if it exists
            if os.path.exists(result):
                os.remove(result)
                
        except Exception as e:
            print(f"Test failed with error: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("Testing concatenate fix for local file paths...")
    success = test_concatenate_with_local_files()
    if success:
        print("✓ Test completed successfully!")
    else:
        print("✗ Test failed!")
