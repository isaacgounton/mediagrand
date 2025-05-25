#!/usr/bin/env python3
"""
Minimal test to verify the services.request_validation module can be imported.
This test specifically addresses the ModuleNotFoundError that was causing the application crash.
"""

import sys
import os

# Add current directory to Python path (simulating app environment)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Test the import that was failing."""
    print("Testing import: from services.request_validation import validate_json_request")
    
    try:
        # Mock Flask since it's not available in this environment
        import types
        flask_mock = types.ModuleType('flask')
        flask_mock.request = None
        flask_mock.jsonify = lambda x: x
        sys.modules['flask'] = flask_mock
        
        # Now test the import
        from services.request_validation import validate_json_request
        
        print("✅ SUCCESS: Import completed without errors!")
        print("✅ Module location:", validate_json_request.__module__)
        print("✅ Function name:", validate_json_request.__name__)
        
        # Test the function with a mock request
        class MockRequest:
            def __init__(self, is_json=True, json_data=None):
                self.is_json = is_json
                self.json = json_data
        
        test_req = MockRequest(True, {"test": "data"})
        result = validate_json_request(test_req)
        print("✅ Function test successful, result:", result)
        
        return True
        
    except ImportError as e:
        print("❌ IMPORT ERROR:", str(e))
        return False
    except Exception as e:
        print("❌ UNEXPECTED ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 The ModuleNotFoundError has been fixed!")
        print("The application should now start successfully with gunicorn.")
    else:
        print("\n💥 The fix is not complete. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
