# CampusCred NFT System

A blockchain-based credential verification system for educational institutions, built with Flask (backend), Hardhat (smart contracts), and modern web technologies (frontend).

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Smart Contract Deployment](#smart-contract-deployment)
- [Contributing](#contributing)

---

## 🎯 Overview

CampusCred enables educational institutions to issue verifiable digital credentials as NFTs on the Ethereum blockchain. The system provides:

- **Student Portal**: Submit credential claims with supporting evidence
- **Instructor Dashboard**: Review and approve/reject credential claims
- **Verification System**: Public verification of issued credentials (coming in Sprint 2)
- **Blockchain Integration**: NFT minting for approved credentials (coming in Sprint 2)

**Current Status**: Sprint 1 Complete (Skeletal System Ready for Nov 8 Delivery)

---

## 📁 Project Structure

```
campuscred-nft-system/
├── backend/                    # Flask backend application
│   ├── app/
│   │   ├── models.py          # Database models
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── templates/         # HTML templates
│   ├── tests/                 # Unit tests (25 tests)
│   ├── instance/              # Local database (not in git)
│   ├── venv/                  # Python virtual environment (not in git)
│   ├── requirements.txt       # Python dependencies
│   └── run.py                 # Application entry point
├── frontend/                   # Static assets
│   └── static/
│       ├── css/               # Stylesheets
│       └── js/                # JavaScript files
├── contracts/                  # Solidity smart contracts
├── ignition/                   # Hardhat deployment modules
├── test/                       # Smart contract tests
└── hardhat.config.ts          # Hardhat configuration
```

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads))

Verify installations:

```bash
python3 --version   # Should show 3.12+
node --version      # Should show v18+
npm --version       # Should show 9+
git --version       # Should show 2.0+
```

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd campuscred-nft-system
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate          # On macOS/Linux
# venv\Scripts\activate           # On Windows

# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env

# Initialize database
python setup_database.py
```

**Expected output:**
```
Creating database tables...
Database created successfully!
Tables: claims

Setup complete! You can now run: python run.py
```

### Step 3: Smart Contract Setup

```bash
# Return to project root
cd ..

# Install Node.js dependencies
npm install
```

---

## 🏃 Running the Application

### Backend (Flask)

```bash
# Ensure you're in the backend directory with venv activated
cd backend
source venv/bin/activate

# Start Flask development server
python run.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Access the application:**
- Homepage: http://localhost:5000
- Student Portal: http://localhost:5000/student/portal
- Instructor Dashboard: http://localhost:5000/instructor/dashboard

### Smart Contracts (Hardhat)

```bash
# From project root
npx hardhat test                    # Run smart contract tests
npx hardhat node                    # Start local blockchain
```

---

## 🧪 Testing

### Backend Tests

```bash
# Navigate to backend
cd backend
source venv/bin/activate

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_models.py

# Run with coverage report
python -m pytest --cov=app --cov-report=html
```

**Test Coverage:**
- ✅ 25 unit tests covering models, routes, and services
- ✅ Student submission flow
- ✅ Instructor approval/rejection logic
- ✅ File storage and hashing
- ✅ Database operations

### Smart Contract Tests

```bash
# From project root
npx hardhat test                    # All tests
npx hardhat test solidity           # Solidity tests only
npx hardhat test mocha             # TypeScript tests only
```

---

## 👨‍💻 Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull

# 2. Activate virtual environment
cd backend
source venv/bin/activate

# 3. Start development server
python run.py
```

### After Pulling New Code

If database models have changed:

```bash
# Recreate database
rm instance/campuscred.db
python setup_database.py

# Restart application
python run.py
```

### Adding New Dependencies

**Python (Backend):**
```bash
pip install <package-name>
pip freeze > requirements.txt    # Update requirements
```

**Node.js (Smart Contracts):**
```bash
npm install <package-name>
```

---

## 🔐 Smart Contract Deployment

### Deploy to Local Network

```bash
# Terminal 1: Start local blockchain
npx hardhat node

# Terminal 2: Deploy contracts
npx hardhat ignition deploy ignition/modules/Counter.ts
```

### Deploy to Sepolia Testnet

```bash
# Set private key
npx hardhat keystore set SEPOLIA_PRIVATE_KEY

# Deploy
npx hardhat ignition deploy --network sepolia ignition/modules/Counter.ts
```

---

## 📊 Database Management

### View Database Contents

```bash
cd backend
sqlite3 instance/campuscred.db

# Inside SQLite shell:
.tables                             # List tables
SELECT * FROM claims;               # View all claims
SELECT * FROM claims WHERE status='pending';  # Filter by status
.quit                               # Exit
```

### Reset Database

```bash
cd backend
rm instance/campuscred.db
python setup_database.py
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

**Solution:** Ensure virtual environment is activated
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Port 5000 is already in use"

**Solution:** Kill the process or change port
```bash
# Kill process on port 5000 (macOS/Linux)
lsof -ti:5000 | xargs kill -9

# Or change port in .env
echo "PORT=5001" >> .env
```

### "Database is locked"

**Solution:** Stop Flask first, then access database
```bash
# Stop Flask (Ctrl+C)
# Then access database
```

### Tests failing with import errors

**Solution:** Use `python -m pytest` instead of `pytest`
```bash
python -m pytest -v
```

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Ethers.js Documentation](https://docs.ethers.org/)

---

## 👥 Team

**Group 10 - Fall 2025**
- Technical University of Denmark (DTU)
- Course: Software Processes and Patterns (02369)

---

## 📝 License

This project is part of academic coursework at DTU.

---

**Last Updated:** November 4, 2025