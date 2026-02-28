"""Swagger documentation for UATP 7.0 API endpoints.

This module creates Swagger/OpenAPI documentation for the UATP 7.0 API endpoints.
"""

from flask_restx import Api, Namespace, Resource, fields


def create_swagger_docs(app):
    """Create Swagger documentation for UATP 7.0 API endpoints."""
    # Create API with metadata
    api = Api(
        app,
        version="7.1",
        title="UATP Capsule Engine API",
        description="API for creating and managing UATP 7.0 capsules",
        doc="/docs",
        authorizations={
            "apikey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
        },
        security="apikey",
    )

    # Create namespaces
    uatp7_ns = Namespace("v7", description="UATP 7.0 API endpoints")
    api.add_namespace(uatp7_ns, path="/v7")

    # Common models
    base_request = api.model(
        "BaseRequest",
        {
            "confidence": fields.Float(
                description="Confidence level (0.0 to 1.0)", example=0.9
            ),
            "reasoning_trace": fields.List(
                fields.String, description="List of reasoning steps"
            ),
        },
    )

    base_response = api.model(
        "BaseResponse",
        {
            "status": fields.String(
                description="Status of the request", example="success"
            ),
            "capsule_id": fields.String(description="ID of the created capsule"),
            "capsule": fields.Raw(description="Full capsule data"),
        },
    )

    error_response = api.model(
        "ErrorResponse",
        {
            "error": fields.String(description="Error message"),
            "error_type": fields.String(
                description="Type of error",
                enum=[
                    "invalid_request",
                    "invalid_parameter",
                    "validation_error",
                    "signing_error",
                    "logging_error",
                    "engine_error",
                    "unexpected_error",
                ],
            ),
        },
    )

    # Remix capsule models
    remix_request = api.clone(
        "RemixRequest",
        base_request,
        {
            "source_capsule_ids": fields.List(
                fields.String,
                required=True,
                description="List of capsule IDs being remixed",
            ),
            "remix_type": fields.String(
                required=True, description="Type of remix", example="derivative"
            ),
            "attribution_weights": fields.Raw(
                required=True, description="Dictionary mapping capsule IDs to weights"
            ),
            "license_type": fields.String(
                required=True, description="Type of license", example="CC-BY-4.0"
            ),
            "economic_terms": fields.Raw(description="Optional economic terms"),
        },
    )

    # Temporal signature capsule models
    temporal_request = api.clone(
        "TemporalSignatureRequest",
        base_request,
        {
            "knowledge_cutoff_date": fields.String(
                required=True,
                description="ISO format date of knowledge cutoff",
                example="2025-06-01T00:00:00Z",
            ),
            "runtime_date": fields.String(
                required=True,
                description="ISO format date of runtime",
                example="2025-07-04T00:00:00Z",
            ),
            "temporal_context": fields.Raw(
                required=True, description="Dictionary with temporal context"
            ),
        },
    )

    # Value inception capsule models
    value_request = api.clone(
        "ValueInceptionRequest",
        base_request,
        {
            "value_framework": fields.String(
                required=True, description="Ethical framework used"
            ),
            "value_assertions": fields.List(
                fields.Raw, required=True, description="List of value assertions"
            ),
            "ethical_justification": fields.String(
                required=True, description="Justification for values"
            ),
            "stakeholder_considerations": fields.Raw(
                required=True, description="Stakeholder impact assessment"
            ),
            "values_hierarchy": fields.Raw(
                required=True, description="Hierarchy of values"
            ),
            "trade_offs": fields.Raw(
                required=True, description="Value trade-offs made"
            ),
        },
    )

    # Self-hallucination capsule models
    hallucination_request = api.clone(
        "SelfHallucinationRequest",
        base_request,
        {
            "hallucination_type": fields.String(
                required=True,
                description="Type of hallucination",
                enum=["factual_error", "memory_fabrication", "contextual_confusion"],
            ),
            "affected_content": fields.Raw(
                required=True, description="Content affected by hallucination"
            ),
            "confidence_assessment": fields.Raw(
                required=True, description="Assessment of confidence"
            ),
            "detection_method": fields.String(
                required=True, description="Method used to detect hallucination"
            ),
            "corrective_action": fields.String(
                description="Action taken to correct hallucination"
            ),
            "self_hallucination_markers": fields.Raw(
                description="Markers indicating hallucination"
            ),
        },
    )

    # Simulated Malice capsule models
    simulated_malice_request = api.clone(
        "SimulatedMaliceRequest",
        base_request,
        {
            "simulation_type": fields.String(
                required=True,
                description="Type of malicious behavior being simulated",
                enum=[
                    "prompt_injection",
                    "jailbreak",
                    "data_poisoning",
                    "social_engineering",
                    "model_evasion",
                    "other",
                ],
            ),
            "target_system": fields.String(
                required=True, description="System targeted by the simulation"
            ),
            "ethical_boundaries": fields.List(
                fields.String,
                required=True,
                description="Ethical boundaries for the simulation",
            ),
            "simulation_parameters": fields.Raw(
                required=True, description="Parameters of the simulation"
            ),
            "containment_measures": fields.List(
                fields.String,
                required=True,
                description="Measures to contain the simulation",
            ),
            "authorization": fields.Raw(
                required=True, description="Authorization for the simulation"
            ),
        },
    )

    # Implicit Consent capsule models
    implicit_consent_request = api.clone(
        "ImplicitConsentRequest",
        base_request,
        {
            "action_taken": fields.String(
                required=True, description="Action taken without explicit consent"
            ),
            "justification": fields.String(
                required=True,
                description="Justification for taking action without consent",
            ),
            "risk_assessment": fields.Raw(
                required=True, description="Assessment of risks"
            ),
            "benefit_assessment": fields.Raw(
                required=True, description="Assessment of benefits"
            ),
            "context": fields.String(
                required=True, description="Context in which action was taken"
            ),
            "alternatives_considered": fields.List(
                fields.String, description="Alternative actions that were considered"
            ),
        },
    )

    # Consent capsule models
    consent_request = api.clone(
        "ConsentRequest",
        base_request,
        {
            "consent_provider": fields.String(
                required=True, description="ID of the entity providing consent"
            ),
            "consent_scope": fields.String(
                required=True, description="Scope of the consent"
            ),
            "consent_duration": fields.String(
                required=True,
                description='Duration of consent (ISO duration or "indefinite")',
            ),
            "consent_context": fields.String(
                required=True, description="Context in which consent was given"
            ),
            "consent_timestamp": fields.String(
                required=True, description="Timestamp when consent was given"
            ),
            "consent_verification_method": fields.String(
                required=True, description="Method used to verify consent"
            ),
            "revocable": fields.Boolean(description="Whether consent can be revoked"),
            "conditions": fields.List(
                fields.String, description="Conditions for consent"
            ),
            "consent_details": fields.Raw(
                required=True, description="Detailed consent information"
            ),
        },
    )

    # Trust Renewal capsule models
    trust_renewal_request = api.clone(
        "TrustRenewalRequest",
        base_request,
        {
            "renewal_type": fields.String(
                required=True, description="Type of trust renewal"
            ),
            "verified_claims": fields.List(
                fields.Raw, required=True, description="Claims that have been verified"
            ),
            "verification_methods": fields.List(
                fields.String,
                required=True,
                description="Methods used for verification",
            ),
            "renewal_period": fields.Raw(
                required=True, description="Period of renewal"
            ),
            "evidence": fields.Raw(
                required=True, description="Evidence supporting renewal"
            ),
            "verification_authority": fields.String(
                required=True, description="Authority performing verification"
            ),
            "trust_metrics": fields.Raw(
                required=True, description="Metrics for trust assessment"
            ),
            "renewal_context": fields.Raw(
                required=True, description="Context of renewal"
            ),
        },
    )

    # Capsule Expiration models
    capsule_expiration_request = api.clone(
        "CapsuleExpirationRequest",
        base_request,
        {
            "target_capsule_ids": fields.List(
                fields.String, required=True, description="IDs of capsules to expire"
            ),
            "expiration_type": fields.String(
                required=True,
                description="Type of expiration",
                enum=[
                    "superseded",
                    "deprecated",
                    "revoked",
                    "expired",
                    "compromised",
                    "obsolete",
                ],
            ),
            "expiration_date": fields.String(
                required=True, description="Date of expiration (ISO format)"
            ),
            "expiration_reason": fields.String(
                required=True, description="Reason for expiration"
            ),
            "replacement_capsule_id": fields.String(
                description="ID of replacement capsule"
            ),
            "expiration_note": fields.String(
                description="Additional notes about expiration"
            ),
            "expiration_impact": fields.Raw(
                required=True, description="Impact of expiration"
            ),
            "expiration_effect": fields.Raw(description="Effect of expiration"),
        },
    )

    # Governance capsule models
    governance_request = api.clone(
        "GovernanceRequest",
        base_request,
        {
            "governance_type": fields.String(
                required=True,
                description="Type of governance activity",
                enum=[
                    "policy_creation",
                    "policy_amendment",
                    "dispute_resolution",
                    "membership_change",
                    "sanctions",
                    "parameter_change",
                ],
            ),
            "policy_id": fields.String(required=True, description="ID of the policy"),
            "decision_makers": fields.List(
                fields.String, required=True, description="IDs of decision makers"
            ),
            "decision_rationale": fields.String(
                required=True, description="Rationale for the decision"
            ),
            "affected_scopes": fields.List(
                fields.String,
                required=True,
                description="Scopes affected by the decision",
            ),
            "voting_results": fields.Raw(description="Results of voting"),
            "governance_details": fields.Raw(
                required=True, description="Governance metadata"
            ),
        },
    )

    # Economic capsule models
    economic_request = api.clone(
        "EconomicRequest",
        base_request,
        {
            "economic_event_type": fields.String(
                required=True, description="Type of economic event"
            ),
            "value_amount": fields.Float(required=True, description="Amount of value"),
            "value_recipients": fields.Raw(
                required=True, description="Recipients and their shares"
            ),
            "value_calculation_method": fields.String(
                required=True, description="Method used to calculate value"
            ),
            "transaction_reference": fields.String(
                description="Reference to a transaction"
            ),
            "dividend_distribution": fields.Raw(
                required=True,
                description="Distribution of dividends (must sum to ~1.0)",
            ),
            "economic_value": fields.Raw(
                required=True, description="Economic metadata"
            ),
        },
    )

    # Register API endpoints with their models

    # Remix endpoint
    @uatp7_ns.route("/remix")
    class RemixAPI(Resource):
        @uatp7_ns.doc("create_remix_capsule", security="apikey")
        @uatp7_ns.expect(remix_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Remix capsule tracking attribution and licensing"""
            pass  # Implementation is in the blueprint

    # Temporal signature endpoint
    @uatp7_ns.route("/temporal-signature")
    class TemporalSignatureAPI(Resource):
        @uatp7_ns.doc("create_temporal_signature_capsule", security="apikey")
        @uatp7_ns.expect(temporal_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Temporal Signature capsule marking knowledge boundaries"""
            pass  # Implementation is in the blueprint

    # Value inception endpoint
    @uatp7_ns.route("/value-inception")
    class ValueInceptionAPI(Resource):
        @uatp7_ns.doc("create_value_inception_capsule", security="apikey")
        @uatp7_ns.expect(value_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Value Inception capsule recording ethical justification"""
            pass  # Implementation is in the blueprint

    # Self hallucination endpoint
    @uatp7_ns.route("/self-hallucination")
    class SelfHallucinationAPI(Resource):
        @uatp7_ns.doc("create_self_hallucination_capsule", security="apikey")
        @uatp7_ns.expect(hallucination_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Self Hallucination capsule for recording self-identified fabrications"""
            pass  # Implementation is in the blueprint

    # Simulated malice endpoint
    @uatp7_ns.route("/simulated-malice")
    class SimulatedMaliceAPI(Resource):
        @uatp7_ns.doc("create_simulated_malice_capsule", security="apikey")
        @uatp7_ns.expect(simulated_malice_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Simulated Malice capsule for adversarial testing"""
            pass  # Implementation is in the blueprint

    # Implicit consent endpoint
    @uatp7_ns.route("/implicit-consent")
    class ImplicitConsentAPI(Resource):
        @uatp7_ns.doc("create_implicit_consent_capsule", security="apikey")
        @uatp7_ns.expect(implicit_consent_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create an Implicit Consent capsule logging actions where consent was bypassed"""
            pass  # Implementation is in the blueprint

    # Consent endpoint
    @uatp7_ns.route("/consent")
    class ConsentAPI(Resource):
        @uatp7_ns.doc("create_consent_capsule", security="apikey")
        @uatp7_ns.expect(consent_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Consent capsule documenting explicit permission"""
            pass  # Implementation is in the blueprint

    # Trust renewal endpoint
    @uatp7_ns.route("/trust-renewal")
    class TrustRenewalAPI(Resource):
        @uatp7_ns.doc("create_trust_renewal_capsule", security="apikey")
        @uatp7_ns.expect(trust_renewal_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Trust Renewal capsule verifying continued reliability"""
            pass  # Implementation is in the blueprint

    # Capsule expiration endpoint
    @uatp7_ns.route("/capsule-expiration")
    class CapsuleExpirationAPI(Resource):
        @uatp7_ns.doc("create_capsule_expiration_capsule", security="apikey")
        @uatp7_ns.expect(capsule_expiration_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Capsule Expiration capsule marking end-of-life for other capsules"""
            pass  # Implementation is in the blueprint

    # Governance endpoint
    @uatp7_ns.route("/governance")
    class GovernanceAPI(Resource):
        @uatp7_ns.doc("create_governance_capsule", security="apikey")
        @uatp7_ns.expect(governance_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create a Governance capsule documenting federated decision-making"""
            pass  # Implementation is in the blueprint

    # Economic endpoint
    @uatp7_ns.route("/economic")
    class EconomicAPI(Resource):
        @uatp7_ns.doc("create_economic_capsule", security="apikey")
        @uatp7_ns.expect(economic_request)
        @uatp7_ns.response(200, "Success", base_response)
        @uatp7_ns.response(400, "Invalid request", error_response)
        @uatp7_ns.response(401, "Unauthorized", error_response)
        def post(self):
            """Create an Economic capsule recording value exchanges and attribution"""
            pass  # Implementation is in the blueprint

    return api
