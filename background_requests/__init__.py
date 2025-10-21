# This module conflicts with the Python requests library
# Ensure the real requests library is available for DRF and other packages
import sys
import os

def _import_real_requests():
    """Import the real requests library, avoiding this local module"""
    # Get the current module path
    current_module_path = os.path.dirname(__file__)
    project_root = os.path.dirname(current_module_path)
    
    # Create a clean sys.path without our local requests module paths
    clean_path = []
    for path in sys.path:
        # Skip paths that would lead to this local requests module
        if path != project_root and path != current_module_path and path != '':
            clean_path.append(path)
    
    # Temporarily replace sys.path
    original_path = sys.path[:]
    sys.path[:] = clean_path
    
    try:
        # Import the real requests library
        import requests as real_requests
        # Restore original path
        sys.path[:] = original_path
        return real_requests
    except ImportError:
        # Restore original path on failure
        sys.path[:] = original_path
        raise

# Provide access to real requests library
try:
    # Make the real requests module available
    _real_requests = _import_real_requests()
    
    # Add requests attributes that other packages might need
    packages = getattr(_real_requests, 'packages', None)
    urllib3 = getattr(_real_requests, 'urllib3', None)
    
    # Export commonly used requests attributes
    globals().update({
        'packages': packages,
        'urllib3': urllib3,
        'Session': getattr(_real_requests, 'Session', None),
        'get': getattr(_real_requests, 'get', None),
        'post': getattr(_real_requests, 'post', None),
        'put': getattr(_real_requests, 'put', None),
        'delete': getattr(_real_requests, 'delete', None),
        'patch': getattr(_real_requests, 'patch', None),
        'head': getattr(_real_requests, 'head', None),
        'options': getattr(_real_requests, 'options', None),
        'request': getattr(_real_requests, 'request', None),
        'exceptions': getattr(_real_requests, 'exceptions', None),
        'codes': getattr(_real_requests, 'codes', None),
        'Response': getattr(_real_requests, 'Response', None),
        'Request': getattr(_real_requests, 'Request', None),
    })
    
except ImportError:
    # If we can't import the real requests library, continue without it
    pass