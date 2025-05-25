# Fix for MoviePy get_setting import error

## Changes Made:

1. Added a compatibility layer for accessing MoviePy config settings
2. Updated font path resolution to work in Coolify environment
3. Modified imports to avoid direct dependency on get_setting
4. Added fallback mechanisms to ensure the application works across MoviePy versions

The fix allows the application to work with both older and newer versions of MoviePy by providing a unified interface to access configuration settings.
