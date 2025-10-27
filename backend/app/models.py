from app import db
from datetime import datetime
import hashlib


class Claim(db.Model):
    """Model for credential claims submitted by students"""
    __tablename__ = 'claims'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Student information
    student_name = db.Column(db.String(100), nullable=False)
    student_email = db.Column(db.String(120), nullable=False)
    student_address = db.Column(db.String(42))  # Ethereum wallet address

    # Credential details
    credential_type = db.Column(db.String(20), nullable=False)  # 'micro', 'course', 'diploma'
    course_code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

    # File storage (PRIVATE - not on blockchain/IPFS)
    evidence_file_path = db.Column(db.String(500))  # Path to privately stored file
    evidence_file_hash = db.Column(db.String(64))  # SHA-256 hash of file
    evidence_file_name = db.Column(db.String(255))  # Original filename

    # Status tracking
    status = db.Column(db.String(20), default='pending')
    # values: 'pending', 'approved', 'denied', 'minted'

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)  # When instructor approved
    minted_at = db.Column(db.DateTime)  # When NFT was minted (Sprint 2)

    # Instructor feedback
    instructor_notes = db.Column(db.Text)
    approved_by = db.Column(db.String(100))  # Instructor name/ID

    # Blockchain data (for Sprint 2)
    token_id = db.Column(db.Integer)  # NFT token ID
    metadata_uri = db.Column(db.String(500))  # IPFS URI to metadata
    transaction_hash = db.Column(db.String(66))  # Ethereum transaction hash

    def __repr__(self):
        return f'<Claim {self.id}: {self.course_code} - {self.status}>'

    @staticmethod
    def compute_file_hash(file_path):
        """
        Compute SHA-256 hash of a file
        This hash will later go on-chain for verification
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()