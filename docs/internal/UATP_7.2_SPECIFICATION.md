# UATP 7.2 Specification

## Universal AI Transparency Protocol - Edge-Native Provenance

**Version**: 7.2.0-draft
**Status**: Draft Specification
**Date**: March 2026
**Authors**: UATP Working Group

---

## Abstract

UATP 7.2 extends the Universal AI Transparency Protocol to address the paradigm shift toward edge computing, on-device training, and agentic AI systems. This specification introduces:

1. **Training Provenance** - Full lifecycle tracking from base model to fine-tuned deployment
2. **Agentic Workflow Chains** - DAG-based lineage for multi-step AI agent operations
3. **Hardware Attestation** - Cryptographic proof of execution environment
4. **Edge-Native Capsules** - Lightweight format for resource-constrained devices
5. **Model Registry Protocol** - Content-addressed model versioning and linking

These extensions respond to two critical developments: the democratization of AI training through on-device compute (e.g., Apple Neural Engine) and the proliferation of open-source frontier models (e.g., Qwen 3.5) that rival proprietary systems.

---

## Table of Contents

1. [Motivation](#1-motivation)
2. [Training Provenance Schema](#2-training-provenance-schema)
3. [Agentic Workflow Chains](#3-agentic-workflow-chains)
4. [Hardware Attestation](#4-hardware-attestation)
5. [Edge-Native Capsules](#5-edge-native-capsules)
6. [Model Registry Protocol](#6-model-registry-protocol)
7. [Cryptographic Requirements](#7-cryptographic-requirements)
8. [Backward Compatibility](#8-backward-compatibility)
9. [Security Considerations](#9-security-considerations)
10. [Implementation Guidelines](#10-implementation-guidelines)

---

## 1. Motivation

### 1.1 The Edge AI Shift

Traditional UATP (7.0/7.1) assumed a cloud-centric model:
- AI inference happens on remote servers
- Capsules are created and signed in controlled environments
- Network connectivity is available for verification

This model is obsolete. Evidence:

- **ANE Training** (maderix/ANE): Neural network training directly on Apple Silicon Neural Engine using reverse-engineered APIs demonstrates consumer hardware can perform training, not just inference.
- **Qwen 3.5**: Open-source 397B parameter MoE model matching Claude Opus 4.5/GPT-5.2, deployable locally.
- **Regulatory Pressure**: EU AI Act and similar frameworks require accountability regardless of where AI runs.

### 1.2 The Attribution Gap

Current UATP tracks inference provenance:
```
User Prompt → Model Inference → AI Response → Capsule
```

This misses critical attribution layers:
```
Training Data → Base Model → Fine-Tuning → Deployment → Inference → Response
     ↓              ↓            ↓             ↓            ↓
  [WHO?]        [WHO?]       [WHO?]        [WHERE?]    [VERIFIED?]
```

UATP 7.2 closes this gap.

### 1.3 Agentic Complexity

Modern AI systems are not single-shot inference. Qwen 3.5 and similar models feature native tool calling, enabling:

```
Plan → Search Tool → Code Execution → API Call → Synthesis → Response
```

Each step requires:
- Independent verification
- Lineage linking
- Attribution tracking
- Failure accountability

---

## 2. Training Provenance Schema

### 2.1 Overview

Training provenance captures the complete lifecycle of a model from base weights through deployment.

### 2.2 Schema Definition

```yaml
training_provenance:
  # Base model information
  base_model:
    model_id: string           # Unique identifier (e.g., "qwen3.5-397b-a17b")
    model_hash: string         # SHA-256 of weights file
    registry_uri: string       # Content-addressed location
    license: string            # SPDX identifier (e.g., "Apache-2.0")
    publisher: string          # Organization or individual
    publish_date: datetime     # ISO 8601

  # Training data provenance (may be partially redacted for privacy)
  training_data:
    dataset_id: string         # Optional identifier
    dataset_hash: string       # Hash of training data manifest
    data_sources:              # Array of data source descriptors
      - source_type: enum      # "public", "licensed", "proprietary", "synthetic"
        source_uri: string     # Location or identifier
        license: string        # Data license
        consent_verified: bool # GDPR/consent compliance
    sample_count: integer      # Total training samples
    cutoff_date: datetime      # Data recency cutoff

  # Fine-tuning information (if applicable)
  fine_tuning:
    method: enum               # "full", "lora", "qlora", "adapter", "prompt_tuning"
    parent_model_hash: string  # Hash of model before fine-tuning
    dataset_hash: string       # Fine-tuning dataset hash
    hyperparameters:           # Training configuration
      learning_rate: float
      epochs: integer
      batch_size: integer
      # ... additional params
    hardware:
      device_type: string      # "ANE", "CUDA", "TPU", "CPU"
      device_id: string        # Hardware identifier
      attestation: string      # Hardware attestation token (see Section 4)
    trainer_id: string         # Who performed fine-tuning
    training_date: datetime
    resulting_model_hash: string

  # Deployment context
  deployment:
    environment: enum          # "cloud", "edge", "on-device", "hybrid"
    runtime: string            # "coreml", "onnx", "pytorch", "tflite"
    quantization: string       # "fp16", "int8", "int4", "none"
    hardware_attestation: string  # See Section 4
```

### 2.3 Provenance Chain

Models form a directed acyclic graph (DAG) of provenance:

```
llama-3.1-405b (Meta)
    │
    ├── qwen3.5-397b-a17b (Alibaba, trained on Llama architecture insights)
    │       │
    │       └── my-legal-assistant-v1 (Fine-tuned by LawFirm Inc.)
    │               │
    │               └── capsule_abc123 (Inference output)
    │
    └── mistral-large-2 (Mistral AI)
            │
            └── code-assistant-v3 (Fine-tuned by DevCorp)
```

Each node is content-addressed by its weight hash, enabling:
- Verification of claimed provenance
- Detection of undisclosed fine-tuning
- Attribution to training data sources

### 2.4 Privacy Considerations

Training provenance may contain sensitive information. UATP 7.2 supports:

1. **Redacted Provenance**: Hash commitments without revealing details
2. **Zero-Knowledge Proofs**: Prove properties without revealing data
3. **Tiered Disclosure**: Different detail levels for different verifiers

```yaml
training_data:
  # Redacted form - proves properties without revealing sources
  commitment: "sha256:abc123..."  # Commitment to full data
  proven_properties:
    - "no_pii_in_training"
    - "license_compliant"
    - "consent_verified"
  zk_proof: "base64:..."  # ZK proof of properties
```

---

## 3. Agentic Workflow Chains

### 3.1 Overview

Agentic AI systems execute multi-step workflows with tool calls, branching decisions, and external interactions. UATP 7.2 introduces **Workflow Chains** to track these complex execution paths.

### 3.2 Workflow Capsule Schema

```yaml
workflow_capsule:
  workflow_id: string          # Unique workflow identifier
  version: "7.2"

  # Workflow metadata
  metadata:
    initiator: string          # User or system that started workflow
    intent: string             # High-level goal description
    started_at: datetime
    completed_at: datetime
    status: enum               # "running", "completed", "failed", "cancelled"

  # Execution graph (DAG)
  execution_graph:
    nodes:
      - node_id: string
        node_type: enum        # "plan", "tool_call", "inference", "decision", "output"
        capsule_id: string     # Reference to individual step capsule
        timestamp: datetime

    edges:
      - from_node: string
        to_node: string
        edge_type: enum        # "sequence", "branch", "parallel", "retry"
        condition: string      # Optional: branching condition

  # Aggregated attribution
  attribution:
    models_used:               # All models invoked in workflow
      - model_hash: string
        invocation_count: integer
        token_count: integer
    tools_used:                # All tools invoked
      - tool_id: string
        invocation_count: integer
    total_cost: float          # Aggregated cost if applicable

  # Verification
  verification:
    workflow_hash: string      # Hash of complete execution graph
    signature: string          # Signature over workflow_hash
    signer_id: string
```

### 3.3 Step Capsule Schema

Each node in the workflow graph references a step capsule:

```yaml
step_capsule:
  step_id: string
  workflow_id: string          # Parent workflow reference
  version: "7.2"

  step_type: enum              # "plan", "tool_call", "inference", "decision", "output"

  # For tool calls
  tool_call:
    tool_id: string            # Tool identifier
    tool_version: string
    input_hash: string         # Hash of tool input
    output_hash: string        # Hash of tool output
    execution_time_ms: integer
    success: boolean
    error: string              # If failed

  # For inference steps
  inference:
    model_hash: string
    prompt_hash: string
    response_hash: string
    token_count:
      input: integer
      output: integer
    latency_ms: integer

  # For decision points
  decision:
    condition: string
    evaluated_to: boolean
    alternatives:
      - option: string
        score: float
        selected: boolean

  # Lineage
  parent_steps: [string]       # Step IDs this depends on
  child_steps: [string]        # Step IDs that depend on this

  # Verification
  verification:
    step_hash: string
    signature: string
    timestamp: datetime
```

### 3.4 Workflow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ Workflow: "Research and summarize quantum computing advances"   │
│ ID: wf_2026030212345                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PLAN (step_1) │
                    │ capsule: cap_a  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ TOOL: search│ │ TOOL: search│ │ TOOL: search│
     │   (step_2)  │ │   (step_3)  │ │   (step_4)  │
     │ "arxiv API" │ │ "scholar"   │ │ "news API"  │
     └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                  ┌─────────────────┐
                  │ INFERENCE (5)   │
                  │ "synthesize"    │
                  │ model: qwen3.5  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ OUTPUT (step_6) │
                  │ capsule: cap_f  │
                  └─────────────────┘
```

### 3.5 Failure Attribution

When workflows fail, the chain enables precise attribution:

```yaml
workflow_failure:
  workflow_id: string
  failed_step: string          # Which step failed
  failure_type: enum           # "tool_error", "model_error", "timeout", "policy_violation"
  failure_details: string
  upstream_contributing_factors:
    - step_id: string
      contribution: string     # How this step contributed to failure
  recovery_attempted: boolean
  recovery_steps: [string]     # Steps taken to recover
```

---

## 4. Hardware Attestation

### 4.1 Overview

Hardware attestation proves that AI computation occurred on specific, verified hardware. This prevents:
- Claiming on-device execution when using cloud
- Spoofing hardware capabilities
- Misrepresenting execution environment

### 4.2 Attestation Schema

```yaml
hardware_attestation:
  attestation_version: "1.0"

  # Hardware identification
  hardware:
    device_type: enum          # "apple_ane", "qualcomm_npu", "nvidia_gpu", "intel_cpu", "tpu"
    device_model: string       # e.g., "Apple M4 Pro", "Snapdragon 8 Gen 3"
    device_id: string          # Unique hardware identifier (may be anonymized)

  # Secure element attestation
  secure_element:
    type: enum                 # "secure_enclave", "tee", "tpm", "none"
    attestation_certificate: string  # X.509 certificate chain

  # Execution attestation
  execution:
    operation_type: enum       # "inference", "training", "fine_tuning"
    started_at: datetime
    completed_at: datetime
    input_hash: string         # Hash of inputs
    output_hash: string        # Hash of outputs

  # Attestation proof
  proof:
    attestation_token: string  # Signed by secure element
    signature_algorithm: string  # e.g., "ES256", "Ed25519"
    certificate_chain: [string]  # For verification

  # Optional: Performance metrics
  metrics:
    operations_per_second: float
    memory_used_bytes: integer
    energy_consumed_joules: float
```

### 4.3 Platform-Specific Attestation

#### 4.3.1 Apple Secure Enclave (ANE/Neural Engine)

```yaml
apple_attestation:
  attestation_type: "apple_app_attest"
  device_class: enum           # "iphone", "ipad", "mac"
  chip_family: string          # "M4", "A18 Pro"
  ane_available: boolean
  attestation_object: string   # Base64 App Attest attestation
  assertion: string            # Signed assertion over execution
```

#### 4.3.2 Android Trusted Execution Environment

```yaml
android_attestation:
  attestation_type: "android_key_attestation"
  security_level: enum         # "software", "tee", "strongbox"
  attestation_certificate_chain: [string]
  hardware_backed: boolean
```

#### 4.3.3 NVIDIA Confidential Computing

```yaml
nvidia_attestation:
  attestation_type: "nvidia_cc"
  gpu_model: string
  driver_version: string
  confidential_mode: boolean
  attestation_report: string   # GPU attestation report
```

### 4.4 Attestation Verification

Verifiers can validate attestation by:

1. Validating certificate chain to known root
2. Verifying signature over execution data
3. Checking hardware capabilities match claimed operations
4. Validating timestamps are consistent

---

## 5. Edge-Native Capsules

### 5.1 Design Goals

Edge-native capsules must be:
- **Compact**: <1KB for simple operations
- **Self-contained**: No network required for creation
- **Offline-signable**: Using device secure element
- **Sync-friendly**: Efficient batching when connectivity returns

### 5.2 Compact Capsule Format

```
┌────────────────────────────────────────────────────────────┐
│ UATP Edge Capsule v7.2                                     │
├────────────────────────────────────────────────────────────┤
│ Header (16 bytes)                                          │
│ ├─ Magic: "UATP" (4 bytes)                                │
│ ├─ Version: 0x0702 (2 bytes)                              │
│ ├─ Flags: (2 bytes)                                        │
│ │   ├─ bit 0: has_training_provenance                     │
│ │   ├─ bit 1: has_hardware_attestation                    │
│ │   ├─ bit 2: is_workflow_step                            │
│ │   ├─ bit 3: payload_encrypted                           │
│ │   └─ bits 4-15: reserved                                │
│ ├─ Payload Length: (4 bytes)                              │
│ └─ Reserved: (4 bytes)                                     │
├────────────────────────────────────────────────────────────┤
│ Capsule ID (32 bytes)                                      │
│ └─ SHA-256 hash serving as unique identifier              │
├────────────────────────────────────────────────────────────┤
│ Timestamp (8 bytes)                                        │
│ └─ Unix timestamp in milliseconds                         │
├────────────────────────────────────────────────────────────┤
│ Model Hash (32 bytes)                                      │
│ └─ SHA-256 of model weights                               │
├────────────────────────────────────────────────────────────┤
│ Payload (variable)                                         │
│ └─ CBOR-encoded capsule data                              │
├────────────────────────────────────────────────────────────┤
│ Signature (64 bytes for Ed25519, 2420 for ML-DSA-65)      │
│ └─ Signature over all preceding fields                    │
└────────────────────────────────────────────────────────────┘
```

### 5.3 Compression Strategies

For bandwidth-constrained sync:

1. **Delta Encoding**: Only sync changes from last known state
2. **Batching**: Aggregate multiple capsules into single payload
3. **Priority Tiers**: Critical capsules sync first

```yaml
sync_batch:
  batch_id: string
  capsule_count: integer
  total_size_bytes: integer
  compression: enum            # "none", "zstd", "lz4"
  priority: enum               # "critical", "high", "normal", "low"
  capsules: [bytes]            # Array of compact capsules
```

### 5.4 Offline Operation

Edge devices may operate offline for extended periods. UATP 7.2 supports:

1. **Local Signing**: Using device secure element
2. **Deferred Verification**: Verification happens when connectivity returns
3. **Conflict Resolution**: Deterministic ordering of offline capsules

```yaml
offline_capsule:
  created_offline: boolean
  local_signature: string      # Signed by device
  sync_status: enum            # "pending", "synced", "verified"
  sync_timestamp: datetime     # When synced to server (if applicable)
  verification_deferred: boolean
```

---

## 6. Model Registry Protocol

### 6.1 Overview

The Model Registry Protocol provides content-addressed storage and retrieval for AI models, enabling:
- Verifiable model provenance
- Fine-tune chain tracking
- License compliance verification

### 6.2 Model Manifest

```yaml
model_manifest:
  manifest_version: "1.0"

  # Model identification
  model_id: string             # Human-readable identifier
  model_hash: string           # SHA-256 of weights

  # Model metadata
  metadata:
    name: string
    version: string
    description: string
    architecture: string       # "transformer", "moe", "ssm", etc.
    parameter_count: integer
    context_length: integer

  # Provenance
  provenance:
    publisher: string
    publish_date: datetime
    parent_model: string       # Hash of parent (if fine-tuned)
    training_provenance: object  # Full training provenance (Section 2)

  # Licensing
  license:
    spdx_id: string            # e.g., "Apache-2.0"
    license_url: string
    restrictions: [string]     # Usage restrictions
    attribution_required: boolean

  # Distribution
  distribution:
    primary_uri: string        # Primary download location
    mirrors: [string]          # Alternative locations
    checksum_algorithm: string
    size_bytes: integer

  # Capabilities
  capabilities:
    languages: [string]        # Supported languages
    modalities: [string]       # "text", "image", "audio", "video"
    tool_calling: boolean
    structured_output: boolean

  # Signature
  signature:
    algorithm: string
    public_key: string
    signature: string
```

### 6.3 Registry Operations

```
# Register a new model
POST /registry/models
Body: model_manifest

# Query by hash
GET /registry/models/{model_hash}

# Query by lineage
GET /registry/models/{model_hash}/ancestors
GET /registry/models/{model_hash}/descendants

# Verify model integrity
POST /registry/verify
Body: { model_hash, weights_hash }

# Search models
GET /registry/search?license=Apache-2.0&min_params=100B
```

### 6.4 Decentralized Registry

For censorship resistance, the registry supports:
- **IPFS**: Content-addressed storage
- **Blockchain Anchoring**: Timestamping on public chains
- **Federation**: Multiple registries with cross-verification

---

## 7. Cryptographic Requirements

### 7.1 Supported Algorithms

| Purpose | Algorithm | Key Size | Notes |
|---------|-----------|----------|-------|
| Signing (Classical) | Ed25519 | 256-bit | Default for edge devices |
| Signing (Post-Quantum) | ML-DSA-65 | Level 3 | For high-security contexts |
| Hashing | SHA-256 | 256-bit | Content addressing |
| Hashing (Post-Quantum) | SHA-3-256 | 256-bit | Optional upgrade path |
| Encryption | AES-256-GCM | 256-bit | Payload encryption |
| Key Exchange | X25519 | 256-bit | Classical |
| Key Exchange (PQ) | ML-KEM-768 | Level 3 | Post-quantum |

### 7.2 Signature Requirements

All capsules MUST include a signature over:
```
signature_input = version || timestamp || capsule_id || payload_hash
```

### 7.3 Hardware-Backed Keys

Edge devices SHOULD use hardware-backed keys:
- Apple: Secure Enclave
- Android: StrongBox/TEE
- Server: HSM or TPM

---

## 8. Backward Compatibility

### 8.1 Version Negotiation

UATP 7.2 systems MUST support:
- Reading UATP 7.0 and 7.1 capsules
- Writing UATP 7.1 capsules for legacy consumers
- Graceful degradation when 7.2 features unavailable

### 8.2 Feature Detection

```yaml
capabilities:
  uatp_version: "7.2"
  features:
    training_provenance: boolean
    workflow_chains: boolean
    hardware_attestation: boolean
    edge_capsules: boolean
    model_registry: boolean
```

### 8.3 Migration Path

1. **Phase 1**: Add 7.2 fields as optional extensions
2. **Phase 2**: Encourage 7.2 adoption with tooling
3. **Phase 3**: Deprecate 7.0/7.1-only systems

---

## 9. Security Considerations

### 9.1 Threat Model

| Threat | Mitigation |
|--------|------------|
| Model weight tampering | Content-addressed hashing |
| False provenance claims | Cryptographic signatures, ZK proofs |
| Hardware spoofing | Secure element attestation |
| Offline capsule tampering | Local signatures, deferred verification |
| Privacy leakage in provenance | Redacted provenance, ZK proofs |
| Workflow manipulation | DAG integrity verification |

### 9.2 Privacy Protections

- Training data sources may be redacted
- User prompts can be hashed (not stored)
- Hardware IDs can be anonymized
- Zero-knowledge proofs for sensitive properties

### 9.3 Regulatory Alignment

UATP 7.2 supports compliance with:
- **EU AI Act**: Transparency and accountability requirements
- **GDPR**: Data provenance and consent tracking
- **California CPRA**: Automated decision disclosure
- **China AI Regulations**: Algorithm registration requirements

---

## 10. Implementation Guidelines

### 10.1 Reference Implementations

| Platform | Language | Repository |
|----------|----------|------------|
| Server | Python | uatp-capsule-engine |
| iOS/macOS | Swift | uatp-swift-sdk (planned) |
| Android | Kotlin | uatp-android-sdk (planned) |
| Browser | TypeScript | uatp-js-sdk (planned) |
| Embedded | Rust | uatp-embedded (planned) |

### 10.2 Minimum Implementation

A conforming UATP 7.2 implementation MUST:

1. Create and verify capsule signatures
2. Support Ed25519 signing
3. Generate valid capsule IDs (SHA-256)
4. Parse and emit UATP 7.2 JSON/CBOR

A conforming implementation SHOULD:

1. Support hardware attestation on capable devices
2. Implement training provenance schema
3. Support workflow chains
4. Integrate with model registry

### 10.3 Test Vectors

Test vectors for all cryptographic operations are provided in:
```
tests/vectors/uatp_7.2_test_vectors.json
```

---

## Appendix A: JSON Schema

Full JSON Schema definitions for all UATP 7.2 types are available at:
```
schemas/uatp-7.2-schema.json
```

## Appendix B: CBOR Tags

| Tag | Type |
|-----|------|
| 72001 | UATP Capsule |
| 72002 | Training Provenance |
| 72003 | Workflow Capsule |
| 72004 | Step Capsule |
| 72005 | Hardware Attestation |
| 72006 | Edge Capsule |
| 72007 | Model Manifest |

## Appendix C: Changelog

### 7.2.0-draft (March 2026)
- Initial draft specification
- Added training provenance schema
- Added agentic workflow chains
- Added hardware attestation
- Added edge-native capsules
- Added model registry protocol

---

## References

1. UATP 7.0 Alpha Release (July 2025)
2. UATP 7.1 Production Release (February 2026)
3. Apple Neural Engine Training Research (maderix/ANE)
4. Qwen 3.5 Technical Report (Alibaba, February 2026)
5. EU AI Act (2024)
6. NIST Post-Quantum Cryptography Standards (2024)

---

*This specification is a living document. Submit feedback and proposals via the UATP Working Group.*
