# UATP Vertical Upgrades Plan

**Goal**: Make UATP stronger at what it already does. No new feature categories.

**Philosophy**: Franken-Goat—graft specific muscle from proven systems, don't import organs.

---

## What We're NOT Doing

- ❌ Building a full MLOps platform (MLflow exists)
- ❌ Creating a content authenticity standard (C2PA exists)
- ❌ Implementing a supply chain framework (in-toto exists)
- ❌ Running our own transparency log (Rekor exists)
- ❌ Adding DVC/data versioning (not our problem)
- ❌ Complex policy languages (no Rego engine)

---

## What We ARE Doing

### Phase 1: Schema Discipline (Foundation)

**Problem**: Capsule payloads are snowflakes. Every capsule has different structure.

**Solution**: OpenLineage-style facet pattern.

**Implementation**:

```
src/schema/
├── __init__.py
├── base.py              # BaseFacet with _producer, _schemaURL
├── facets/
│   ├── __init__.py
│   ├── signature.py     # UATPSignatureRunFacet
│   ├── verification.py  # UATPVerificationProofRunFacet
│   ├── capsule.py       # UATPCapsuleMetadataDatasetFacet
│   ├── capture.py       # UATPCaptureContextJobFacet
│   ├── confidence.py    # UATPConfidenceRunFacet
│   └── pii.py           # UATPPIIRedactionRunFacet
├── entities.py          # Run, Job, Dataset mappings
└── validators.py        # JSON Schema validation
```

**Key Decisions**:
- Capsule = Run (execution instance)
- Capture Type = Job (what was captured)
- Input/Output = Dataset (source and result)
- Every facet has `_producer` and `_schemaURL`
- Facet names: `uatp_{name}` (snake_case)

**Minimal Facets (v1)**:
1. `uatp_signature` - Ed25519 + RFC3161 timestamp
2. `uatp_verification` - Proof that signature verified
3. `uatp_capsule` - Core capsule metadata
4. `uatp_capture` - How/why this was captured
5. `uatp_confidence` - Confidence scores with methodology

---

### Phase 2: Workflow Attestations (Chain of Custody)

**Problem**: Capsules are atoms. Real trust stories are molecules (A → B → C with approvals).

**Solution**: in-toto/Witness Link attestation model.

**Implementation**:

```
src/attestation/
├── __init__.py
├── link.py              # LinkAttestation dataclass
├── workflow.py          # WorkflowAttestation (ordered links)
├── materials.py         # ResourceDescriptor for inputs
├── policy.py            # SimplePolicy (no Rego)
└── verification.py      # Chain verification
```

**Data Model** (from in-toto):
```python
@dataclass
class LinkAttestation:
    name: str                           # Step name
    materials: List[ResourceDescriptor] # Inputs (with hashes)
    products: List[ResourceDescriptor]  # Outputs (with hashes)
    byproducts: Dict[str, Any]          # Metadata
    command: Optional[List[str]]        # What ran
```

**Workflow = Ordered Links**:
```python
@dataclass
class WorkflowAttestation:
    workflow_id: str
    steps: List[LinkAttestation]
    policy: SimplePolicy

    def verify_chain(self) -> bool:
        """Verify: step[i].products ⊇ step[i+1].materials"""
```

**Policy** (no Rego, just config):
```python
@dataclass
class SimplePolicy:
    required_steps: List[str]
    allowed_signers: Dict[str, str]  # keyid → name
    step_order: Optional[List[str]]  # None = any order
```

---

### Phase 3: DSSE Bundle Export (Portability)

**Problem**: Capsules can only be verified by UATP. External systems can't consume them.

**Solution**: Sigstore-style DSSE envelope export.

**Implementation**:

```
src/export/
├── __init__.py
├── dsse.py              # DSSE envelope creation
├── bundle.py            # Full bundle with verification material
├── pae.py               # Pre-Auth-Encoding for signing
└── formats.py           # Format converters
```

**DSSE Envelope** (exactly this structure):
```json
{
  "payload": "<Base64(capsule-as-json)>",
  "payloadType": "application/vnd.uatp.capsule.v1+json",
  "signatures": [
    {
      "keyid": "ed25519-<key-hash>",
      "sig": "<Base64(signature-over-PAE)>"
    }
  ]
}
```

**Full Bundle** (self-contained verification):
```json
{
  "mediaType": "application/vnd.uatp.bundle.v1+json",
  "dsse": { /* envelope above */ },
  "verification": {
    "publicKey": "<Base64(Ed25519 public key)>",
    "timestamp": {
      "rfc3161Token": "<Base64(RFC 3161 token)>",
      "authority": "https://freetsa.org"
    }
  }
}
```

**API Endpoint**:
```
GET /capsules/{id}/export/bundle
    → Returns DSSE bundle

GET /capsules/{id}/export/dsse
    → Returns just the envelope
```

---

### Phase 4: Verification CLI (Developer Experience)

**Problem**: Verification is API-only. No local tooling.

**Solution**: `uatp` CLI with verify command.

**Implementation**:

```
src/cli/
├── __init__.py
├── main.py              # Click CLI entry
├── verify.py            # verify subcommand
├── export.py            # export subcommand
└── inspect.py           # inspect subcommand
```

**Commands**:
```bash
# Verify a bundle file
uatp verify bundle.json
# → ✓ Signature valid (Ed25519)
# → ✓ Timestamp valid (RFC 3161, 2026-03-11T10:30:00Z)
# → ✓ Content hash matches

# Verify a capsule from server
uatp verify --capsule-id caps_2026_03_11_...
# → Fetches bundle, verifies locally

# Verify a workflow chain
uatp verify --workflow workflow_123
# → ✓ Step 1: model_inference (materials: 3, products: 1)
# → ✓ Step 2: human_review (materials: 1, products: 1)
# → ✓ Chain intact: all handoffs verified

# Export a capsule
uatp export caps_2026_... --format bundle > capsule.json
uatp export caps_2026_... --format dsse > envelope.json
```

---

## Implementation Order

```
✅ Phase 1 - Schema Discipline (COMPLETE - 20 tests)
├── ✅ Define facet base classes (src/schema/base.py)
├── ✅ Implement 5 core facets (src/schema/facets/)
├── ✅ Entity model (src/schema/entities.py)
└── ✅ Tests (tests/unit/test_schema_facets.py)

✅ Phase 2 - Workflow Attestations (COMPLETE - 31 tests)
├── ✅ ResourceDescriptor (src/attestation/materials.py)
├── ✅ LinkAttestation (src/attestation/link.py)
├── ✅ WorkflowAttestation (src/attestation/workflow.py)
├── ✅ SimplePolicy (src/attestation/policy.py)
├── ✅ AttestationVerifier (src/attestation/verification.py)
└── ✅ Tests (tests/integration/test_workflow_attestation.py)

✅ Phase 3 - DSSE Export (COMPLETE - 23 tests)
├── ✅ PAE encoding (src/export/pae.py)
├── ✅ DSSE envelope (src/export/dsse.py)
├── ✅ Bundle format (src/export/bundle.py)
└── ✅ Tests (tests/unit/test_dsse.py)

✅ Phase 4 - CLI (COMPLETE)
├── ✅ Click CLI setup (src/cli/main.py)
├── ✅ verify command (src/cli/verify.py)
├── ✅ export command (src/cli/export_cmd.py)
├── ✅ inspect command (src/cli/inspect.py)
└── ✅ pyproject.toml entry point
```

**Total: 74 tests passing**

---

## Files to Create

### Phase 1 (Schema)
```
src/schema/__init__.py
src/schema/base.py
src/schema/facets/__init__.py
src/schema/facets/signature.py
src/schema/facets/verification.py
src/schema/facets/capsule.py
src/schema/facets/capture.py
src/schema/facets/confidence.py
src/schema/entities.py
tests/unit/test_schema_facets.py
```

### Phase 2 (Attestation)
```
src/attestation/__init__.py
src/attestation/link.py
src/attestation/workflow.py
src/attestation/materials.py
src/attestation/policy.py
src/attestation/verification.py
tests/integration/test_workflow_attestation.py
```

### Phase 3 (Export)
```
src/export/__init__.py
src/export/dsse.py
src/export/bundle.py
src/export/pae.py
tests/unit/test_dsse.py
tests/integration/test_bundle_export.py
```

### Phase 4 (CLI)
```
src/cli/__init__.py
src/cli/main.py
src/cli/verify.py
src/cli/export.py
pyproject.toml (add entry point)
```

---

## What This Enables (Without Adding)

1. **Interoperability**: External systems can verify UATP capsules without importing UATP
2. **Chain of custody**: Multi-step AI workflows have verifiable handoffs
3. **Machine legibility**: Capsules follow consistent schema, can be processed automatically
4. **Developer adoption**: CLI makes verification practical, not ceremonial
5. **Future-proofing**: Schema discipline means we can evolve without breaking consumers

---

## What This Does NOT Add

- No new capsule types (just better structure for existing)
- No new storage backends
- No new authentication methods
- No new UI components
- No new external service dependencies
- No new database tables (workflow uses existing chain_seals)

---

## Success Criteria

1. **Schema**: `python -c "from src.schema import UATPSignatureRunFacet"` works
2. **Workflow**: `GET /workflows/{id}/verify` returns chain verification
3. **Export**: `GET /capsules/{id}/export/bundle` returns valid DSSE
4. **CLI**: `uatp verify bundle.json` exits 0 for valid bundles

---

## Dependencies (What We Steal)

| System | What We Take | What We Skip |
|--------|-------------|--------------|
| OpenLineage | Facet pattern, entity model | Job scheduling, data quality metrics |
| in-toto | Link structure, material/product hashing | Layout DSL, sublayouts, complex rules |
| Witness | Handoff verification pattern | Rego engine, X.509 chains |
| Sigstore | DSSE envelope, PAE, bundle format | Fulcio, Rekor (use existing RFC3161) |
| MLflow | Nothing code-wise | Study for UX inspiration only |
