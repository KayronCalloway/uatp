# UATP Quick Start Guide

## 🚀 Starting the System

### One-Command Start
```bash
./start_uatp_system.sh
```

This will:
- Start backend API on port 8000
- Start frontend on port 3000
- Run both in background
- Save logs to `api_server.log` and `frontend.log`

### Manual Start

**Backend:**
```bash
UATP_DEMO_MODE=true python3 -m quart --app src.api.server:app run --host 0.0.0.0 --port 8000 &
```

**Frontend:**
```bash
cd frontend && npm run dev &
```

## 🔍 Checking Status

```bash
./check_uatp_status.sh
```

Shows:
- Backend API status (port 8000)
- Frontend status (port 3000)
- Process IDs
- System health metrics

## 🌐 Accessing the System

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Platforms**: http://localhost:8000/onboarding/api/platforms

## 🛑 Stopping the System

```bash
# Stop both services
pkill -f 'next-server'
pkill -f 'quart.*src.api.server'

# Or individually
kill $(cat api_server.pid)         # Backend
kill $(cat frontend/frontend.pid)  # Frontend
```

## 📊 Viewing Logs

```bash
# Backend logs (live)
tail -f api_server.log

# Frontend logs (live)
tail -f frontend.log

# Last 50 lines
tail -50 api_server.log
tail -50 frontend.log
```

## 🔧 Configuration

### Backend Environment
The backend runs in **Demo Mode** by default:
- `UATP_DEMO_MODE=true` - Uses sample data
- Port: 8000
- Log: `api_server.log`

### Frontend Environment
Configuration in `frontend/.env.local`:
```bash
NEXT_PUBLIC_UATP_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_REAL_API=true
NEXT_PUBLIC_DEBUG_MODE=true
```

## 📚 Documentation

- **System Status**: `SYSTEM_STATUS.md` - Current configuration
- **Technical Debt**: `TECHNICAL_DEBT_ASSESSMENT.md` - Code quality
- **Dependency Injection**: `DEPENDENCY_INJECTION_REFACTORING_COMPLETE.md` - Architecture
- **Session Summary**: `SESSION_SUMMARY_DEPENDENCY_INJECTION.md` - Recent work

## ✅ System Health

**Current Status**: Production-Ready

- **Technical Debt**: ~5% (Excellent)
- **Code Quality**: 0 TODO/FIXME comments
- **Architecture**: SOLID principles throughout
- **Security**: Post-quantum cryptography enabled

### Core Components Status
- ✅ Security Layer: Quantum-resistant
- ✅ Economic Layer: Fair attribution working
- ✅ Governance Layer: DAO functionality operational
- ✅ Ethics Layer: Real-time monitoring active
- ✅ API Layer: REST API functional

## 🆘 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Restart
UATP_DEMO_MODE=true python3 -m quart --app src.api.server:app run --port 8000 &
```

### Frontend Won't Start
```bash
# Check if port 3000 is in use
lsof -ti:3000

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Restart
cd frontend && npm run dev &
```

### API Connection Issues
1. Check backend is running: `curl http://localhost:8000/onboarding/api/platforms`
2. Check frontend .env.local has correct API URL
3. Restart frontend to pick up new environment variables

### View Full Logs
```bash
# Backend full log
cat api_server.log

# Frontend full log
cat frontend.log

# Recent errors only
grep -i error api_server.log | tail -20
```

## 🔄 Restarting Services

```bash
# Restart backend only
pkill -f 'quart.*src.api.server'
UATP_DEMO_MODE=true python3 -m quart --app src.api.server:app run --port 8000 &

# Restart frontend only
cd frontend && pkill next-server
npm run dev &
```

## 📈 Monitoring

```bash
# Watch processes
watch -n 2 'ps aux | grep -E "(next-server|quart)" | grep -v grep'

# Monitor logs in real-time (split screen)
tail -f api_server.log &
tail -f frontend.log &
```

---

*For detailed system architecture, see `SYSTEM_STATUS.md`*
*For technical details, see `TECHNICAL_DEBT_ASSESSMENT.md`*
