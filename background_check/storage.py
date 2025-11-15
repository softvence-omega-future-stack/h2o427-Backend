"""
Custom Cloudinary storage backend for handling PDFs and documents
"""
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class PublicMediaCloudinaryStorage(RawMediaCloudinaryStorage):
    """
    Use RawMediaCloudinaryStorage for PDFs and documents.
    This stores files as raw/upload (not image/upload) so PDFs are downloadable.
    """
    pass
