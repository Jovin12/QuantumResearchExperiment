# 🚀 Step-by-Step Launch Guide

---

### STEP 0: Activate Virtual Environment
I personally go through Anaconda Navigator, but this is the python version of doing it

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```


## Step 1: Start MongoDB

Choose the command for your operating system:

### Windows (Command Prompt as Administrator)
```bash
mongod
```

### Windows (PowerShell as Administrator)
```powershell
mongod
```

### Verify MongoDB is Running

The easiest way is to get Mongodb Compampass installed, and then just connect to the db that way, but if you dont want to do it. 

```bash

sc query MongoDB                   # Windows

# Test connection
mongosh --eval "db.runCommand({ping: 1})"
```
---

## Step 2: Start FastAPI Backend

Open a new terminal window and navigate to your project directory:

```bash
cd /path/to/backend_fastAPI/
fastapi run backend.py
```

### Verify Backend is Running

Open your browser and go to:

http://localhost:8000/docs

You should see:
- FastAPI Swagger UI documentation
- All API endpoints listed



### Optional: Test with curl

```bash
curl http://127.0.0.1:8000/docs
```

---



## Step 3: Start Streamlit Frontend

Open another terminal window (keep backend running) and navigate to your project directory:

```bash
cd /path/to/QuantumResearchExperiment
```

### Start the Streamlit App

```bash
streamlit run run_frontend.py
```

<!-- ### Command Breakdown -->
<!-- 
| Parameter              | Description |
|------------------------|------------|
| `run_frontend.py`      | Main Streamlit application file |
| `--server.port 8501`   | (Optional) Change default port |
| `--server.address 127.0.0.1` | (Optional) Bind to specific address | -->

### Expected Output

```text
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501  
Network URL: http://192.168.1.100:8501  

For better performance, install the Watchdog module:
$ pip install watchdog
```

---

## Access the App

Go to:

http://localhost:8501


EXAMPLE OUTPUT: 
┌─────────────────────────────────────────────────────────────────┐
│  Terminal 1: MongoDB Logs (Optional)                            │
│  $ mongod --dbpath /data/db                                     │
│  [initandlisten] waiting for connections on port 27017          │
├─────────────────────────────────────────────────────────────────┤
│  Terminal 2: FastAPI Backend                                    │
│  $ cd project                                                   │
│  $ source venv/bin/activate                                     │
│  $ uvicorn backend:app --reload                                 │
│  INFO: Uvicorn running on http://127.0.0.1:8000                 │
│  INFO: Application startup complete.                            │
├─────────────────────────────────────────────────────────────────┤
│  Terminal 3: Streamlit Frontend                                 │
│  $ cd project                                                   │
│  $ source venv/bin/activate                                     │
│  $ streamlit run run_frontend.py                                │
│  You can now view your Streamlit app in your browser.           │
│  Local URL: http://localhost:8501                               │
└─────────────────────────────────────────────────────────────────┘