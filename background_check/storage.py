"""
Custom Cloudinary storage backend for handling PDFs and documents
"""
from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary


class PublicMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom Cloudinary storage that ensures files are publicly accessible
    """
    
    def _save(self, name, content):
        """
        Override save method to add public access options
        """
        # Set upload options for public access
        options = {
            'resource_type': 'auto',  # Auto-detect file type
            'type': 'upload',  # Upload type (not authenticated)
            'access_mode': 'public',  # Make file publicly accessible
            'invalidate': True,  # Invalidate CDN cache
        }
        
        # Store original options
        original_options = getattr(self, 'upload_options', {})
        self.upload_options = {**original_options, **options}
        
        # Call parent save method
        result = super()._save(name, content)
        
        # Restore original options
        self.upload_options = original_options
        
        return result
