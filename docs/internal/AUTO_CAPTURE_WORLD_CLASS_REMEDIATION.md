# Auto Capture System - World-Class Remediation Plan

## Executive Summary

**Current State**: 79 files, Grade C+ (working but chaotic)
**Target State**: 15 files, Grade A (production-ready, maintainable)
**Time to Fix**: 3-4 hours (comprehensive refactor)
**Risk**: LOW (mostly organizational, not functional)

---

## Critical Assessment

### The Good [OK]
- **Core modules work** (`src/live_capture/` - 13 files, 5,038 lines)
- **Currently capturing** (2 processes running, data flowing)
- **Rich metadata** (confidence, uncertainty, court-admissible format)
- **Multiple platform support** (Claude, OpenAI, Cursor, Windsurf, Gemini)

### The Bad [ERROR]
- **79 total files** (44 experimental scripts cluttering root)
- **13+ ways to capture** (no canonical approach documented)
- **Import bugs** (4 files will fail at runtime)
- **Timezone bugs** (naive datetime.now() usage)
- **Duplicate processes** (2 running, probably capturing same data)
- **Tests in wrong location** (10 files in root instead of tests/)

### The Ugly
- **No architecture doc** explaining which system to use
- **70% code duplication** across 6 hook files
- **Single class doing 7+ jobs** (ClaudeCodeCapture)
- **Competing implementations** fighting over data

---

## Phase 1: CRITICAL BUGS (Fix Immediately)

### Bug #1: Import Path Errors [ERROR] CRITICAL

**4 files will fail at runtime:**

```python
# WRONG (will crash):
from live_capture.real_time_capsule_generator import capture_live_interaction

# CORRECT:
from src.live_capture.real_time_capsule_generator import capture_live_interaction
```

**Affected Files:**
- `src/live_capture/openai_hook.py`
- `src/live_capture/cursor_hook.py`
- `src/live_capture/windsurf_hook.py`
- `src/live_capture/anthropic_hook.py`

**Fix Script:**
```bash
# Replace broken imports
for file in src/live_capture/{openai,cursor,windsurf,anthropic}_hook.py; do
    sed -i '' 's/from live_capture\./from src.live_capture./g' "$file"
done
```

### Bug #2: Timezone Issues [ERROR] HIGH

**File:** `src/live_capture/claude_code_hook.py:84`

```python
# WRONG:
"timestamp": datetime.now().isoformat()  # Naive datetime

# CORRECT:
"timestamp": utc_now().isoformat()  # Timezone-aware
```

**Scope:** Need to scan all capture files for naive datetime usage.

### Bug #3: Duplicate Processes  MEDIUM

**Running:**
- PID 1325: `claude_code_auto_capture.py` (since Dec 2)
- PID 37964: `antigravity_capture_integration.py` (since Dec 6)

**Problem:** Probably capturing same conversations twice.

**Investigation Needed:**
1. Check database for duplicate capsules
2. Determine which process is authoritative
3. Kill redundant process or merge logic

---

## Phase 2: ARCHITECTURE CLEANUP (Consolidate)

### Problem: 44 Experimental Files in Root

**Categorization:**

| Category | Count | Action |
|----------|-------|--------|
| **Duplicate capture scripts** | 12 | Delete or archive |
| **Fix/debug scripts** | 4 | Delete (obsolete) |
| **Setup scripts** | 2 | Keep 1, archive 1 |
| **Test files** | 10 | Move to `tests/capture/` |
| **ChatGPT-specific** | 3 | Move to `experiments/chatgpt/` |
| **Experimental variants** | 8 | Archive to `experiments/` |
| **Legitimate tools** | 5 | Keep, rename for clarity |

**Keep (5 files):**
1. `claude_code_auto_capture.py` - Background service (if needed)
2. `antigravity_capture_integration.py` - Gemini integration (if distinct)
3. `rich_hook_capture.py` - Shell hook entry point
4. `manage-auto-capture.sh` - Control script
5. One canonical setup script (rename to `setup_capture.py`)

**Archive (35+ files):**
```bash
mkdir -p archive/experimental_capture
mv capture_*.py archive/experimental_capture/
mv fix_*.py archive/experimental_capture/
mv create_*.py archive/experimental_capture/
mv setup_*.py archive/experimental_capture/
mv dynamic_*.py archive/experimental_capture/
# ... (see detailed list below)
```

**Move to tests/ (10 files):**
```bash
mkdir -p tests/capture
mv test_*.py tests/capture/
```

---

## Phase 3: CODE REFACTORING (DRY Principle)

### Problem: 70% Code Duplication Across Hooks

**Current: 6 separate hook files**
- `openai_hook.py` (595 lines)
- `cursor_hook.py` (499 lines)
- `windsurf_hook.py` (377 lines)
- `anthropic_hook.py` (402 lines)
- `antigravity_hook.py` (419 lines)
- `claude_code_hook.py` (198 lines)

**Total:** 2,490 lines (est. 1,700 lines are duplicate)

**Solution: Create BaseHook Class**

```python
# src/live_capture/base_hook.py (NEW)

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.utils.timezone_utils import utc_now

class BaseHook(ABC):
    """
    Abstract base class for all platform hooks.

    Eliminates duplication across OpenAI, Cursor, Windsurf, etc.
    """

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.capture_generator = RealTimeCapsuleGenerator()

    @abstractmethod
    def extract_conversation(self, raw_data: Any) -> Dict[str, Any]:
        """Platform-specific: Extract conversation from raw API data."""
        pass

    @abstractmethod
    def get_platform_metadata(self) -> Dict[str, Any]:
        """Platform-specific: Get platform-specific metadata."""
        pass

    def capture_interaction(self, raw_data: Any) -> Dict[str, Any]:
        """
        Common capture logic (same across all platforms).

        This method is 90% identical across all hooks.
        """
        # 1. Extract conversation (platform-specific)
        conversation = self.extract_conversation(raw_data)

        # 2. Add timestamp (common)
        conversation["timestamp"] = utc_now().isoformat()

        # 3. Calculate significance (common)
        significance = self.capture_generator.calculate_significance(conversation)

        # 4. Add platform metadata (platform-specific)
        metadata = self.get_platform_metadata()
        conversation["platform"] = metadata

        # 5. Store capsule (common)
        capsule_id = self.capture_generator.create_capsule(conversation)

        return {"capsule_id": capsule_id, "significance": significance}
```

**Then: Platform-specific hooks become tiny**

```python
# src/live_capture/openai_hook.py (AFTER refactor - 50 lines)

from src.live_capture.base_hook import BaseHook

class OpenAIHook(BaseHook):
    def __init__(self):
        super().__init__(platform_name="OpenAI")

    def extract_conversation(self, raw_data):
        """OpenAI-specific extraction logic."""
        return {
            "messages": raw_data["choices"][0]["message"],
            "model": raw_data["model"],
            "tokens": raw_data["usage"]
        }

    def get_platform_metadata(self):
        """OpenAI-specific metadata."""
        return {
            "platform": "OpenAI",
            "api_version": "v1",
            "endpoint": "chat/completions"
        }
```

**Savings:** 2,490 lines → ~600 lines (75% reduction)

---

## Phase 4: SINGLE SOURCE OF TRUTH

### Problem: 3 Competing Capture Paths

**Current Mess:**
```
Path 1: Shell hook → rich_hook_capture.py → claude_code_capture.py → SQLite
Path 2: Background service (claude_code_auto_capture.py) → PostgreSQL
Path 3: Antigravity service (antigravity_capture_integration.py) → PostgreSQL
Path 4: API routes → Generic handlers → PostgreSQL
Path 5-17: 44 root scripts → Unknown destinations
```

**Solution: Canonical Path (One Entry Point)**

```
┌─────────────────────────────────────────┐
│  USER INTERACTION (any platform)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  CaptureOrchestrator       │  ← NEW: Single entry point
    │  (platform detection)      │
    └────────────┬───────────────┘
                 │
       ┌─────────┼─────────┐
       │         │         │
       ▼         ▼         ▼
   OpenAI    Claude    Cursor   (Platform hooks extend BaseHook)
   Hook      Hook      Hook
       │         │         │
       └─────────┼─────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  RealTimeCapsuleGenerator  │  ← Significance analysis
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  RichCaptureEnhancer       │  ← Metadata enrichment
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  PostgreSQL (production)   │  ← Single database
    └────────────────────────────┘
```

**Implementation:**

```python
# src/live_capture/capture_orchestrator.py (NEW)

class CaptureOrchestrator:
    """
    Single entry point for ALL capture operations.

    Routes to appropriate hook based on platform detection.
    """

    def __init__(self):
        self.hooks = {
            "openai": OpenAIHook(),
            "claude": ClaudeCodeHook(),
            "cursor": CursorHook(),
            "windsurf": WindsurfHook(),
            "anthropic": AnthropicHook(),
            "gemini": AntigravityHook()
        }

    def capture(self, platform: str, data: Any) -> Dict[str, Any]:
        """Route to appropriate hook."""
        if platform not in self.hooks:
            raise ValueError(f"Unknown platform: {platform}")

        hook = self.hooks[platform]
        return hook.capture_interaction(data)
```

---

## Phase 5: TESTING INFRASTRUCTURE

### Problem: Tests Scattered, Incomplete

**Move Tests to Proper Location:**

```bash
mkdir -p tests/capture/unit
mkdir -p tests/capture/integration

# Move unit tests
mv test_live_capture.py tests/capture/unit/
mv test_enhanced_auto_capture.py tests/capture/unit/

# Move integration tests
mv test_live_capture_integration.py tests/capture/integration/
mv test_capture_to_postgres.py tests/capture/integration/
```

**Create Comprehensive Test Suite:**

```python
# tests/capture/test_capture_system.py (NEW)

import pytest
from src.live_capture.capture_orchestrator import CaptureOrchestrator
from src.live_capture.base_hook import BaseHook

class TestCaptureSystem:
    """Comprehensive capture system tests."""

    def test_all_hooks_registered(self):
        """Ensure all platform hooks are registered."""
        orchestrator = CaptureOrchestrator()
        expected_platforms = ["openai", "claude", "cursor", "windsurf", "anthropic", "gemini"]
        assert set(orchestrator.hooks.keys()) == set(expected_platforms)

    def test_no_duplicate_processes(self):
        """Ensure only one capture process per platform."""
        # Check process list
        # Assert no duplicates
        pass

    def test_timezone_consistency(self):
        """All capture timestamps must be timezone-aware UTC."""
        from src.live_capture import claude_code_capture
        import inspect

        # Scan source for naive datetime usage
        source = inspect.getsource(claude_code_capture)
        assert "datetime.now()" not in source, "Found naive datetime usage"

    def test_import_paths_valid(self):
        """All imports must be absolute (from src.*)."""
        # Verify no relative imports in hooks
        pass

    def test_no_duplicate_capsules(self):
        """Multiple capture processes shouldn't create duplicates."""
        # Query database for duplicate capsule_ids
        pass
```

---

## Phase 6: DOCUMENTATION

### Create Master Architecture Document

**File:** `docs/CAPTURE_SYSTEM_ARCHITECTURE.md`

```markdown
# UATP Capture System Architecture

## Quick Start

**Question: Which capture method should I use?**

**Answer: Use the canonical path (automatic):**
1. Claude Code messages → `.claude/hooks/auto_capture.sh` (automatic)
2. Other platforms → `CaptureOrchestrator.capture(platform, data)`

**DO NOT use any of the 44 root-level scripts** - they're experimental.

## Architecture Diagram

[Insert diagram from Phase 4]

## Components

### Production Code (USE THIS)
- `src/live_capture/capture_orchestrator.py` - Entry point
- `src/live_capture/base_hook.py` - Hook base class
- `src/live_capture/real_time_capsule_generator.py` - Core engine
- `src/live_capture/*_hook.py` - Platform-specific hooks

### Experimental Code (IGNORE)
- `archive/experimental_capture/*` - Old experiments

## Migration Guide

### If you're using old scripts:
1. Stop using root-level `capture_*.py` scripts
2. Use `CaptureOrchestrator` instead
3. See examples in `tests/capture/`
```

---

## Phase 7: CONTINUOUS PREVENTION

### Add Linting Rules

**File:** `.pylintrc` (add to existing)

```ini
[MASTER]
# Prevent root-level capture scripts
disable=
    root-level-capture-script

[CAPTURE]
# Ban patterns that indicate experimental capture code
bad-names=
    capture_this_*,
    create_instant_*,
    fix_live_*
```

### Pre-commit Hook

**File:** `.pre-commit-config.yaml` (add)

```yaml
repos:
  - repo: local
    hooks:
      - id: no-root-capture-scripts
        name: Prevent root-level capture scripts
        entry: '^(capture_|test_live_|fix_live_|create_instant_).*\.py$'
        language: pygrep
        files: '^[^/]+\.py$'  # Root level only
```

---

## Execution Plan

### Immediate (Today - 1 hour)

**Priority 1: Fix Critical Bugs**
```bash
# 1. Fix import paths
python3 scripts/fix_capture_imports.py

# 2. Fix timezone issues
python3 scripts/fix_capture_timezones.py

# 3. Identify duplicate processes
ps aux | grep capture
# Kill redundant process after verification
```

### Short-term (This Week - 3 hours)

**Priority 2: Consolidate Architecture**
```bash
# 1. Create archive directory
mkdir -p archive/experimental_capture
mkdir -p experiments/chatgpt

# 2. Move experimental files
mv capture_*.py archive/experimental_capture/
mv test_*.py tests/capture/

# 3. Create BaseHook class
# (Manual coding - see Phase 3)

# 4. Refactor existing hooks to extend BaseHook
# (Manual coding - reduces 2,490 lines → 600 lines)
```

### Medium-term (Next Sprint - 2 hours)

**Priority 3: Create Canonical Path**
```bash
# 1. Implement CaptureOrchestrator
# (Manual coding - see Phase 4)

# 2. Create comprehensive tests
# (Manual coding - see Phase 5)

# 3. Write architecture documentation
# (Manual writing - see Phase 6)
```

---

## Success Metrics

### Before:
- [ERROR] 79 files (44 experimental)
- [ERROR] 13+ ways to capture
- [ERROR] Import bugs in 4 files
- [ERROR] Timezone bugs present
- [ERROR] 70% code duplication
- [ERROR] No architecture docs
- [ERROR] Tests scattered
- **Grade: C+**

### After:
- [OK] ~15 production files
- [OK] 1 canonical capture path
- [OK] All import bugs fixed
- [OK] All timezone bugs fixed
- [OK] Minimal duplication (BaseHook pattern)
- [OK] Complete architecture docs
- [OK] Organized test suite
- **Grade: A**

---

## Risk Analysis

### Low Risk Changes (Safe)
- Moving experimental files to archive
- Moving tests to proper location
- Adding documentation
- Creating new utility classes (BaseHook, CaptureOrchestrator)

### Medium Risk Changes (Test Carefully)
- Fixing import paths (changes production code)
- Fixing timezone issues (changes timestamps)
- Refactoring hooks to use BaseHook (significant refactor)

### High Risk Changes (DO NOT DO)
- Deleting files without archiving
- Changing capture format (breaks existing capsules)
- Modifying database schema

---

## Files to Archive (Detailed List)

### Duplicate Capture Scripts (12 files):
- `capture_this_conversation.py` (5.7K)
- `capture_current_conversation.py` (6.3K)
- `capture_todays_conversation.py` (8.3K)
- `capture_this_session.py` (8.5K)
- `capture_session.py` (11K)
- `capture_direct_capsule.py` (1.7K)
- `capture_quality_badge_session.py` (9.8K)
- `capture_real_data.py` (8.1K)
- `capture_with_significance.py` (6.5K)
- `capture_universal_implementation_session.py` (5.9K)
- `capture_via_api.py` (4.3K)
- `fixed_conversation_capture.py` (16K)

### Fix/Debug Scripts (4 files):
- `fix_live_capture_display.py` (12K) - OBSOLETE
- `fix_live_capture_schema.py` (14K) - OBSOLETE
- `fix_live_capture_verification.py` (5.3K) - OBSOLETE
- `run_fixed_capture.py` (3.8K) - DEBUG

### Experimental Variants (8 files):
- `create_instant_capture.py` (9.6K)
- `create_rich_live_capture.py` (5.1K)
- `create_verified_live_capture.py` (14K)
- `dynamic_session_capture.py` (5.8K)
- `add_live_capture_to_db.py` (2.4K)
- `live_capture_client.py` (1.8K)
- `setup_live_capture.py` (2.8K)
- `setup_automatic_capture.py` (11K)

### ChatGPT-Specific (3 files):
- `capture_chatgpt_conversations.py` (6.1K)
- `capture_chatgpt_desktop.py` (8.0K)
- `chatgpt_network_capture.py` (8.9K)

### Keep (5 files):
- `claude_code_auto_capture.py` - Background service
- `antigravity_capture_integration.py` - Gemini integration
- `rich_hook_capture.py` - Shell hook entry
- `manage-auto-capture.sh` - Control script
- `check_capture_status.sh` - Status utility

---

## Conclusion

The UATP auto capture system has **excellent core functionality** buried under **architectural sprawl**.

**The world-class approach:**
1. Fix critical bugs first (import paths, timezones)
2. Archive experimental files (don't delete - might learn from them)
3. Consolidate to single canonical path
4. Eliminate duplication with BaseHook pattern
5. Add comprehensive tests and documentation
6. Prevent future sprawl with linting rules

**Time investment: 6 hours**
**Result: Production-grade, maintainable capture system**
**Grade improvement: C+ → A**

---

*Generated: 2025-12-14*
*Approach: World-Class Engineering Methodology*
*Status: READY TO EXECUTE*
