import os
from datetime import datetime

from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import ClientError

# Import for safe logging
try:
    from flask import current_app
    _has_flask = True
except (ImportError, RuntimeError):
    _has_flask = False


def _safe_log(level: str, message: str) -> None:
    """Log safely whether or not we're in a Flask app context."""
    if _has_flask:
        try:
            getattr(current_app.logger, level)(message)
            return
        except RuntimeError:
            # No app context
            pass
    print(f"[{level.upper()}] {message}")


class StorageService:
    """
    Private evidence file storage.

    - Supports **local disk** and **S3-compatible** object storage.
    - Files are NOT on-chain and NOT on IPFS.
    - In this project:
        * Default base_path 'app/private_storage' + valid AWS_* env → S3.
        * Any *custom* base_path (e.g. tests using tmp_path) → local disk only.

    This keeps unit tests fast and deterministic, while allowing real S3 in dev/prod.
    """

    def __init__(self, base_path: str = "app/private_storage") -> None:
        self.base_path = base_path
        self.allowed_extensions = {
            "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "txt"
        }

        # Use S3 only when:
        #   - AWS env vars are present, AND
        #   - we are using the default private storage path.
        if self.base_path == "app/private_storage" and self._check_s3_config():
            self.use_s3 = True
            self._init_s3_client()
        else:
            self.use_s3 = False
            os.makedirs(self.base_path, exist_ok=True)

    # -------------------------------------------------------------------------
    # S3 setup / helpers
    # -------------------------------------------------------------------------

    def _check_s3_config(self) -> bool:
        """Check if S3 env vars are configured."""
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
        configured = all(os.getenv(var) for var in required_vars)
        if not configured:
            _safe_log("info", "S3 not configured; using local storage")
        return configured

    def _init_s3_client(self) -> None:
        """Initialise S3 client; if it fails, fall back to local."""
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "eu-north-1"),
                endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            )
            self.bucket_name = os.getenv("S3_BUCKET_NAME")
            _safe_log("info", f"S3 storage initialized: bucket={self.bucket_name}")
        except Exception as e:
            _safe_log("error", f"Failed to initialize S3 client, falling back to local: {e}")
            self.use_s3 = False
            os.makedirs(self.base_path, exist_ok=True)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def allowed_file(self, filename: str | None) -> bool:
        """Check if filename has an allowed extension."""
        if not filename:
            return False
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions
        )

    def save_evidence_file(self, file, claim_id: int) -> tuple[str | None, str | None]:
        """
        Save an uploaded evidence file, either to S3 or local disk.

        Returns:
            (stored_path, original_filename) or (None, None) on failure / invalid.
        """
        if not file or not self.allowed_file(file.filename):
            return None, None

        original_filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ext = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"claim_{claim_id}_{timestamp}.{ext}"

        # Prefer S3 if enabled; if that fails, fall back to local.
        if self.use_s3:
            s3_path, s3_orig = self._save_to_s3(file, unique_filename, original_filename)
            if s3_path:
                return s3_path, s3_orig
            _safe_log("warning", "S3 upload failed; falling back to local storage")

        # Local fallback
        file.seek(0) if hasattr(file, "seek") else None
        return self._save_locally(file, unique_filename, original_filename)

    def get_file(self, file_path: str) -> bytes | None:
        """Retrieve file contents from S3 or local disk."""
        if self.use_s3 and file_path.startswith("evidence/"):
            content = self._get_from_s3(file_path)
            if content is not None:
                return content
            _safe_log("warning", f"S3 get failed for {file_path}, trying local")

        return self._get_locally(file_path)

    def delete_file(self, file_path: str | None) -> bool:
        """Delete a file; returns True if removed, False otherwise."""
        if not file_path:
            return False

        if self.use_s3 and file_path.startswith("evidence/"):
            deleted = self._delete_from_s3(file_path)
            if deleted:
                return True
            _safe_log("warning", f"S3 delete failed for {file_path}, trying local")

        return self._delete_locally(file_path)

    def file_exists(self, file_path: str | None) -> bool:
        """Check if a file exists in S3 or locally."""
        if not file_path:
            return False

        if self.use_s3 and file_path.startswith("evidence/"):
            exists = self._exists_in_s3(file_path)
            if exists:
                return True
            # If S3 doesn’t see it, no need to check local unless you want
            # hybrid storage; here we assume S3-only for that key.
            return False

        return os.path.exists(file_path)

    # -------------------------------------------------------------------------
    # Local storage helpers
    # -------------------------------------------------------------------------

    def _save_locally(self, file, unique_filename: str, original_filename: str) -> tuple[str, str]:
        """Save file to local disk."""
        os.makedirs(self.base_path, exist_ok=True)
        file_path = os.path.join(self.base_path, unique_filename)
        file.save(file_path)
        return file_path, original_filename

    def _get_locally(self, file_path: str) -> bytes | None:
        """Read local file into memory."""
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            _safe_log("error", f"Failed to read local file {file_path}: {e}")
        return None

    def _delete_locally(self, file_path: str) -> bool:
        """Delete local file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            _safe_log("error", f"Failed to delete local file {file_path}: {e}")
        return False

    # -------------------------------------------------------------------------
    # S3 helpers
    # -------------------------------------------------------------------------

    def _save_to_s3(self, file, unique_filename: str, original_filename: str) -> tuple[str | None, str | None]:
        """Upload file to S3; returns (s3_key, original_filename) or (None, None)."""
        try:
            s3_key = f"evidence/{unique_filename}"
            # File must be file-like with .read(); for Werkzeug file objects this is true.
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "Metadata": {"original-filename": original_filename},
                },
            )
            _safe_log("info", f"File uploaded to S3: {s3_key}")
            return s3_key, original_filename
        except ClientError as e:
            _safe_log("error", f"Failed to upload to S3: {e}")
        except Exception as e:
            _safe_log("error", f"Unexpected error during S3 upload: {e}")
        return None, None

    def _get_from_s3(self, s3_key: str) -> bytes | None:
        """Download a file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            _safe_log("error", f"Failed to download from S3: {e}")
        except Exception as e:
            _safe_log("error", f"Unexpected error during S3 download: {e}")
        return None

    def _delete_from_s3(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            _safe_log("info", f"File deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            _safe_log("error", f"Failed to delete from S3: {e}")
        except Exception as e:
            _safe_log("error", f"Unexpected error during S3 delete: {e}")
        return False

    def _exists_in_s3(self, s3_key: str) -> bool:
        """Check if a key exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
        except Exception as e:
            _safe_log("error", f"Error checking existence in S3: {e}")
            return False