# IPFS service for uploading credential metadata Uses Pinata API for pinning to IPFS

import requests
import json
import os
from flask import current_app


class IPFSService:
    """Handle IPFS uploads via Pinata"""

    def __init__(self):
        self.api_key = os.getenv('PINATA_API_KEY')
        self.secret_key = os.getenv('PINATA_SECRET_API_KEY')
        self.base_url = 'https://api.pinata.cloud'

        # check if credentials are configured
        self.enabled = bool(self.api_key and self.secret_key)

    def upload_json(self, data, pin_name=None):
        """
        Upload JSON metadata to IPFS via Pinata

        Args:
            data: Dictionary to upload
            pin_name: Optional name for the pin

        Returns:
            str: ipfs:// URI
        """
        if not self.enabled:
            current_app.logger.warning("Pinata credentials not configured, using mock IPFS")
            # Return a mock IPFS URI for testing
            import hashlib
            data_str = json.dumps(data, sort_keys=True)
            mock_hash = hashlib.sha256(data_str.encode()).hexdigest()[:46]
            return f'ipfs://Qm{mock_hash}'

        url = f'{self.base_url}/pinning/pinJSONToIPFS'

        headers = {
            'pinata_api_key': self.api_key,
            'pinata_secret_api_key': self.secret_key
        }

        payload = {
            'pinataContent': data,
            'pinataMetadata': {
                'name': pin_name or 'CampusCred Metadata'
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            ipfs_hash = response.json()['IpfsHash']
            ipfs_uri = f'ipfs://{ipfs_hash}'

            current_app.logger.info(f"Uploaded to IPFS: {ipfs_uri}")
            return ipfs_uri

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Pinata upload failed: {str(e)}")
            raise Exception(f"Failed to upload to IPFS: {str(e)}")

    def get_gateway_url(self, ipfs_uri):
        """
        Convert IPFS URI to gateway URL

        Args:
            ipfs_uri: ipfs://hash format

        Returns:
            str: HTTPS gateway URL
        """
        if ipfs_uri.startswith('ipfs://'):
            ipfs_hash = ipfs_uri.replace('ipfs://', '')
            return f'https://gateway.pinata.cloud/ipfs/{ipfs_hash}'
        return ipfs_uri