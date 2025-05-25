#!/usr/bin/env python3
"""
Test script to verify the fix for the missing services.request_validation module.
This simulates the import chain that was causing the application startup failure.
"""

import sys
import os

# Add the current directory to Python path to simulate the app environment
sys.path.insert(0, '/workspaces/dahopevi')

def test_import_chain():
    """Test the import chain that was causing the original error."""
    try:
        print("Testing import chain...")
        
        # Step 1: Test direct import of services.request_validation
        print("1. Testing: from services.request_validation import validate_json_request")
        from services.request_validation import validate_json_request
        print("   ✓ SUCCESS")
        
        # Step 2: Test that the function works as expected
        print("2. Testing validate_json_request function...")
        class MockRequest:
            def __init__(self, is_json=True, json_data=None):
                self.is_json = is_json
                self.json = json_data
        
        mock_req = MockRequest(True, {'test': 'data'})
        result = validate_json_request(mock_req)
        assert result == {'test': 'data'}, f"Expected {{'test': 'data'}}, got {result}"
        print("   ✓ SUCCESS: Function works correctly")
        
        # Step 3: Test error cases
        print("3. Testing error cases...")
        try:
            invalid_req = MockRequest(False, None)
            validate_json_request(invalid_req)
            print("   ✗ FAILED: Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"   ✓ SUCCESS: Correctly raised ValueError: {e}")
        
        print("\nAll tests passed! The import issue should be resolved.")
        return True
        
    except ImportError as e:
        print(f"   ✗ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"   ✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_chain()
    if success:
        print("\n🎉 Fix confirmed! The application should now start without the ModuleNotFoundError.")
        sys.exit(0)
    else:
        print("\n❌ Fix validation failed.")
        sys.exit(1)
