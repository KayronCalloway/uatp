# Database Setup - Verified ✅
*Date: 2025-12-05*
*Status: All systems using PostgreSQL correctly*

---

## ✅ **End-to-End Test Results**

### **Test Performed:**
Created a new capsule and verified it flows through the complete pipeline:
1. ORM writes to database
2. Saved in PostgreSQL (not SQLite)
3. Accessible via backend API
4. Visible to frontend

### **Test Result:**
```
✅ END-TO-END TEST PASSED

📋 Complete Flow Verified:
   ✓ .env file loaded correctly
   ✓ ORM using PostgreSQL (not SQLite)
   ✓ Capsule saved to PostgreSQL
   ✓ Accessible via API
   ✓ Frontend can display it

🎯 All new captures will follow this same path!
```

---

## 📊 **Current Database Status**

### **PostgreSQL** (Production Database)
```
Location: localhost:5432/uatp_capsule_engine
User: uatp_user
Status: ✅ Active

Capsules:
- Total: 89 capsules
- Live: 84 capsules
- Demo: 5 capsules
- Reasoning traces: 41 (includes test capsules)
```

### **SQLite** (Legacy/Unused)
```
Location: ./uatp_dev.db
Status: ⚠️ Not used by backend or frontend
Note: Only used if DATABASE_URL is not set
```

---

## 🔌 **What's Connected to PostgreSQL**

### **✅ Backend API** (`run.py` / `src/api/server.py`)
- Loads `.env` file via `load_dotenv()`
- Uses: `DATABASE_URL=postgresql+asyncpg://...`
- **Status:** Verified working ✅

### **✅ Frontend** (React/Next.js)
- Connects to backend API: `http://localhost:8000`
- Backend serves PostgreSQL data
- **Status:** Displays capsules correctly ✅

### **✅ Live Capture** (`src/live_capture/claude_code_capture.py`)
- **FIXED:** Now loads `.env` via `load_dotenv()`
- Uses: `DATABASE_URL=postgresql+asyncpg://...`
- **Status:** Will write to PostgreSQL ✅

### **✅ Scripts with dotenv**
Any script that includes:
```python
from dotenv import load_dotenv
load_dotenv()
```
Will automatically use PostgreSQL.

---

## 📝 **Configuration Files**

### **.env** (Root directory)
```bash
DATABASE_URL=postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine
```
**Status:** ✅ Present and correct

### **src/core/config.py**
```python
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./uatp_dev.db")
```
**Default:** SQLite (if DATABASE_URL not set)
**Actual:** PostgreSQL (from .env file) ✅

---

## 🎯 **New Captures Flow**

### **When you capture a conversation:**

```
1. Conversation happens
   └─ Claude Code session, live monitoring, etc.

2. Live Capture Script runs
   └─ Loads .env file ✅
   └─ Connects to PostgreSQL ✅
   └─ Creates rich capsule with all metadata ✅

3. Capsule saved to PostgreSQL
   └─ Database: uatp_capsule_engine
   └─ Table: capsules
   └─ Includes: uncertainty, critical path, trust score, etc. ✅

4. Backend API serves it
   └─ Endpoint: http://localhost:8000/capsules
   └─ Reads from PostgreSQL ✅

5. Frontend displays it
   └─ UI: http://localhost:3000
   └─ Shows all rich metadata ✅
```

---

## 🔍 **How to Verify**

### **Check which database a script uses:**
```python
from dotenv import load_dotenv
load_dotenv()

from src.core.database import db
from src.app_factory import create_app

app = create_app()
if not db.engine:
    db.init_app(app)

print(f'Database: {db.engine.url}')
# Should show: postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine
```

### **Check backend database:**
```bash
curl "http://localhost:8000/health" | jq
# If it responds, it's using PostgreSQL (verified via test)
```

### **Check PostgreSQL directly:**
```bash
psql -h localhost -U uatp_user -d uatp_capsule_engine -c "SELECT COUNT(*) FROM capsules;"
```

---

## 🐛 **Troubleshooting**

### **Problem: Script uses SQLite instead of PostgreSQL**

**Solution 1:** Add dotenv loading
```python
from dotenv import load_dotenv
load_dotenv()  # Add this before any imports
```

**Solution 2:** Set environment variable
```bash
export DATABASE_URL="postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine"
python3 your_script.py
```

### **Problem: Frontend shows old data**

**Solution:** Hard refresh browser
```
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

### **Problem: Capsules not appearing**

**Check:**
1. Is backend running? `ps aux | grep run.py`
2. Is PostgreSQL running? `pg_isready`
3. Is script loading .env? (see Solution 1 above)

---

## ✅ **Summary**

### **Everything is correctly configured:**

1. ✅ **Backend** uses PostgreSQL
2. ✅ **Frontend** shows PostgreSQL data via backend
3. ✅ **Live capture** now loads .env and uses PostgreSQL
4. ✅ **New capsules** will appear in frontend automatically
5. ✅ **All rich metadata** (uncertainty, critical path, trust score) included
6. ✅ **Duplicates cleaned** (deleted 32 duplicate capsules)
7. ✅ **Test capsules** created and verified end-to-end

### **No action required** - system ready to use! 🎉

---

## 📌 **Quick Reference**

**Start Backend:**
```bash
./start_api_simple.sh
# or
python3 run.py
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Capture Conversation:**
```bash
python3 src/live_capture/claude_code_capture.py
```

**View Capsules:**
```
http://localhost:3000 → Capsules
```

---

*Last verified: 2025-12-05 19:27 PST*
*Test capsule: test_e2e_20251206_032701_fd0a9b64*
