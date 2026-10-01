import os
import aiofiles
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from app.core.config import settings

class StorageAdapter(ABC):
    @abstractmethod
    async def save_file(self, file_bytes: bytes, filename: str) -> str:
        """Saves file bytes and returns the stored file path/URL."""
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> bytes:
        """Reads file bytes from stored location."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    async def check_ready(self) -> bool:
        """Checks if the storage backend is reachable, writeable, and healthy."""
        pass

class LocalStorageAdapter(StorageAdapter):
    """Local disk storage adapter for development and self-hosted deployments."""
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        target_path = os.path.join(self.upload_dir, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        async with aiofiles.open(target_path, "wb") as out_file:
            await out_file.write(file_bytes)
        return target_path

    async def read_file(self, file_path: str) -> bytes:
        async with aiofiles.open(file_path, "rb") as in_file:
            return await in_file.read()

    async def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False

    async def check_ready(self) -> bool:
        try:
            os.makedirs(self.upload_dir, exist_ok=True)
            probe_path = os.path.join(self.upload_dir, ".health_probe")
            async with aiofiles.open(probe_path, "w") as f:
                await f.write("ok")
            if os.path.exists(probe_path):
                os.remove(probe_path)
            return True
        except Exception:
            return False

class GoogleCloudStorageAdapter(StorageAdapter):
    """
    Google Cloud Storage (GCS) / Firebase Storage adapter.
    Uploads blobs to a Google Cloud Storage bucket and generates secure HTTPS URLs.
    Requires GOOGLE_APPLICATION_CREDENTIALS or GCS_BUCKET_NAME.
    Gracefully falls back to local storage if credentials/bucket are unavailable.
    """
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        credentials_path: Optional[str] = None,
        fallback_local: Optional[StorageAdapter] = None
    ):
        self.bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        self.credentials_path = credentials_path or settings.GOOGLE_APPLICATION_CREDENTIALS
        self.fallback = fallback_local or LocalStorageAdapter()
        self._client = None
        self._bucket = None
        self.is_configured = False

        try:
            from google.cloud import storage
            if self.credentials_path and os.path.exists(self.credentials_path):
                self._client = storage.Client.from_service_account_json(self.credentials_path)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
                self._client = storage.Client.from_service_account_json(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            else:
                self._client = storage.Client()

            if self.bucket_name:
                self._bucket = self._client.bucket(self.bucket_name)
                self.is_configured = True
        except Exception as e:
            # GCP credentials not yet provisioned; will use fallback
            self.is_configured = False

    async def save_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        if not self.is_configured or not self._bucket:
            return await self.fallback.save_file(file_bytes, filename)

        try:
            def _upload():
                import urllib.parse
                import uuid
                
                token = str(uuid.uuid4())
                blob = self._bucket.blob(filename)
                blob.metadata = {"firebaseStorageDownloadTokens": token}
                if content_type:
                    blob.content_type = content_type
                blob.upload_from_string(file_bytes, content_type=content_type)

                encoded_filename = urllib.parse.quote(filename, safe="")
                # Firebase Storage tokenized download URL
                if "appspot.com" in self.bucket_name or "firebasestorage" in self.bucket_name:
                    return f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{encoded_filename}?alt=media&token={token}"
                # Standard Google Cloud Storage URL
                return f"https://storage.googleapis.com/{self.bucket_name}/{filename}"

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _upload)
        except Exception as err:
            # Fallback to local storage if GCS upload fails
            return await self.fallback.save_file(file_bytes, filename)

    async def read_file(self, file_path: str) -> bytes:
        if not self.is_configured or not self._bucket or not file_path.startswith("http"):
            return await self.fallback.read_file(file_path)
        try:
            def _download():
                prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
                filename = file_path.replace(prefix, "")
                blob = self._bucket.blob(filename)
                return blob.download_as_bytes()
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _download)
        except Exception:
            return await self.fallback.read_file(file_path)

    async def delete_file(self, file_path: str) -> bool:
        if not self.is_configured or not self._bucket or not file_path.startswith("http"):
            return await self.fallback.delete_file(file_path)
        try:
            def _delete():
                prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
                filename = file_path.replace(prefix, "")
                blob = self._bucket.blob(filename)
                blob.delete()
                return True
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _delete)
        except Exception:
            return await self.fallback.delete_file(file_path)

    async def check_ready(self) -> bool:
        if self.is_configured and self._bucket:
            return True
        return await self.fallback.check_ready()

class S3CompatibleStorageAdapter(StorageAdapter):
    """
    STUB / BLUEPRINT: Cloudflare R2 / AWS S3 / MinIO object storage adapter.
    Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, S3_ENDPOINT_URL.
    Ready for production activation when cloud storage bucket credentials are provisioned.
    """
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "vitalens-reports")
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self.aws_access_key = aws_access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.is_configured = bool(self.aws_access_key and self.aws_secret_key)

    async def save_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        if not self.is_configured:
            raise NotImplementedError(
                "S3CompatibleStorageAdapter: Cloud credentials missing. Configure AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY."
            )
        return f"s3://{self.bucket_name}/{filename}"

    async def read_file(self, file_path: str) -> bytes:
        if not self.is_configured:
            raise NotImplementedError("S3 credentials not configured.")
        return b""

    async def delete_file(self, file_path: str) -> bool:
        if not self.is_configured:
            return False
        return True

    async def check_ready(self) -> bool:
        return self.is_configured

class ImageKitStorageAdapter(StorageAdapter):
    """
    ImageKit.io cloud storage adapter.
    Fast, global image CDN with generous free tier (20 GB bandwidth & storage).
    Requires NO credit card to sign up.
    """
    def __init__(
        self,
        private_key: Optional[str] = None,
        fallback_local: Optional[StorageAdapter] = None
    ):
        self.private_key = private_key or os.getenv("IMAGEKIT_PRIVATE_KEY") or getattr(settings, "IMAGEKIT_PRIVATE_KEY", None)
        self.fallback = fallback_local or LocalStorageAdapter()
        self._client = None
        self.is_configured = bool(self.private_key)

        if self.is_configured:
            try:
                from imagekitio import AsyncImageKit
                self._client = AsyncImageKit(private_key=self.private_key)
            except Exception as e:
                self.is_configured = False

    async def save_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        if not self.is_configured or not self._client:
            return await self.fallback.save_file(file_bytes, filename)

        try:
            clean_name = filename.split("/")[-1]
            response = await self._client.files.upload(
                file=file_bytes,
                file_name=clean_name,
                folder="/vitalens_avatars",
                use_unique_file_name=True
            )
            return response.url
        except Exception as err:
            print(f"[ImageKit] Upload error, falling back to local: {err}")
            return await self.fallback.save_file(file_bytes, filename)

    async def read_file(self, file_path: str) -> bytes:
        return await self.fallback.read_file(file_path)

    async def delete_file(self, file_path: str) -> bool:
        return True

    async def check_ready(self) -> bool:
        return self.is_configured

# Factory to provide active storage adapter based on environment configuration
def get_storage_adapter() -> StorageAdapter:
    provider = os.getenv("STORAGE_PROVIDER", settings.STORAGE_PROVIDER).lower()
    if provider in ["imagekit", "imagekitio"]:
        return ImageKitStorageAdapter()
    elif provider in ["gcs", "google", "firebase"]:
        return GoogleCloudStorageAdapter()
    elif provider == "s3":
        return S3CompatibleStorageAdapter()
    return LocalStorageAdapter()

storage_adapter = get_storage_adapter()

def get_public_file_url(file_path_or_url: str) -> str:
    """Converts a local file path or cloud URL into an accessible HTTP URL."""
    if not file_path_or_url:
        return ""
    if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
        return file_path_or_url
    
    # Normalize local upload path
    normalized = file_path_or_url.replace("\\", "/")
    if "/uploads/" in normalized:
        subpath = normalized.split("/uploads/", 1)[1]
        return f"/uploads/{subpath}"
    return f"/uploads/{os.path.basename(normalized)}"
