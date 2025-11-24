# CampusCred NFT System

A blockchain-based credential verification system for educational institutions, built with Flask (backend), Hardhat (smart contracts), and a small vanilla JS frontend.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [End-to-End Demo Flow](#end-to-end-demo-flow)
- [Testing](#testing)
- [Smart Contract & Blockchain](#smart-contract--blockchain)
- [Selective Disclosure & Evidence Signing](#selective-disclosure--evidence-signing)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)
- [Team](#team)
- [License](#license)

---

## 🎯 Overview

CampusCred enables educational institutions to issue **verifiable digital credentials as non-transferable NFTs** on the Ethereum Sepolia testnet.

The system includes:

- **Student Portal**
  - Submit credential claims (micro-credential, course completion, diploma)
  - Upload supporting evidence (PDF / images / docs)
  - Evidence stored privately (local or S3), with a **SHA-256 hash** for integrity

- **Instructor Dashboard**
  - Review and approve or reject pending claims
  - On approval, automatically:
    - Upload credential metadata to IPFS (via Pinata, or a deterministic mock hash if not configured)
    - Mint a **non-transferable CampusCred NFT** to the student’s wallet
  - Track statistics: total claims, pending, approved, minted

- **Verification System (No Wallet Required)**
  - Public page to verify credentials by **Token ID**
  - Shows issuer, course, credential type, issuance date, on-chain transaction and metadata
  - Uses on-chain data (`ownerOf`, `tokenURI`, `isRevoked`) plus local DB

- **Selective PII Disclosure**
  - Credential owner can generate a **time-limited verifier link (15 minutes)**  
  - Recruiter following this link can:
    - See legal name, email, and evidence file name
    - Download a **digitally signed PDF** of the evidence (if evidence is a PDF)

- **Blockchain Integration**
  - Solidity smart contract `CampusCredNFT` (non-transferable ERC-721)
  - Deployed to **Sepolia** (see `DEPLOYMENT.txt`)
  - Minting performed from a backend-controlled deployer wallet

**Current Status (Nov 2025)**  
End-to-end prototype is implemented:

- ✅ Student submission with file upload & private storage  
- ✅ Instructor approval & NFT minting on Sepolia  
- ✅ Public verification by token ID (no wallet required)  
- ✅ Time-limited verifier links for PII + signed PDF download  
- ✅ Hardhat-based contract deployment & tests

---

## 📁 Project Structure

    campuscred-nft-system/
    ├── DEPLOYMENT.txt              # Sepolia deployment info (address, date)
    ├── README.md                   # This file
    ├── backend/                    # Flask backend
    │   ├── app/
    │   │   ├── __init__.py         # Flask app factory
    │   │   ├── config.py           # Configuration loader (env-based)
    │   │   ├── models.py           # SQLAlchemy models (Claim)
    │   │   ├── routes/             # Blueprints
    │   │   │   ├── home.py         # Landing/about
    │   │   │   ├── auth.py         # Wallet-connect session & instructor auth
    │   │   │   ├── claims.py       # Student portal & submission
    │   │   │   ├── instructor.py   # Approve/reject/mint
    │   │   │   └── verify.py       # Public verify + verifier links + downloads
    │   │   ├── services/
    │   │   │   ├── storage.py      # Local + S3-compatible private storage
    │   │   │   ├── blockchain.py   # Web3 integration & minting
    │   │   │   ├── ipfs.py         # Pinata/IPFS integration
    │   │   │   └── pdf_signer.py   # PDF signing for evidence downloads
    │   │   └── templates/          # HTML (Jinja) templates
    │   ├── tests/                  # Backend tests (pytest)
    │   ├── .env.example            # Backend environment template
    │   ├── requirements.txt        # Python dependencies
    │   ├── run.py                  # Flask entry point
    │   └── setup_database.py       # DB initialisation helper
    ├── frontend/
    │   └── static/
    │       ├── css/style.css       # Theme, student/instructor/verify styling
    │       ├── js/main.js          # Theme toggle + wallet connect + toasts
    │       └── images/dtu-1.svg    # DTU / CampusCred logo
    ├── contracts/
    │   ├── CampusCredNFT.sol       # Solidity credential NFT contract
    │   └── CampusCredNFT_ABI.json  # ABI exported for backend Web3
    ├── test/
    │   └── CampusCredNFT.test.js   # Hardhat/Mocha tests for the contract
    ├── ignition/                   # Hardhat Ignition deployment modules
    ├── scripts/                    # Hardhat helper scripts (deploy, export ABI)
    ├── hardhat.config.ts           # Hardhat 3 configuration (TypeScript)
    ├── package.json                # Node/Hardhat dev dependencies
    └── types/ethers-contracts/     # Typechain-generated contract types

---

## ✨ Features

### Student

- Submit claims with:
  - Name, email, course code, type (micro-credential / course completion / diploma)
  - Optional description and course name
  - Optional evidence file (PDF, PNG, JPG, DOC, DOCX, TXT,…)
- Evidence stored privately (not on-chain, not on IPFS)
- File hash (SHA-256) computed and stored on the claim for integrity
- When approved & minted:
  - See Token ID, status, and links to verification + Etherscan
  - Can copy a public verification link from the Student Portal

### Instructor

- Connect instructor wallet via MetaMask (pre-configured instructor address)
- View **pending** claims, drill into details, approve or reject:
  - Approve → attempts NFT mint on Sepolia
  - Reject → set status to `denied` with an instructor-provided reason
- Quick stats: total claims, pending, recent approved, recent minted

### Verifier / Recruiter

- Public page `/verify/`:
  - Enter Token ID to see:
    - Credential type, course code, description
    - Issuer and issuance date
    - Owner address
    - Transaction hash & Etherscan link (if available)
    - Metadata URI (IPFS)
    - Evidence hash (SHA-256) to verify underlying evidence file
- If given a **verifier link** (e.g. `/verify/private/<token>`):
  - During the 15-minute window:
    - See legal name and email
    - See evidence file name & hash
    - Download signed PDF evidence (if applicable)

---

## ⚙️ Prerequisites

Make sure you have:

- **Python 3.12+**
- **Node.js 18+** and **npm 9+**
- **Git**
- (Optional) **MetaMask** in your browser for local testing of wallet flows

Check:

    python3 --version   # 3.12+
    node --version      # 18+
    npm --version       # 9+
    git --version       # recent 2.x

---

## 🚀 Installation

### 1. Clone the Repository

    git clone <repository-url>
    cd campuscred-nft-system

### 2. Backend Setup

    cd backend

    # Create virtual environment
    python3 -m venv venv

    # Activate it
    source venv/bin/activate          # macOS/Linux
    # venv\Scripts\activate           # Windows

    # Install dependencies
    pip install -r requirements.txt

    # Create .env from template
    cp .env.example .env

    # Initialize database
    python setup_database.py

Expected output:

    Creating database tables...
    Database created successfully!
    Tables: claims

    Setup complete! You can now run: python run.py

### 3. Smart Contract / Node Setup

From the project root:

    # Install Node dev dependencies for Hardhat & contracts
    npm install

---

## 🏃 Running the Application

### Backend (Flask API + HTML UI)

From `backend/` with your virtualenv activated:

    cd backend
    source venv/bin/activate          # if not already
    python run.py

You should see something like:

    * Running on http://127.0.0.1:5000
    * Debug mode: on

Navigate to:

- Home / Landing: `http://localhost:5000/`
- Student Portal: `http://localhost:5000/student/portal`
- Instructor Dashboard: `http://localhost:5000/instructor/dashboard`
- Verify: `http://localhost:5000/verify/`

> **Note:** Instructor actions (approve/reject/mint) require connecting with the designated instructor wallet (hard-coded in `auth.py`).

### Smart Contracts (Hardhat)

From project root:

    # Compile and run contract tests
    npx hardhat test

    # Start a local dev chain (if you want to experiment)
    npx hardhat node

---

## 🧩 End-to-End Demo Flow

Here’s a quick walkthrough of the full flow:

1. **Student submits a claim**
   - Go to `/student/portal`
   - Fill in name, email, credential type, course code, optional description
   - Optionally upload a PDF (transcript, certificate, etc.)
   - Submit → you get a success flash with a tracking ID

2. **Connect as Instructor**
   - In your browser (with MetaMask), click **“Connect Wallet”**
   - Use the pre-configured instructor wallet (see comment in `auth.py`)
   - You’ll be redirected to `/instructor/dashboard`

3. **Instructor approves and mints**
   - In the dashboard, find the pending claim
   - Click ✅ to approve
   - Backend:
     - Builds JSON metadata
     - Uploads to IPFS via Pinata (or returns a mock `ipfs://` URI if no Pinata keys)
     - Mints a non-transferable NFT to the student’s wallet
   - Claim status becomes `minted` and includes `token_id`, `metadata_uri`, `transaction_hash`

4. **Public verification**
   - Go to `/verify/`
   - Enter the Token ID you saw in the portal
   - See credential details + blockchain provenance, without logging in or connecting a wallet

5. **Selective PII sharing**
   - As the student, go to the Student Portal → **Minted** tab
   - Copy the verification link or open in new tab
   - On the verify page for that token, click **Generate Verifier Link**
   - This:
     - Checks that your wallet address matches the credential owner
     - Generates a time-limited URL (15 minutes)
   - Share that URL with a recruiter:
     - They see your name, email, and evidence filename
     - They can download a digitally signed PDF of the evidence

---

## 🧪 Testing

### Backend Tests

From `backend/`:

    cd backend
    source venv/bin/activate

    # Run all tests
    python -m pytest

    # Verbose
    python -m pytest -v

    # Specific test file
    python -m pytest tests/test_models.py

    # Coverage
    python -m pytest --cov=app --cov-report=html

Current backend tests cover (non-exhaustive):

- App factory + blueprint registration
- Home and basic pages (`/`, `/about`, `/verify/`, `/auth/test-html`)
- Student submission:
  - Validation errors
  - Successful claim creation
  - File upload + hash calculation
- Storage service:
  - Allowed file types
  - Local file existence + deletion
- Instructor dashboard:
  - Dashboard load and statistics
  - Fetch claim details
  - Approve & reject flows and DB side-effects
- Claim model:
  - Defaults, status workflow, hash computation

Open `htmlcov/index.html` to inspect per-file coverage.

### Smart Contract Tests

From project root:

    # All Solidity tests (Hardhat + Mocha + Ethers)
    npx hardhat test

`test/CampusCredNFT.test.js` verifies:

- Minting a credential (token 0 owned by student)
- Transfers are blocked (non-transferable design)
- `revoke` marks a credential as revoked

---

## 🔐 Smart Contract & Blockchain

### Contract

- **Name:** CampusCred  
- **Symbol:** CCRED  
- **File:** `contracts/CampusCredNFT.sol`
- **Key properties:**
  - Non-transferable ERC-721 (only mint & burn-like revoke, no transfers)
  - `MINTER_ROLE` for minting, `DEFAULT_ADMIN_ROLE` for revocation
  - `CredentialMinted` and `CredentialRevoked` events
  - Mapping of `tokenId → tokenURI` and `tokenId → isRevoked`

### Deployment (Sepolia)

See `DEPLOYMENT.txt` for the most recent Sepolia deployment address.

To (re-)deploy with Hardhat:

    # Compile
    npx hardhat compile

    # Deploy via simple script (Node ESM)
    npx hardhat run scripts/deploy.js --network sepolia

Make sure your `.env` (for Hardhat) defines:

    SEPOLIA_RPC_URL=<Alchemy-or-Infura-URL>
    SEPOLIA_PRIVATE_KEY=<deployer-private-key>

Backend `.env` (see `.env.example`) should set:

    CONTRACT_ADDRESS=<deployed-campuscred-address>
    SEPOLIA_RPC_URL=<same as above>
    DEPLOYER_PRIVATE_KEY=<same private key without 0x>
    PINATA_API_KEY=...               # optional; enables real IPFS uploads
    PINATA_SECRET_API_KEY=...

---

## 🔏 Selective Disclosure & Evidence Signing

### Verifier Links

- Backend stores time-limited verifier tokens in memory (for the demo):
  - Generated only by the credential owner (wallet match enforced)
  - Valid for 15 minutes by default
- Route summary:
  - `POST /verify/generate-verifier-link/<token_id>` → JSON with `verifier_url` & `expires_in`
  - `GET /verify/private/<verifier_token>` → HTML view with PII

### Evidence Download & PDF Signing

- Evidence is retrieved from:
  - Local disk (`app/private_storage`) **or**
  - S3-compatible object storage (if `AWS_*` env vars are configured)
- If the evidence filename ends with `.pdf`:
  - `PDFSignerService` signs the document using a self-signed certificate
  - The signed file is streamed to the verifier as a download
- Route:
  - `GET /verify/download-evidence/<verifier_token>`

> **Note:** The PDF signing keys are generated on first use and stored in `app/private_storage/` (or paths overridden via env). For production, you would replace this with institutional keys.

---

## 👨‍💻 Development Workflow

### Daily Development

    # Get latest code
    git pull

    # Backend
    cd backend
    source venv/bin/activate
    python run.py

### When Models Change

If you change `Claim` or add models:

    cd backend
    rm -f instance/campuscred.db
    python setup_database.py
    python run.py

### Adding New Dependencies

**Python:**

    pip install <package>
    pip freeze > requirements.txt

**Node:**

    npm install <package> --save-dev

---

## 🐛 Troubleshooting

### “ModuleNotFoundError: No module named 'flask'”

Your virtualenv is probably not active:

    cd backend
    source venv/bin/activate
    pip install -r requirements.txt

### “Port 5000 is already in use”

Kill the process or change port:

    # macOS/Linux
    lsof -ti:5000 | xargs kill -9

    # Or in backend/.env
    echo "PORT=5001" >> .env

### “Database is locked”

Stop Flask (Ctrl+C) before opening the SQLite DB manually.

### Tests failing with import errors

Use `python -m pytest` (as configured in `conftest.py`), not plain `pytest`:

    python -m pytest -v

### Cannot connect to Sepolia / mint fails

- Check `SEPOLIA_RPC_URL` in backend `.env`
- Check `DEPLOYER_PRIVATE_KEY` is set **without** `0x`
- Check that the deployer address has `MINTER_ROLE` on the contract and some test ETH

If minting fails, the claim still becomes `approved` and the instructor sees a message that minting will be retried / handled later.

---

## 📚 Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Hardhat Documentation: https://hardhat.org/docs
- Ethers.js: https://docs.ethers.org/
- Pinata (IPFS pinning): https://www.pinata.cloud/

---

## 👥 Team

**Group 10 – Fall 2025**  
Technical University of Denmark (DTU)  
Course: Software Processes and Patterns (02369)

This system is a **prototype** for educational purposes and does not represent an official DTU credentialing system.

---

## 📝 License

This project is part of academic coursework at DTU.  
Usage is limited to educational and demonstration purposes.