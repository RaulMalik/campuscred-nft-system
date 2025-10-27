import os
from werkzeug.utils import secure_filename
from datetime import datetime


class StorageService:
    """
    Handle private file storage for evidence uploads
    Files are stored locally in app/private_storage/
    NOT on blockchain or IPFS - these are private!
    """

    def __init__(self, base_path='app/private_storage'):
        self.base_path = base_path
        # Allowed file types
        self.allowed_extensions = {
            'pdf', 'png', 'jpg', 'jpeg', 'gif',
            'doc', 'docx', 'txt'
        }

        # Create storage directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)

    def allowed_file(self, filename):
        "Check if file extension is allowed"
        if not filename:
            return False
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_evidence_file(self, file, claim_id):
        """
        Save uploaded evidence file privately

        Args:
            file: FileStorage object from Flask request.files
            claim_id: ID of the claim this evidence belongs to

        Returns:
            tuple: (file_path, original_filename) or (None, None) if failed
        """
        if not file or not self.allowed_file(file.filename):
            return None, None

        # Secure the original filename
        original_filename = secure_filename(file.filename)

        # Create unique filename: claim_ID_timestamp.ext
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"claim_{claim_id}_{timestamp}.{file_extension}"

        # Full path to save file
        file_path = os.path.join(self.base_path, unique_filename)

        # Save the file
        file.save(file_path)

        return file_path, original_filename

    def delete_file(self, file_path):
        "Delete a file (for claim rejection cleanup)"
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def file_exists(self, file_path):
        "Check if a file exists"
        return file_path and os.path.exists(file_path)