# UATP Repository Restructure Plan

## Current State Analysis

**Root level chaos:**
- 95+ files (should be ~15)
- 27 directories (should be ~8)
- Logs, PIDs, generated JSONs, RTFs, PDFs mixed with source
- 50+ shell scripts at root
- Overlapping infra folders: dashboards, grafana, monitoring, observability, k8s, helm, deployment

## Target Architecture

```
uatp/
├── README.md              # Front door - one proof path
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── THREAT_MODEL.md        # NEW: Attack surface documentation
├── TRUST_MODEL.md
├── STATUS.md              # NEW: What's shipped/beta/experimental
├── CHANGELOG.md
├── CLAUDE.md              # Claude Code context
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
│
├── src/                   # Core product
│   ├── api/
│   ├── engine/
│   ├── crypto/
│   └── core/
│
├── sdk/                   # Client libraries
│   └── python/
│
├── frontend/              # Web dashboard
│
├── tests/                 # All tests
│
├── examples/              # Usage examples (curated)
│
├── infra/                 # Consolidated operations
│   ├── docker/
│   ├── kubernetes/
│   │   ├── helm/
│   │   └── manifests/
│   └── monitoring/
│       ├── grafana/
│       └── dashboards/
│
├── docs/                  # Documentation wings
│   ├── start-here.md      # Navigation for all audiences
│   ├── getting-started/
│   ├── concepts/
│   ├── architecture/
│   ├── operations/
│   └── research/
│       ├── whitepaper.md
│       └── system-guide.md
│
├── scripts/               # Operational scripts (organized)
│   ├── setup/
│   ├── capture/
│   └── dev/
│
└── archive/               # Historical artifacts
    ├── README.md          # "These are not canonical"
    ├── vision/
    ├── generated/
    └── legacy/
```

## User Journey Paths

### Engineer Path
README → docs/getting-started → examples → sdk/python → tests

### Security Reviewer Path
README → TRUST_MODEL.md → THREAT_MODEL.md → SECURITY.md → tests/security

### Buyer/Partner Path
README → STATUS.md → examples/demo → docs/architecture

### Researcher Path
README → docs/research/whitepaper.md → ROADMAP.md → docs/concepts

## Files to Move

### Root → archive/generated/
- All *.log files
- All *.pid files
- All generated *.json capsules
- *.db files (except as examples)

### Root → archive/vision/
- COMPLETE_VISION_BLUEPRINT_v2.rtf
- UATP_Vision_Blueprint.rtf
- UATP_White_Paper.docx
- *.pdf vision documents

### Root → scripts/
- All *.sh files (organized by purpose)
- All *.command files

### Root → archive/legacy/
- HTML test files
- One-off demo files

### Directories to Consolidate

#### Into infra/
- deployment/ → infra/docker/
- k8s/ → infra/kubernetes/manifests/
- helm/ → infra/kubernetes/helm/
- grafana/ → infra/monitoring/grafana/
- dashboards/ → infra/monitoring/dashboards/
- monitoring/ → infra/monitoring/
- observability/ → infra/monitoring/observability/

#### Into docs/
- outreach/ → docs/outreach/ or archive/
- experiments/ → archive/experiments/

#### Into archive/
- chain_seals/ → archive/generated/
- audit_reports/ → archive/reports/
- backups/ → (gitignore, don't commit)
- data/ → (gitignore or archive)
- storage/ → (gitignore)

## New Files to Create

1. **STATUS.md** - What's shipped, beta, experimental, planned
2. **THREAT_MODEL.md** - Attack surface and mitigations
3. **docs/start-here.md** - Navigation hub for all audiences
4. **archive/README.md** - "Files here are historical artifacts"

## Execution Order

### Phase 1: Create structure
1. Create infra/, archive/ directories
2. Create STATUS.md, THREAT_MODEL.md
3. Create docs/start-here.md

### Phase 2: Move files
1. Move generated files to archive/
2. Move scripts to scripts/
3. Consolidate infra folders

### Phase 3: Update references
1. Update any hardcoded paths
2. Update documentation links
3. Test that everything still works

### Phase 4: Push and verify
1. Commit with clear message
2. Push to GitHub
3. Verify GitHub renders correctly
