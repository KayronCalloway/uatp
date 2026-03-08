# Complete Migration Guide: Transfer to New M5 MacBook (24GB)

## Phase 1: Backup Current System

### 1.1 Save Git Work
```bash
cd ~/uatp-capsule-engine
git status                    # Check for uncommitted changes
git add .
git commit -m "Pre-migration backup - $(date +%Y%m%d)"
git push origin main          # Push to remote (if you have one)
```

### 1.2 Export Critical Data Files
```bash
# Create backup directory
mkdir -p ~/uatp-backup

# Copy data files
cp capsule_chain.jsonl ~/uatp-backup/
cp -r chain_seals ~/uatp-backup/
cp .env ~/uatp-backup/          # Your API keys and secrets
cp .env.example ~/uatp-backup/  # Template reference

# Copy any SQLite databases
cp *.db ~/uatp-backup/ 2>/dev/null || true

# Copy any custom configs
cp config/setup.json ~/uatp-backup/ 2>/dev/null || true
```

### 1.3 Document Current Environment
```bash
# Save installed packages
pip freeze > ~/uatp-backup/requirements-backup.txt
brew list > ~/uatp-backup/brew-packages.txt
npm list -g --depth=0 > ~/uatp-backup/npm-global-packages.txt 2>/dev/null || true

# Save shell config
cp ~/.zshrc ~/uatp-backup/.zshrc-backup 2>/dev/null || true
cp ~/.bash_profile ~/uatp-backup/.bash_profile-backup 2>/dev/null || true

# Save git config
git config --list > ~/uatp-backup/git-config.txt
```

### 1.4 Transfer Backup to New Machine
Options:
- **iCloud Drive**: Copy `~/uatp-backup` to iCloud
- **USB Drive**: Copy to external drive
- **AirDrop**: Transfer directly during setup
- **Migration Assistant**: Will copy everything automatically

---

## Phase 2: New M5 MacBook Initial Setup

### 2.1 macOS System Setup
1. Complete macOS setup wizard
2. Sign into Apple ID
3. Enable iCloud Drive (if using for transfer)
4. System Settings → Software Update (get latest macOS)

### 2.2 Install Xcode Command Line Tools
```bash
xcode-select --install
```
Click "Install" when prompted. This provides Git, make, and other development tools.

### 2.3 Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# IMPORTANT: Add Homebrew to PATH (follow the terminal instructions after install)
# For M5 (Apple Silicon), typically:
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify
brew --version
```

---

## Phase 3: Install Core Development Tools

### 3.1 Install Python 3
```bash
brew install python@3.11
# Or whatever version you're currently using

# Verify
python3 --version
pip3 --version
```

### 3.2 Install Node.js (for frontend)
```bash
brew install node

# Verify
node --version
npm --version
```

### 3.3 Install Git (if not already from Xcode tools)
```bash
brew install git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3.4 Install Docker Desktop (Optional)
Download from: https://www.docker.com/products/docker-desktop/
- Get the **Apple Silicon** version
- Install and start Docker Desktop

---

## Phase 4: Install Claude Code

### 4.1 Install Claude Code via npm
```bash
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version
```

### 4.2 Configure Claude Code
```bash
# Set up API key
claude-code auth login

# Follow prompts to authenticate
```

---

## Phase 5: Set Up UATP Project

### 5.1 Clone or Restore Repository

**Option A: Clone from Remote**
```bash
cd ~
git clone <your-repo-url> uatp-capsule-engine
cd uatp-capsule-engine
```

**Option B: Copy from Backup**
```bash
# If using Migration Assistant or manual backup
cd ~/uatp-capsule-engine
git status  # Should show clean working directory
```

### 5.2 Restore Environment Variables
```bash
# Copy .env from backup
cp ~/uatp-backup/.env ~/uatp-capsule-engine/.env

# Verify it contains your keys
cat .env
# Should show:
# ANTHROPIC_API_KEY=sk-ant-api03-...
# OPENAI_API_KEY=sk-...
# UATP_SIGNING_KEY=...
```

### 5.3 Restore Data Files
```bash
cd ~/uatp-capsule-engine

# Restore main data file
cp ~/uatp-backup/capsule_chain.jsonl .

# Restore chain seals
cp -r ~/uatp-backup/chain_seals .

# Restore any database files
cp ~/uatp-backup/*.db . 2>/dev/null || true
```

### 5.4 Create Python Virtual Environment
```bash
cd ~/uatp-capsule-engine

# Create virtualenv
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# If you have dev dependencies
pip install -r requirements-dev.in 2>/dev/null || true
```

### 5.5 Install Frontend Dependencies (if applicable)
```bash
cd ~/uatp-capsule-engine/frontend
npm install
```

---

## Phase 6: Verify Installation

### 6.1 Test Python Environment
```bash
cd ~/uatp-capsule-engine
source venv/bin/activate

# Test basic imports
python3 -c "
from src.engine.capsule_engine import CapsuleEngine
from src.integrations.anthropic_client import AnthropicClient
print('✓ Core imports working')
"
```

### 6.2 Test API Server
```bash
# Start API server
python3 run.py

# In another terminal, test:
curl http://localhost:8000/health

# Should return: {"status":"ok"}
```

### 6.3 Test Claude Code Integration
```bash
# Run quick test
python3 -c "
import os
print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING')
"
```

### 6.4 Run Test Suite
```bash
# Run basic tests
python3 -m pytest tests/test_capsule_engine.py -v

# Run all tests (optional, may take time)
python3 -m pytest tests/ -v
```

---

## Phase 7: Additional Setup

### 7.1 Install Pre-commit Hooks (if you use them)
```bash
pip install pre-commit
pre-commit install
```

### 7.2 Set Up Auto-Capture (if you use it)
```bash
./manage-auto-capture.sh install
./manage-auto-capture.sh start
```

### 7.3 Restore Shell Customizations
```bash
# If you had custom aliases/functions in .zshrc
cp ~/uatp-backup/.zshrc-backup ~/.zshrc
source ~/.zshrc
```

---

## Quick Reference Commands

### Daily Development
```bash
# Activate Python environment
cd ~/uatp-capsule-engine
source venv/bin/activate

# Start API server
python3 run.py

# Start visualizer
streamlit run visualizer/app.py

# Run tests
pytest tests/ -v
```

### Troubleshooting
```bash
# If pip install fails, upgrade pip first:
pip install --upgrade pip setuptools wheel

# If Python imports fail, check you're in virtualenv:
which python3  # Should show path in venv/

# If API keys aren't loaded:
source .env  # or
export $(cat .env | xargs)

# Check Python version (should be 3.10+):
python3 --version
```

---

## Migration Checklist

Before wiping old laptop, verify:
- [ ] All git changes committed and pushed
- [ ] `.env` file backed up (DO NOT COMMIT TO GIT)
- [ ] `capsule_chain.jsonl` backed up
- [ ] `chain_seals/` directory backed up
- [ ] Any custom config files backed up
- [ ] SSH keys backed up (`~/.ssh/`)
- [ ] Important documents/files backed up

On new laptop, verify:
- [ ] Homebrew installed
- [ ] Python 3 installed
- [ ] Node.js installed
- [ ] Claude Code installed (`claude-code --version`)
- [ ] Git configured (name/email)
- [ ] Repository cloned or restored
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file restored
- [ ] Data files restored
- [ ] API server starts successfully
- [ ] Tests pass
- [ ] Auto-capture working (if used)

---

## Notes for M5 MacBook (Apple Silicon)

### Architecture Differences
- M5 uses ARM64 architecture (Apple Silicon)
- Most tools now have native ARM versions
- Some Python packages may need to be compiled

### If You Hit "Architecture" Errors
```bash
# Check if running in Rosetta mode (x86_64)
uname -m  # Should show "arm64" for native

# If a package won't install, try:
arch -arm64 brew install <package>

# For Python packages:
pip install --no-cache-dir <package>
```

### Performance Benefits
- M5 with 24GB RAM will handle:
  - Multiple Docker containers
  - Local LLM inference
  - Large pytest runs
  - Frontend + Backend + Database simultaneously
  - Much faster than Intel Macs

---

## Emergency Recovery

If something goes wrong:
```bash
# Nuclear option - fresh start
cd ~
rm -rf uatp-capsule-engine
git clone <repo-url> uatp-capsule-engine
cd uatp-capsule-engine
cp ~/uatp-backup/.env .
cp ~/uatp-backup/capsule_chain.jsonl .
cp -r ~/uatp-backup/chain_seals .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Time Estimate

- Phase 1 (Backup): 15 minutes
- Phase 2 (macOS Setup): 30 minutes
- Phase 3 (Dev Tools): 20 minutes
- Phase 4 (Claude Code): 5 minutes
- Phase 5 (UATP Setup): 20 minutes
- Phase 6 (Verification): 15 minutes
- **Total: ~2 hours** (plus download times)

---

## Questions During Migration?

Run these diagnostic commands and share output:
```bash
# System info
uname -m                 # Architecture
sw_vers                  # macOS version
which python3            # Python location
python3 --version        # Python version
brew --version           # Homebrew version
claude-code --version    # Claude Code version

# Environment check
echo $PATH
env | grep -i python

# Project check
cd ~/uatp-capsule-engine
git status
ls -la .env
head -n 1 capsule_chain.jsonl
```

Good luck with the migration! 🚀
