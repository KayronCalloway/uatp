# UATP 7.0 Specialized Capsule Types

This document provides detailed information about the specialized capsule types introduced in UATP 7.0, including their purpose, required fields, and usage examples.

## Table of Contents
1. [Governance Capsules](#governance-capsules)
2. [Economic Capsules](#economic-capsules)
3. [Consent Capsules](#consent-capsules)
4. [Trust Renewal Capsules](#trust-renewal-capsules)
5. [Value Inception Capsules](#value-inception-capsules)
6. [Temporal Signature Capsules](#temporal-signature-capsules)
7. [Remix Capsules](#remix-capsules)
8. [Self-Hallucination Capsules](#self-hallucination-capsules)
9. [Simulated Malice Capsules](#simulated-malice-capsules)
10. [Implicit Consent Capsules](#implicit-consent-capsules)
11. [Capsule Expiration Capsules](#capsule-expiration-capsules)

## Governance Capsules

Governance capsules record policy decisions, stakeholder votes, and implementation processes for protocol governance actions.

### Required Fields
- `governance_type`: Type of governance activity (e.g., "Protocol Update", "Policy Change")
- `policy_id`: ID of the policy being created or modified
- `decision_makers`: List of IDs of decision makers/stakeholders
- `decision_rationale`: Rationale for the governance decision
- `affected_scopes`: List of areas affected by the decision
- `governance_details`: Dictionary containing governance metadata
- `signature`: Cryptographic signature validating the governance action

### Optional Fields
- `voting_results`: Results of voting process (counts, approval rate, etc.)
- `governance_action`: Human-readable description of the action
- `action_details`: Structured details about the action (policy info, rationale, scope, timeline, impact)
- `affected_entities`: Detailed list of specific entities affected
- `stakeholder_votes`: Individual votes from each stakeholder
- `authorization_proof`: Cryptographic proof of authorization for the action
- `implementation_status`: Current status of implementation
- `implementation_timeline`: Timeline for implementation steps
- `implementation_details`: Resources, dependencies, and other implementation data
- `document_references`: References to related documentation

### Example
```python
governance_capsule = GovernanceCapsule(
    schema_version="1.0",
    capsule_id="gov-12345",
    capsule_type="Governance",
    agent_id="gov-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Policy analysis", "Stakeholder consultation", "Impact assessment"],
    metadata={"priority": "high"},
    governance_type="Protocol Update",
    policy_id="POLICY-2025-001",
    decision_makers=["Security Council", "API Team"],
    decision_rationale="Enhanced security requirements",
    affected_scopes=["authentication", "api"],
    governance_details={"version": "1.2"},
    signature="valid-signature-hash"
)
```

## Economic Capsules

Economic capsules manage value attribution and dividend calculation for multi-agent contributions.

### Required Fields
- `economic_event_type`: Type of economic event (e.g., "Attribution", "Compensation")
- `value_amount`: Amount of value being attributed or distributed
- `value_recipients`: Dictionary mapping recipients to their value shares
- `value_calculation_method`: Method used to calculate value distribution
- `dividend_distribution`: Dictionary mapping recipients to dividend amounts
- `economic_value`: Dictionary containing economic value metadata

### Optional Fields
- `transaction_reference`: Reference to an external transaction ID or record

### Example
```python
economic_capsule = EconomicCapsule(
    schema_version="1.0",
    capsule_id="econ-12345",
    capsule_type="Economic",
    agent_id="econ-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Contribution assessment", "Value calculation"],
    metadata={"currency": "USD"},
    economic_event_type="Attribution",
    value_amount=100.0,
    value_recipients={"agent-001": 0.6, "agent-002": 0.4},
    value_calculation_method="Proportional Contribution",
    dividend_distribution={"agent-001": 60.0, "agent-002": 40.0},
    economic_value={"total_distribution": 100.0},
    transaction_reference="tx-54321"
)
```

## Consent Capsules

Consent capsules track explicit permission for specific actions with duration and revocation support.

### Required Fields
- `consent_provider`: ID of the entity providing consent
- `consent_requester`: ID of the entity requesting consent
- `consent_purpose`: Purpose for which consent is provided
- `consent_scope`: Scope of actions permitted under this consent
- `consent_timestamp`: When consent was provided
- `consent_duration`: How long consent is valid for (ISO 8601 duration)
- `consent_terms`: The specific terms of consent

### Optional Fields
- `revocable`: Whether consent can be revoked (boolean)
- `revocation_method`: Method to revoke consent if applicable
- `consent_receipt`: Receipt or proof of consent
- `consent_verification`: Verification method for consent

### Example
```python
consent_capsule = ConsentCapsule(
    schema_version="1.0",
    capsule_id="consent-12345",
    capsule_type="Consent",
    agent_id="consent-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Consent request", "Verification of identity", "Consent receipt"],
    metadata={"consent_version": "2.1"},
    consent_provider="user-jane-doe",
    consent_requester="service-analytics",
    consent_purpose="Data analysis for service improvement",
    consent_scope=["usage_data", "performance_metrics"],
    consent_timestamp="2025-07-01T12:00:00Z",
    consent_duration="P90D",  # 90 days in ISO 8601 duration format
    consent_terms="All data will be anonymized and used only for service improvements",
    revocable=True,
    revocation_method="API call to /revoke with consent_id",
    consent_receipt="receipt-hash-67890"
)
```

## Trust Renewal Capsules

Trust renewal capsules handle periodic trust verification and credential re-validation.

### Required Fields
- `trust_context`: Context in which trust is being renewed
- `verification_timestamp`: When verification was performed
- `verified_claims`: List of claims that were verified
- `trust_level`: Numeric or categorical trust level assigned
- `renewal_period`: Period for which trust is renewed (ISO 8601 duration)
- `verification_method`: Method used to verify trust

### Optional Fields
- `previous_trust_level`: Trust level before renewal
- `trust_change_reason`: Reason for any change in trust level
- `verification_evidence`: Evidence supporting verification
- `trust_metrics`: Detailed metrics used for trust assessment

### Example
```python
trust_renewal_capsule = TrustRenewalCapsule(
    schema_version="1.0",
    capsule_id="trust-12345",
    capsule_type="TrustRenewal",
    agent_id="trust-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Credential verification", "History analysis", "Trust calculation"],
    metadata={"renewal_type": "scheduled"},
    trust_context="API access privileges",
    verification_timestamp="2025-07-01T11:30:00Z",
    verified_claims=[
        {"claim_type": "identity", "status": "verified"},
        {"claim_type": "credentials", "status": "verified"},
        {"claim_type": "history", "status": "verified"}
    ],
    trust_level=0.85,
    renewal_period="P180D",  # 180 days in ISO 8601 duration format
    verification_method="Multi-factor authentication + history review",
    previous_trust_level=0.80,
    trust_change_reason="Improved history of responsible usage",
    verification_evidence="evidence-hash-67890"
)
```

## Value Inception Capsules

Value inception capsules record ethical justifications and value alignment decisions.

### Required Fields
- `value_framework`: Ethical framework being used
- `value_assertions`: List of value assertions made
- `ethical_justification`: Justification for ethical decisions
- `stakeholder_considerations`: Considerations for different stakeholders
- `values_hierarchy`: Hierarchical structure of values
- `trade_offs`: Ethical trade-offs considered

### Example
```python
value_inception_capsule = ValueInceptionCapsule(
    schema_version="1.0",
    capsule_id="value-12345",
    capsule_type="ValueInception",
    agent_id="ethics-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Ethical analysis", "Stakeholder impact assessment", "Value prioritization"],
    metadata={"ethics_version": "3.2"},
    value_framework="Principlist Ethics",
    value_assertions=["Privacy is essential", "Transparency builds trust", "User autonomy must be preserved"],
    ethical_justification="The recommendation optimizes for user autonomy while ensuring sufficient privacy safeguards",
    stakeholder_considerations={
        "users": "Privacy and control over data",
        "service_providers": "Viable business model with ethical constraints",
        "regulators": "Compliance with privacy regulations"
    },
    values_hierarchy=[
        {"value": "autonomy", "priority": 1},
        {"value": "privacy", "priority": 2},
        {"value": "efficiency", "priority": 3}
    ],
    trade_offs=[
        {"values": ["efficiency", "privacy"], "resolution": "Prioritize privacy at cost of reduced efficiency"}
    ]
)
```

## Temporal Signature Capsules

Temporal signature capsules establish time-bound validity for knowledge claims.

### Required Fields
- `knowledge_claim`: The specific knowledge claim being made
- `knowledge_domain`: Domain to which the knowledge applies
- `knowledge_timestamp`: When the knowledge was acquired/valid
- `knowledge_cutoff_date`: Date after which knowledge may be obsolete
- `temporal_scope`: Scope of time for which the knowledge is valid

### Optional Fields
- `confidence_over_time`: How confidence decays over time
- `update_triggers`: Events that would trigger knowledge update
- `update_source`: Where updates to this knowledge would come from

### Example
```python
temporal_signature_capsule = TemporalSignatureCapsule(
    schema_version="1.0",
    capsule_id="temporal-12345",
    capsule_type="TemporalSignature",
    agent_id="knowledge-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Knowledge acquisition", "Temporal boundary analysis"],
    metadata={"knowledge_source": "financial_database"},
    knowledge_claim="Company X has a P/E ratio of 15.3",
    knowledge_domain="Financial Markets",
    knowledge_timestamp="2025-07-01T09:30:00Z",
    knowledge_cutoff_date="2025-07-02T00:00:00Z",
    temporal_scope="Trading day 2025-07-01",
    confidence_over_time={"initial": 0.95, "24h": 0.7, "48h": 0.3},
    update_triggers=["Market close", "Earnings report", "Significant news"],
    update_source="Financial data API endpoint /company/X/metrics"
)
```

## Remix Capsules

Remix capsules provide attribution for derivative content creation.

### Required Fields
- `source_contents`: List of source content identifiers
- `contribution_type`: Type of contribution to each source
- `transformation_description`: Description of how sources were transformed
- `attribution_method`: Method used for attribution
- `attribution_rationale`: Rationale for the attribution approach

### Optional Fields
- `license_implications`: Implications for licensing of the remix
- `permission_status`: Status of permissions for using sources

### Example
```python
remix_capsule = RemixCapsule(
    schema_version="1.0",
    capsule_id="remix-12345",
    capsule_type="Remix",
    agent_id="content-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Source identification", "Transformation analysis", "Attribution determination"],
    metadata={"remix_type": "content_synthesis"},
    source_contents=["content-id-123", "content-id-456", "content-id-789"],
    contribution_type={
        "content-id-123": "primary_structure",
        "content-id-456": "supporting_evidence",
        "content-id-789": "contrasting_viewpoint"
    },
    transformation_description="Synthesized multiple viewpoints into a balanced analysis with novel insights",
    attribution_method="Explicit in-text citation with percentage contribution",
    attribution_rationale="Each source contributed distinct elements requiring specific attribution",
    license_implications={
        "content-id-123": "CC-BY compatible",
        "content-id-456": "CC-BY compatible",
        "content-id-789": "CC-BY-NC requires non-commercial use"
    },
    permission_status="All permissions verified"
)
```

## Self-Hallucination Capsules

Self-hallucination capsules record instances where an agent identifies its own factual fabrication or uncertainty.

### Required Fields
- `hallucination_type`: Type of hallucination detected
- `affected_content`: Content affected by the hallucination
- `confidence_assessment`: Assessment of confidence in different parts
- `detection_method`: Method used to detect the hallucination
- `self_hallucination_markers`: Markers indicating hallucination

### Optional Fields
- `corrective_action`: Action taken to correct the hallucination

### Example
```python
self_hallucination_capsule = SelfHallucinationCapsule(
    schema_version="1.0",
    capsule_id="hallucination-12345",
    capsule_type="SelfHallucination",
    agent_id="reasoning-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Response generation", "Self-verification", "Hallucination detection"],
    metadata={"response_id": "resp-67890"},
    hallucination_type="Factual Fabrication",
    affected_content="The statement that 'Company X released their Q2 earnings yesterday' is incorrect",
    confidence_assessment={
        "company_exists": 0.99,
        "earnings_relevance": 0.95,
        "date_accuracy": 0.15
    },
    detection_method="Internal knowledge-base cross-reference",
    self_hallucination_markers=[
        {"marker": "temporal_contradiction", "severity": "high"},
        {"marker": "source_absence", "severity": "high"}
    ],
    corrective_action="Revised statement to indicate that Q2 earnings are scheduled for next month"
)
```

## Simulated Malice Capsules

Simulated malice capsules document red-team and adversarial testing processes.

### Required Fields
- `simulation_type`: Type of malicious behavior being simulated
- `simulation_target`: Target of the simulated malice
- `simulation_constraints`: Constraints placed on the simulation
- `simulation_justification`: Justification for performing the simulation
- `safety_measures`: Measures in place to ensure safety
- `authorization`: Authorization for the simulation

### Optional Fields
- `simulation_results`: Results of the simulation
- `discovered_vulnerabilities`: Vulnerabilities discovered
- `remediation_recommendations`: Recommendations for remediation

### Example
```python
simulated_malice_capsule = SimulatedMaliceCapsule(
    schema_version="1.0",
    capsule_id="malice-12345",
    capsule_type="SimulatedMalice",
    agent_id="redteam-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Vulnerability hypothesis", "Attack vector identification", "Exploitation attempt"],
    metadata={"test_session": "redteam-session-001"},
    simulation_type="Prompt Injection Attack",
    simulation_target="Content Filtering System",
    simulation_constraints=["No actual data exfiltration", "System contained in sandbox", "No impact on production"],
    simulation_justification="Identify vulnerabilities in content filtering before deployment",
    safety_measures=["Sandboxed environment", "Monitored execution", "Pre-approved test cases only"],
    authorization={
        "authorized_by": "Security Council",
        "authorization_id": "auth-54321",
        "scope": "Content filtering subsystem only"
    },
    simulation_results="Successfully bypassed filter using specific character sequences",
    discovered_vulnerabilities=[
        {"id": "vuln-001", "severity": "high", "description": "Unicode character normalization bypass"}
    ],
    remediation_recommendations=["Implement unicode normalization before filtering", "Add pattern detection for evasion techniques"]
)
```

## Implicit Consent Capsules

Implicit consent capsules track implied consent derived from user behavior.

### Required Fields
- `consent_context`: Context in which implicit consent is inferred
- `observed_behaviors`: Behaviors observed that imply consent
- `inference_justification`: Justification for inferring consent
- `inference_confidence`: Confidence in the consent inference
- `consent_scope`: Scope of actions covered by implicit consent
- `consent_limitations`: Limitations on the inferred consent

### Optional Fields
- `related_explicit_consent`: References to related explicit consent
- `expiration_conditions`: Conditions that would invalidate consent

### Example
```python
implicit_consent_capsule = ImplicitConsentCapsule(
    schema_version="1.0",
    capsule_id="implicit-12345",
    capsule_type="ImplicitConsent",
    agent_id="consent-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.90,
    reasoning_trace=["Behavior analysis", "Pattern recognition", "Consent inference"],
    metadata={"user_id": "user-67890"},
    consent_context="Feature recommendations based on usage patterns",
    observed_behaviors=[
        {"behavior": "Frequent manual filtering of content type X", "frequency": "daily", "duration": "3 weeks"},
        {"behavior": "Manual creation of collections for filtered content", "frequency": "weekly"}
    ],
    inference_justification="Consistent pattern of content organization indicates preference for automated assistance",
    inference_confidence=0.85,
    consent_scope=["Suggest filters", "Recommend organization", "Highlight similar content"],
    consent_limitations=["No automatic application of filters", "No sharing of filtering preferences"],
    related_explicit_consent="explicit-consent-54321",
    expiration_conditions=["14 days of inactivity", "Explicit opt-out", "Dismissal of 3 consecutive suggestions"]
)
```

## Capsule Expiration Capsules

Capsule expiration capsules define time-based or condition-based validity periods for other capsules.

### Required Fields
- `target_capsule_ids`: List of capsule IDs affected by expiration
- `expiration_type`: Type of expiration (time-based, condition-based)
- `expiration_value`: Value that defines when expiration occurs
- `expiration_effect`: Effect of expiration on target capsules

### Optional Fields
- `expiration_notification`: When/how to notify about approaching expiration
- `renewal_process`: Process for renewal if applicable
- `grace_period`: Additional period after expiration

### Example
```python
capsule_expiration_capsule = CapsuleExpirationCapsule(
    schema_version="1.0",
    capsule_id="expiration-12345",
    capsule_type="CapsuleExpiration",
    agent_id="lifecycle-agent-001",
    timestamp="2025-07-01T12:00:00Z",
    confidence=0.95,
    reasoning_trace=["Lifecycle analysis", "Expiration determination"],
    metadata={"policy_reference": "data-retention-policy-v3"},
    target_capsule_ids=["consent-67890", "knowledge-54321"],
    expiration_type="time-based",
    expiration_value="2025-10-01T00:00:00Z",
    expiration_effect="invalidate",
    expiration_notification={
        "timing": "P7D",  # 7 days before in ISO 8601 duration format
        "method": "system notification",
        "recipients": ["data-owner", "system-admin"]
    },
    renewal_process="Submit new consent through /api/consent endpoint",
    grace_period="P3D"  # 3 days in ISO 8601 duration format
)
```
