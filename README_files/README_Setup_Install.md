# Setup and Installation Guide

## SECURITY MUST HAVE
1. Create the Streamlit Secrets Directory and file: 
   ```bash
   mkdir -p .streamlit
   ```
2. Create ```.streamlit/secrets.toml```
```bash
    # IBM Quantum API Token
    YOUR_TOKEN = "your-ibm-quantum-api-token-here"

    # Optional: MongoDB URI for production
    MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

## Prerequisites

Before installing the Quantum Compression and Performance Prediction Platform, ensure you have the following:

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11 | Core runtime |
| **MongoDB** | 5.0+ (local) or Atlas account | Database |
| **Git** | Latest | Version control |
| **pip** | Latest | Package management |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 2 GB free | 5 GB free |
| **CPU** | 2 cores | 4 cores+ |
| **Internet** | Broadband (for IBM API) | High-speed |

### Accounts Needed

1. **IBM Quantum Account** - Get your API token from [IBM Quantum Platform](https://quantum.ibm.com/)
2. **MongoDB Atlas** (optional) - For cloud deployment from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

---

## Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the project
git clone https://github.com/your-username/quantum-compression-platform.git

# Navigate to project directory
cd quantum-compression-platform
```

### Step 2: Setup Python Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure MongoDB

#### FOR Local MongoDB Installation

**Windows:**
1. Download MongoDB Community Edition from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
2. Install with default settings
3. Start MongoDB service in cmd: ( do this before running the backend)
   
```bash
mongod
```

#### FOR Cloud MongoDB Installation (STILL BEING TESTED)

1. Create account at MongoDB Atlas
2. Create a new cluster (free tier is M0, with 512MB free)
3. Get connection string
   1. Connect -> connect your application
   2. Copy the connection string: 
      1. ```mongodb+srv://<username>:<password>@cluster.mongodb.net/```
   3. Add IP address to the network list
   
### Step 5: Configure Database Connection
**Edit dbConnection.py**
**FOR LOCAL MongoDB**
```bash
from pymongo import MongoClient

client = MongoClient(
    host="127.0.0.1",
    port=27017,
    # Comment these if no authentication is set up
    # username="your_username",  
    # password="your_password",
    # authSource="admin"
)

db = client["QAdapt_DB"]
```

**FOR MongoDB Atlas**
```bash
import os
from pymongo import MongoClient

# Use environment variable for security
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/")

client = MongoClient(MONGODB_URI)
db = client["QAdapt_DB"]
```
