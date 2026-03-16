# UATP Vertical Upgrades v2 - Research-Driven Improvements

**Based on research from**: OpenLineage, in-toto/Witness, Sigstore, cosign, grype, trivy

---

## Quick Wins (Implement Now)

### 1. Schema: Versioned Schema URLs + Deletion Tracking

**Problem**: Schema URLs aren't versioned; deletion isn't tracked properly.

```python
# BEFORE
_schemaURL = f"{UATP_SCHEMA_BASE}/{self.__class__.__name__}.json"

# AFTER
_schemaURL = f"{UATP_SCHEMA_BASE}/v{self._facet_version}/{self.__class__.__name__}.json"
_deleted_at: Optional[datetime] = None
_deletion_reason: Optional[str] = None
```

### 2. Schema: Facet Registry for Discovery

```python
class FacetRegistry:
    _facets: Dict[str, Type[BaseFacet]] = {}

    @classmethod
    def register(cls, facet_class, entity_type, version, tags):
        key = facet_class.facet_key()
        cls._facets[key] = {"class": facet_class, ...}

    @classmethod
    def list_facets(cls, entity_type=None, tag=None):
        # Filter and return registered facets
```

### 3. Attestation: Expiration & Validity Windows

```python
@dataclass
class AttestationValidity:
    issued_at: datetime
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None

    def is_valid_at(self, when: datetime) -> bool:
        if self.not_before and when < self.not_before:
            return False
        if self.not_after and when > self.not_after:
            return False
        return True
```

### 4. Export: Transparency Log Evidence

```python
@dataclass
class TransparencyLogEvidence:
    log_url: Optional[str] = None
    log_entry_uuid: Optional[str] = None
    log_index: Optional[int] = None
    inclusion_proof: Optional[Dict[str, Any]] = None  # Merkle proof
    signed_entry_timestamp: Optional[str] = None
```

### 5. Export: Algorithm Negotiation

```python
def verify_bundle(bundle: UATPBundle) -> VerificationResult:
    algorithms_to_try = material.signature_algorithms or [material.key_algorithm]
    for algo in algorithms_to_try:
        if algo == "ed25519" and _verify_ed25519(bundle):
            return success
        elif algo == "ecdsa-sha256" and _verify_ecdsa(bundle):
            return success
        elif algo == "ml-dsa-65" and _verify_ml_dsa(bundle):
            return success
```

### 6. CLI: Multi-Level Exit Codes

```
0 = All checks passed
1 = Verification failed (signature invalid)
2 = Warnings only (signature valid, timestamp missing)
3 = Configuration error (file not found)
4 = Network/transient error (timeout, retry)
```

### 7. CLI: JSON Output Mode

```bash
uatp verify bundle.json --output json
# {"is_valid": true, "signature_valid": true, ...}
```

### 8. CLI: Batch Verification

```bash
uatp verify *.json --parallel 4
# Process 4 bundles at a time with progress
```

---

## Medium-Term Improvements

### 9. Schema: Hierarchical Facets (Parent Capsule)

```python
@dataclass
class UATPParentCapsuleRunFacet(RunFacet):
    parent_capsule_id: str = ""
    root_capsule_id: Optional[str] = None
    chain_depth: int = 1
```

### 10. Attestation: Threshold Signer Requirements

```python
@dataclass
class ThresholdSignerPolicy:
    step_name: str
    required_signers: int  # M threshold
    eligible_signers: List[str]  # N possible signers
```

### 11. Attestation: Signed Policy Layouts

```python
@dataclass
class WorkflowLayout:
    layout_id: str
    steps: List[LayoutStep]
    signed_by: str
    signature: str
```

### 12. Export: Certificate Chain Support

```python
@dataclass
class VerificationMaterial:
    certificate: Optional[str] = None  # PEM X.509
    certificate_chain: Optional[List[str]] = None
    identity: Optional[str] = None  # OIDC email
    identity_issuer: Optional[str] = None
```

### 13. Export: Offline vs Online Verification Modes

```python
class VerificationMode(Enum):
    OFFLINE = "offline"  # Use only stapled data
    ONLINE = "online"    # Query TSA, transparency logs
    HYBRID = "hybrid"    # Prefer offline, fallback
```

### 14. CLI: Verbosity Levels

```bash
uatp verify bundle.json -v    # Show checks
uatp verify bundle.json -vv   # Show details
uatp verify bundle.json -vvv  # Show raw crypto
uatp verify bundle.json -q    # Quiet mode
```

---

## Lower Priority / Future

### 15. Schema: JSON Schema Validation Layer
### 16. Attestation: Revocation Management
### 17. Attestation: Nested/Hierarchical Workflows
### 18. Export: Key/CA Rotation with TUF Metadata
### 19. CLI: Config File Support (~/.config/uatp/verify.yaml)
### 20. CLI: Retry with Exponential Backoff

---

## Implementation Order

```
Phase 1 (Quick Wins - This Session):
├── ✅ Schema: Facet versioning + deletion tracking
├── ✅ Schema: Facet registry
├── ✅ Attestation: Validity windows
├── ✅ CLI: Exit codes + JSON output + batch

Phase 2 (Next Session):
├── Attestation: Threshold signers
├── Export: Certificate chain
├── Export: Transparency log evidence
├── CLI: Verbosity levels

Phase 3 (Future):
├── Schema: Hierarchical facets
├── Attestation: Signed layouts
├── Export: Verification modes
├── Full Sigstore interop
```
