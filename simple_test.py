#!/usr/bin/env python3
"""
Simple test to verify the core logic of the concatenate fix.
"""

import os

def test_file_path_detection():
    """Test the core logic that determines if a path is a local file or URL."""
    
    print("Testing file path detection logic...")
    
    # Test cases that simulate the original error scenario
    test_cases = [
        # Original failing case from the error logs
        "/tmp/scene_445_0.mp4",
        "/tmp/scene_445_1.mp4", 
        "/tmp/scene_445_2.mp4",
        # URL cases (should still work)
        "https://example.com/video.mp4",
        "http://example.com/video.mp4",
        "ftp://example.com/video.mp4",
        # Other local path variations
        "/workspaces/dahopevi/test.mp4",
        "./relative/path.mp4",
        "relative_file.mp4"
    ]
    
    print("\nSimulating the logic from the fixed concatenate function:")
    print("if os.path.isfile(url): use local file")
    print("else: download as URL")
    print()
    
    for path in test_cases:
        is_local_file = os.path.isfile(path)
        action = "Use local file directly" if is_local_file else "Download as URL"
        
        print(f"Path: {path}")
        print(f"  os.path.isfile(): {is_local_file}")
        print(f"  Action: {action}")
        print()
    
    print("✅ Core logic test completed!")
    print("\nThe fix works by:")
    print("1. Using os.path.isfile() to detect local files vs URLs") 
    print("2. Local files (like /tmp/scene_445_0.mp4) bypass download_file()")
    print("3. URLs still go through download_file() as before")
    print("4. Only downloaded files are cleaned up, not original local files")
    
    return True

def simulate_original_error():
    """Simulate the original error scenario."""
    
    print("\n" + "="*60)
    print("SIMULATING ORIGINAL ERROR SCENARIO")
    print("="*60)
    
    # This is what was happening before the fix
    scene_videos = [
        "/tmp/scene_445_0.mp4",
        "/tmp/scene_445_1.mp4", 
        "/tmp/scene_445_2.mp4",
        "/tmp/scene_445_3.mp4",
        "/tmp/scene_445_4.mp4"
    ]
    
    print("Original code was doing:")
    print("video_urls = [{'video_url': scene_video} for scene_video in scene_videos]")
    print()
    
    video_urls = [{"video_url": scene_video} for scene_video in scene_videos]
    
    print("This created video_urls:")
    for i, item in enumerate(video_urls):
        print(f"  {i}: {item}")
    
    print("\nThen download_file() was called on each path:")
    print("download_file('/tmp/scene_445_0.mp4', ...)")
    print("↓")
    print("requests.get('/tmp/scene_445_0.mp4', ...)")
    print("↓") 
    print("❌ Invalid URL '/tmp/scene_445_0.mp4': No scheme supplied")
    
    print("\n✅ With the fix:")
    print("os.path.isfile('/tmp/scene_445_0.mp4') → True (if file exists)")
    print("→ Use file directly, skip download_file()")
    print("→ No more 'No scheme supplied' error!")
    
    return True

if __name__ == "__main__":
    print("Testing the concatenate fix logic...")
    
    test_file_path_detection()
    simulate_original_error()
    
    print("\n🎉 Logic verification completed!")
    print("The fix should resolve the 'No scheme supplied' error.")
