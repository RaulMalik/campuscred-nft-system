"""
PDF Signing Service
Signs PDFs with digital signatures for authenticity verification
"""
import os
from datetime import datetime, timedelta
from PyPDF2 import PdfReader, PdfWriter
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
import io


def _safe_log(level, message):
    # log safely whether or not we're in app context
    try:
        from flask import current_app
        getattr(current_app.logger, level)(message)
    except (ImportError, RuntimeError):
        print(f"[{level.upper()}] {message}")


class PDFSignerService:
    # service for signing PDF documents with digital signatures as per usercase. Maybe let's add PNG's etc also right now only hash

    def __init__(self):
        self.private_key = None
        self.certificate = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        #load existing signing keys or generate new ones. These are in env gets generated to local storage and used
        key_path = os.getenv('PDF_SIGNING_KEY_PATH', 'app/private_storage/signing_key.pem')
        cert_path = os.getenv('PDF_SIGNING_CERT_PATH', 'app/private_storage/signing_cert.pem')

        # Try to load existing keys
        if os.path.exists(key_path) and os.path.exists(cert_path):
            try:
                with open(key_path, 'rb') as key_file:
                    self.private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                with open(cert_path, 'rb') as cert_file:
                    self.certificate = x509.load_pem_x509_certificate(
                        cert_file.read(),
                        backend=default_backend()
                    )
                _safe_log('info', "Loaded existing signing keys")
                return
            except Exception as e:
                _safe_log('warning', f"Failed to load keys: {str(e)}, generating new ones")

        # generate new keys if we dont find any
        self._generate_signing_keys(key_path, cert_path)

    def _generate_signing_keys(self, key_path, cert_path):
        """Generate new RSA signing keys and self-signed certificate"""
        try:
            #generate private key
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            #generate self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "DK"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Capital Region"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Copenhagen"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CampusCred"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CampusCred Document Signer"),
            ])

            self.certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                self.private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=3650)
            ).sign(self.private_key, hashes.SHA256(), default_backend())

            # Save keys
            os.makedirs(os.path.dirname(key_path), exist_ok=True)

            with open(key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            with open(cert_path, 'wb') as f:
                f.write(self.certificate.public_bytes(serialization.Encoding.PEM))

            _safe_log('info', "Generated new signing keys and certificate")

        except Exception as e:
            _safe_log('error', f"Failed to generate signing keys: {str(e)}")
            raise

    def sign_pdf(self, pdf_content, metadata=None):
        #Sign the PDF document with digital signature
        try:
            # read PDF
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            pdf_writer = PdfWriter()

            # copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            # add metadata to it (authentication method)
            if metadata:
                pdf_writer.add_metadata({
                    '/Title': metadata.get('title', 'Signed Document'),
                    '/Author': 'CampusCred System',
                    '/Subject': metadata.get('subject', 'Academic Credential'),
                    '/Creator': 'CampusCred PDF Signer',
                    '/Producer': 'CampusCred',
                    '/CreationDate': datetime.utcnow().strftime('D:%Y%m%d%H%M%S'),
                })

            # write PDF
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            signed_content = output_buffer.getvalue()

            # compute the signature over the PDF
            signature = self.private_key.sign(
                signed_content,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            _safe_log('info', "PDF signed successfully")
            return signed_content

        except Exception as e:
            _safe_log('error', f"Failed to sign PDF: {str(e)}")
            raise

    def get_certificate_info(self):
        if not self.certificate:
            return None

        return {
            'subject': self.certificate.subject.rfc4514_string(),
            'issuer': self.certificate.issuer.rfc4514_string(),
            'serial_number': str(self.certificate.serial_number),
            'not_before': self.certificate.not_valid_before.isoformat(),
            'not_after': self.certificate.not_valid_after.isoformat(),
        }