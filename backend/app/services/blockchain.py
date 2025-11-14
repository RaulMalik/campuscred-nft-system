"""
blockchain service for interacting with CampusCredNFT contract
handle minting, verification, and on-chain queries.
"""
from web3 import Web3
import json
import os
from flask import current_app


class BlockchainService:
    # handle blockchain interactions for minting NFTs

    def __init__(self):
        self.w3 = None
        self.contract = None
        self.contract_address = None
        self.deployer_account = None

    def initialize(self):
        # start web3 connection and contract
        rpc_url = os.getenv('SEPOLIA_RPC_URL')
        if not rpc_url:
            raise ValueError("SEPOLIA_RPC_URL not set in environment")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        # check connection
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")

        # load contract address
        self.contract_address = os.getenv('CONTRACT_ADDRESS', '0x04fe8305F4C511052A5255758Bf71DF343CeFB57')

        # Load contract ABI
        try:
            # I tried multiple times here, it finally got to work on 8th mint test.
            # do not change things around with this.
            current_file = os.path.abspath(__file__)  # backend/app/services/blockchain.py
            services_dir = os.path.dirname(current_file)  # backend/app/services
            app_dir = os.path.dirname(services_dir)  # backend/app
            backend_dir = os.path.dirname(app_dir)  # backend
            project_root = os.path.dirname(backend_dir)  # project root
            abi_path = os.path.join(project_root, 'contracts', 'CampusCredNFT_ABI.json')

            current_app.logger.info(f"Looking for ABI at: {abi_path}")

            if os.path.exists(abi_path):
                with open(abi_path, 'r') as f:
                    contract_abi = json.load(f)
                current_app.logger.info(f"Loaded full ABI with {len(contract_abi)} functions/events")
            else:
                # minimal ABI for testing, so a little fallback
                contract_abi = [
                    {
                        "inputs": [
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "string", "name": "uri", "type": "string"}
                        ],
                        "name": "mint",
                        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    },
                    {
                        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                        "name": "ownerOf",
                        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                        "name": "tokenURI",
                        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                        "name": "isRevoked",
                        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]
                current_app.logger.warning("Using fallback ABI - run 'node scripts/export-abi.js' to export full ABI")
        except Exception as e:
            current_app.logger.error(f"Error loading contract ABI: {str(e)}")
            raise

        # initialize contract here
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=contract_abi
        )

        # load deployer account env file
        deployer_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        if deployer_key:
            if deployer_key.startswith('0x'):
                deployer_key = deployer_key[2:]
            self.deployer_account = self.w3.eth.account.from_key(deployer_key)

    def mint_credential(self, recipient_address, metadata_uri):
        """
        Mint a new credential NFT

        Args:
            recipient_address: Student's Ethereum address
            metadata_uri: IPFS URI pointing to credential metadata

        Returns:
            tuple: (token_id, transaction_hash)
        """
        if not self.w3 or not self.contract:
            self.initialize()

        if not self.deployer_account:
            raise ValueError("Deployer private key not configured")

        # address is checksummed
        recipient_address = Web3.to_checksum_address(recipient_address)

        #get current nonce
        nonce = self.w3.eth.get_transaction_count(self.deployer_account.address)

        # Estimate gas
        gas_estimate = self.contract.functions.mint(
            recipient_address,
            metadata_uri
        ).estimate_gas({'from': self.deployer_account.address})

        # get current base fee and calculate gas prices dynamically
        latest_block = self.w3.eth.get_block('latest')
        base_fee = latest_block['baseFeePerGas']
        max_priority_fee = self.w3.to_wei(2, 'gwei')  # 2 gwei tip to miners
        max_fee = base_fee * 2 + max_priority_fee  # Double base fee + tip for safety

        current_app.logger.info(f"Gas pricing - Base fee: {self.w3.from_wei(base_fee, 'gwei')} gwei, "
                               f"Max fee: {self.w3.from_wei(max_fee, 'gwei')} gwei, "
                               f"Priority fee: {self.w3.from_wei(max_priority_fee, 'gwei')} gwei")

        # Build transaction
        txn = self.contract.functions.mint(
            recipient_address,
            metadata_uri
        ).build_transaction({
            'from': self.deployer_account.address,
            'nonce': nonce,
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': max_priority_fee,
            'chainId': 11155111  # Sepolia chain ID
        })

        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.deployer_account.key)

        # send transaction. Important use rawTransaction instead of raw_transaction.
        # This caused continious errors before
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        current_app.logger.info(f"Minting transaction sent: {tx_hash.hex()}")

        # wait for receipt (with timeout)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] != 1:
            raise Exception("Transaction failed")

        # Extract token ID from logs
        # The mint function returns the token ID, we can parse it from logs
        # For now, we'll track this manually in the database
        # A proper implementation would parse the CredentialMinted event

        # Parse logs to get token ID
        token_id = None
        for log in receipt['logs']:
            try:
                if log['address'].lower() == self.contract_address.lower():
                    # This is a Transfer event from minting (from address(0))
                    # Token ID is in the third topic (indexed parameter)
                    if len(log['topics']) >= 3:
                        token_id = int(log['topics'][3].hex(), 16)
                        break
            except Exception as e:
                current_app.logger.warning(f"Error parsing log: {str(e)}")
                continue

        if token_id is None:
            # Fallback: query the contract for the last token
            # This is not ideal but works for testing
            current_app.logger.warning("Could not parse token ID from logs, using fallback")
            token_id = 0  # Will be updated manually

        return token_id, tx_hash.hex()

    def verify_credential(self, token_id):
        """
        Verify a credential on-chain

        Args:
            token_id: NFT token ID

        Returns:
            dict: Credential verification data
        """
        if not self.w3 or not self.contract:
            self.initialize()

        try:
            owner = self.contract.functions.ownerOf(token_id).call()
            token_uri = self.contract.functions.tokenURI(token_id).call()
            is_revoked = self.contract.functions.isRevoked(token_id).call()

            return {
                'exists': True,
                'owner': owner,
                'token_uri': token_uri,
                'is_revoked': is_revoked,
                'token_id': token_id
            }
        except Exception as e:
            current_app.logger.error(f"Error verifying credential: {str(e)}")
            return {
                'exists': False,
                'error': str(e)
            }

    def get_balance(self, address):
        """Get ETH balance of an address"""
        if not self.w3:
            self.initialize()

        balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return self.w3.from_wei(balance_wei, 'ether')