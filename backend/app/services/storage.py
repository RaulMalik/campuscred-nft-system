import os
from werkzeug.utils import secure_filename
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

#import for safe logging
try:
    from flask import current_app
    _has_flask = True
except (ImportError, RuntimeError):
    _has_flask = False


def _safe_log(level, message):
    """Log safely whether or not we're in app context"""
    if _has_flask:
        try:
            from flask import current_app
            getattr(current_app.logger, level)(message)
        except RuntimeError:
            #no app context, print to the console
            print(f"[{level.upper()}] {message}")
    else:
        print(f"[{level.upper()}] {message}")


class StorageService:
    """
    Handle private file storage for evidence uploads
    Supports both local storage and S3-compatible object storage
    Files are NOT on blockchain or IPFS - these are private!
    """

    def __init__(self, base_path='app/private_storage'):
        self.base_path = base_path
        self.allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt'}

        # Check if S3 is configured
        self.use_s3 = self._check_s3_config()

        if self.use_s3:
            self._init_s3_client()
        else:
            os.makedirs(self.base_path, exist_ok=True)

    def _check_s3_config(self):
        #check if S3 environment variables are configured first
        required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
        return all(os.getenv(var) for var in required_vars)

    def _init_s3_client(self):
        # Initialization of s3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'eu-north-1'),
                endpoint_url=os.getenv('S3_ENDPOINT_URL')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME')
            _safe_log('info', f"S3 storage initialized: bucket={self.bucket_name}")
        except Exception as e:
            _safe_log('error', f"Failed to initialize S3 client: {str(e)}")
            self.use_s3 = False

    def allowed_file(self, filename):
       #check first if file extension is allowed to be uploaded
        if not filename:
            return False
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_evidence_file(self, file, claim_id):
        # save uploaded evidence file privately (local or S3) fallback
        if not file or not self.allowed_file(file.filename):
            return None, None

        original_filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"claim_{claim_id}_{timestamp}.{file_extension}"

        if self.use_s3:
            return self._save_to_s3(file, unique_filename, original_filename)
        else:
            return self._save_locally(file, unique_filename, original_filename)

    def _save_locally(self, file, unique_filename, original_filename):
        #save file to local storage in directory func
        file_path = os.path.join(self.base_path, unique_filename)
        file.save(file_path)
        return file_path, original_filename

    def _save_to_s3(self, file, unique_filename, original_filename):
        # save file to S3 aws
        try:
            s3_key = f"evidence/{unique_filename}"

            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {'original-filename': original_filename}
                }
            )

            _safe_log('info', f"File uploaded to S3: {s3_key}")
            return s3_key, original_filename

        except ClientError as e:
            _safe_log('error', f"Failed to upload to S3: {str(e)}")
            return None, None

    def get_file(self, file_path):
        # retrieve the file content (from local or S3 whaever is used)
        if self.use_s3 and file_path.startswith('evidence/'):
            return self._get_from_s3(file_path)
        else:
            return self._get_locally(file_path)

    def _get_locally(self, file_path):
        #get file from local
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            _safe_log('error', f"Failed to read local file: {str(e)}")
        return None

    def _get_from_s3(self, s3_key):
      # Get file from S3
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            _safe_log('error', f"Failed to download from S3: {str(e)}")
            return None

    def delete_file(self, file_path):
        # delete a file (for claim rejection cleanup)
        if self.use_s3 and file_path.startswith('evidence/'):
            return self._delete_from_s3(file_path)
        else:
            return self._delete_locally(file_path)

    def _delete_locally(self, file_path):
        #delete file from local storage also
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def _delete_from_s3(self, s3_key):
        #delete file from S3 also same same
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            _safe_log('info', f"File deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            _safe_log('error', f"Failed to delete from S3: {str(e)}")
            return False

    def file_exists(self, file_path):
        # check if file exists
        if self.use_s3 and file_path.startswith('evidence/'):
            return self._exists_in_s3(file_path)
        else:
            return file_path and os.path.exists(file_path)

    def _exists_in_s3(self, s3_key):
        # check if file exists in S3 also
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False