# CampusCred NFT System

A blockchain-based credential verification system for educational institutions, built with Flask (backend), Hardhat (smart contracts), and a small vanilla JS frontend.

## 📋 Table of Contents

- [Overview](#-overview)
- [Project Structure](#-project-structure)
- [Features](#-features)
- [Prerequisites](#️-prerequisites)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [End-to-End Demo Flow](#-end-to-end-demo-flow)
- [Testing](#-testing)
- [Smart Contract & Blockchain](#-smart-contract--blockchain)
- [Selective Disclosure & Evidence Signing](#-selective-disclosure--evidence-signing)
- [Troubleshooting](#-troubleshooting)
- [Team](#-team)
- [License](#-license)

## 🎯 Overview

CampusCred enables educational institutions to issue verifiable digital credentials as non-transferable NFTs on the Ethereum Sepolia testnet.

The system includes:

### Student Portal
- Submit credential claims (micro-credential, course completion, diploma)
- Upload supporting evidence (PDF / images / docs)
- Evidence stored privately (local or S3), with a SHA-256 hash for integrity

### Instructor Dashboard
- Review and approve or reject pending claims
- On approval, automatically:
  - Upload credential metadata to IPFS (via Pinata, or a deterministic mock hash if not configured)
  - Mint a non-transferable CampusCred NFT to the student's wallet
- Track statistics: total claims, pending, approved, minted

### Verification System (No Wallet Required)
- Public page to verify credentials by Token ID
- Shows issuer, course, credential type, issuance date, on-chain transaction and metadata
- Uses on-chain data (ownerOf, tokenURI, isRevoked) plus local DB

### Selective PII Disclosure
- Credential owner can generate a time-limited verifier link (15 minutes)
- Recruiter following this link can:
  - See legal name, email, and evidence file name
  - Download a digitally signed PDF of the evidence (if evidence is a PDF)

### Blockchain Integration
- Solidity smart contract CampusCredNFT (non-transferable ERC-721)
- Deployed to Sepolia (see DEPLOYMENT.txt)
- Minting performed from a backend-controlled deployer wallet

### Current Status (Final Prototype)

End-to-end prototype is fully implemented:

- ✅ Student submission with file upload & private storage
- ✅ Instructor approval & NFT minting on Sepolia
- ✅ Public verification by token ID (no wallet required)
- ✅ Time-limited verifier links for PII + signed PDF download
- ✅ Hardhat-based contract deployment & tests
- ✅ Full E2E Browser Testing with mocked MetaMask injection

## 📁 Project Structure
```
campuscred-nft-system/
├── DEPLOYMENT.txt              # Sepolia deployment info (address, date)
├── README.md                   # This file
├── backend/                    # Flask backend
│   ├── app/
│   │   ├── __init__.py         # Flask app factory
│   │   ├── config.py           # Configuration loader (env-based)
│   │   ├── models.py           # SQLAlchemy models (Claim)
│   │   ├── routes/             # Blueprints (auth, claims, instructor, verify)
│   │   └── services/           # Logic (blockchain, storage, ipfs, signer)
│   ├── e2e/                    # End-to-End Playwright Tests
│   │   ├── __init__.py
│   │   ├── conftest.py         # Live server fixture & blockchain mocks
│   │   ├── mocks.py            # Window.ethereum injection
│   │   └── test_full_flow.py   # Full critical path tests
│   ├── tests/                  # Backend Unit tests (pytest)
│   ├── .env.example            # Backend environment template
│   ├── requirements.txt        # Python dependencies
│   ├── run.py                  # Flask entry point
│   └── setup_database.py       # DB initialisation helper
├── frontend/
│   └── static/                 # CSS, JS, and Images
├── contracts/
│   ├── CampusCredNFT.sol       # Solidity credential NFT contract
│   └── CampusCredNFT_ABI.json  # ABI exported for backend Web3
├── test/
│   └── CampusCredNFT.test.js   # Hardhat/Mocha tests for the contract
├── ignition/                   # Hardhat Ignition deployment modules
├── scripts/                    # Hardhat helper scripts (deploy, export ABI)
├── hardhat.config.ts           # Hardhat 3 configuration (TypeScript)
└── package.json                # Node/Hardhat dev dependencies
```

## ✨ Features

### Student
- Submit claims with name, email, course code, and credential type.
- Securely upload evidence files (stored off-chain).
- Connect wallet via MetaMask to associate credentials with Ethereum address.
- View status of submitted claims (Pending, Approved, Minted).

### Instructor
- Authenticated via specific instructor wallet address.
- Dashboard view of all pending claims.
- Approve claims → Triggers metadata generation, IPFS pin, and Blockchain mint.
- Reject claims → Records reason and notifies student.

### Verifier / Recruiter
- **Public Verify:** Enter Token ID to view immutable blockchain record (Issuer, Date, Course).
- **Private Link:** Credential owner generates a 15-minute link. Verifier can download digitally signed evidence and view PII (Name/Email).

## ⚙️ Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- MetaMask (for manual testing)
- Playwright Browsers (for E2E testing)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd campuscred-nft-system
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies (Flask, Web3, Playwright)
pip install -r requirements.txt

# Install Playwright browsers for E2E testing
python -m playwright install chromium

# Create .env and initialize DB
cp .env.example .env
python setup_database.py
```

### 3. Smart Contract Setup
```bash
# Install Node dependencies
npm install
```

## 🏃 Running the Application

### Backend (Flask API + HTML UI)
```bash
cd backend
source venv/bin/activate
python run.py
```

Access the app at: http://localhost:5000

### Smart Contracts (Hardhat)
```bash
# Start local node (optional)
npx hardhat node
```

## 🧩 End-to-End Demo Flow

1. **Student:** Go to `/student/portal`. Fill out the form, upload a PDF, and submit.
2. **Instructor:** Connect wallet (use the address in auth.py). Go to `/instructor/dashboard`. Click Approve.
3. **System:** Uploads metadata to IPFS -> Mints NFT on Sepolia -> Updates DB.
4. **Verifier:** Go to `/verify/`, enter Token ID, see valid credential.
5. **Private Share:** Student generates link -> Verifier downloads signed PDF.

## 🧪 Testing

This project employs a "Testing Pyramid" strategy including Unit, Integration, and End-to-End (E2E) Browser tests.

### 1. Backend Unit Tests

Cover models, routes, storage, and services logic using pytest.
```bash
cd backend
python -m pytest tests/
```

### 2. Smart Contract Tests

Cover minting, role-based access control, and revocation using Hardhat/Chai.
```bash
npx hardhat test
```

### 3. End-to-End (E2E) Tests

Cover the full lifecycle (Student -> Instructor -> Verify) using Playwright.

- Runs the Flask server in a background thread using an in-memory DB.
- Launches a headless Chromium browser.
- **Mocks MetaMask:** Injects a fake `window.ethereum` provider so tests can click "Connect Wallet" without a real browser extension.
- **Mocks Blockchain:** Patches `BlockchainService` to simulate minting without waiting for Sepolia confirmation.
```bash
cd backend

# Run in headed mode to see the browser actions
python -m pytest e2e/test_full_flow.py --headed
```

## 🔐 Smart Contract & Blockchain

- **Contract:** `CampusCredNFT.sol` (ERC-721)
- **Network:** Sepolia Testnet

### Features

- `MINTER_ROLE`: Only the backend deployer can mint.
- `revoke()`: Allows the university to invalidate credentials.
- **Non-transferable:** Overrides `_update` to prevent students from selling/transferring credentials (Soulbound).

### Deployment (Sepolia)

To (re-)deploy with Hardhat:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

## 🔏 Selective Disclosure & Evidence Signing

### Verifier Links
- Time-limited tokens (15 mins) stored in backend memory.
- Generated only by the wallet owner of the credential.

### PDF Signing
- `PDFSignerService` generates a self-signed PKI certificate on the fly (stored in `private_storage`).
- When a recruiter downloads evidence via a private link, the PDF is digitally signed to prove it came from the CampusCred system.

## 🐛 Troubleshooting

### "Playwright: Executable doesn't exist"

If E2E tests fail with browser errors, the binary installation might be corrupted. Force a clean reinstall:
```bash
# Delete cache
rm -rf ~/Library/Caches/ms-playwright
# Reinstall via python module
python -m playwright install chromium
```

### "ImportError: cannot import name 'ContractName' from 'eth_typing'"

This is a dependency conflict between web3.py and newer versions of eth-typing. Fix by pinning the version:
```bash
pip install "eth-typing<5.0.0"
```

### "Database is locked"

Ensure you don't have the SQLite file open in a viewer/IDE while running tests or the server.

### "ModuleNotFoundError: No module named 'flask'"

Your virtualenv is not active. Run `source venv/bin/activate`.

## 👥 Team

**Group 10** – Fall 2025 Technical University of Denmark (DTU)

**Course:** Software Processes and Patterns (02369)

> This system is a prototype for educational purposes and does not represent an official DTU credentialing system.

## 📝 License

This project is part of academic coursework at DTU.
Usage is limited to educational and demonstration purposes.