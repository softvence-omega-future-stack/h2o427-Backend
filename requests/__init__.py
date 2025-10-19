# This module conflicts with the Python requests library
# Ensure the real requests library is available for DRF
import sys
import os

# Store the original module search path
_original_path = sys.path[:]

def _import_real_requests():
    """Import the real requests library, avoiding this local module"""
    # Temporarily modify sys.path to avoid importing this local module
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    
    # Remove paths that would import our local requests module
    temp_path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]
    
    # Temporarily replace sys.path
    original_path = sys.path[:]
    sys.path[:] = temp_path
    
    try:
        import requests as real_requests
        sys.path[:] = original_path
        return real_requests
    except ImportError:
        sys.path[:] = original_path
        raise

# Make real requests available as a fallback
try:
    requests = _import_real_requests()
except ImportError:
    pass