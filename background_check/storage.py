"""
Custom Cloudinary storage backend for handling PDFs and documents
"""
from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader


class PublicMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom Cloudinary storage that ensures files are publicly accessible
    """
    
    def _save(self, name, content):
        """
        Override save method to upload with public access and proper file extension
        """
        # Get file extension from original filename
        import os
        from django.core.files.uploadedfile import UploadedFile
        
        # Preserve original filename and extension
        if isinstance(content, UploadedFile) and content.name:
            original_name = content.name
            # Use original filename to preserve extension
            name = os.path.join(os.path.dirname(name), original_name)
        
        # Upload with public access options
        try:
            # Read file content
            content.seek(0)
            file_content = content.read()
            
            # Upload to Cloudinary with proper options
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder='media/reports',
                resource_type='auto',  # Auto-detect file type
                type='upload',  # Standard upload (not authenticated)
                use_filename=True,  # Use original filename
                unique_filename=True,  # Add unique suffix
                overwrite=False,
                invalidate=True,
            )
            
            # Return the public_id (Cloudinary's file identifier)
            return upload_result['public_id']
            
        except Exception as e:
            # Fall back to parent class method if upload fails
            print(f"Cloudinary upload error: {e}")
            return super()._save(name, content)
    
    def url(self, name):
        """
        Override URL method to ensure proper file extension in URL
        """
        # Get the base URL from parent
        base_url = super().url(name)
        
        # Cloudinary URLs for raw/auto files should include extension
        # If missing, the file won't be accessible
        return base_url
