"""Component for creating specialized capsule types in the visualizer.

This module provides a UI form for creating different types of specialized capsules
as defined in the UATP 6.0 white paper.
"""

import uuid

import streamlit as st

# Try to import specialized engine, handle gracefully if not available
try:
    from engine.specialized_engine import SpecializedCapsuleEngine

    SPECIALIZED_ENGINE_AVAILABLE = True
except ImportError:
    SpecializedCapsuleEngine = None
    SPECIALIZED_ENGINE_AVAILABLE = False


def render_specialized_creator(engine):
    """Render the specialized capsule creation interface."""
    st.header("Create Specialized Capsule")

    # Check if specialized engine is available
    if not SPECIALIZED_ENGINE_AVAILABLE:
        st.warning("Specialized engine is not available. Using legacy capsule engine.")
        st.info("Some advanced capsule types may not be available.")
        return

    # Check if engine is a SpecializedCapsuleEngine
    is_specialized = isinstance(engine, SpecializedCapsuleEngine)

    if not is_specialized:
        st.warning(
            "[WARN] Standard capsule engine detected. Advanced capsule types are not supported."
        )
        st.info("Please restart the application to use the specialized engine.")
        return

    # Capsule type selection
    capsule_type = st.selectbox(
        "Capsule Type",
        options=[
            "Refusal",
            "Introspective",
            "Joint",
            "Meta",
            "Influence",
            "Perspective",
            "Lifecycle",
            "Embodied",
            "AncestralKnowledge",
        ],
    )

    # Common fields for all capsule types
    confidence = st.slider("Confidence", 0.0, 1.0, 0.9, 0.01)
    reasoning_trace = st.text_area("Reasoning Trace (one per line)", "")
    reasoning_list = [
        step.strip() for step in reasoning_trace.split("\n") if step.strip()
    ]

    # Create tabs for different capsule types
    if capsule_type == "Refusal":
        create_refusal_form(engine, confidence, reasoning_list)
    elif capsule_type == "Introspective":
        create_introspective_form(engine, confidence, reasoning_list)
    elif capsule_type == "Joint":
        create_joint_form(engine, confidence, reasoning_list)
    elif capsule_type == "Meta":
        create_meta_form(engine, confidence, reasoning_list)
    elif capsule_type == "Influence":
        create_influence_form(engine, confidence, reasoning_list)
    elif capsule_type == "Perspective":
        create_perspective_form(engine, confidence, reasoning_list)
    elif capsule_type == "Lifecycle":
        create_lifecycle_form(engine, confidence, reasoning_list)
    elif capsule_type == "Embodied":
        create_embodied_form(engine, confidence, reasoning_list)
    elif capsule_type == "AncestralKnowledge":
        create_ancestral_knowledge_form(engine, confidence, reasoning_list)


def create_refusal_form(engine, confidence, reasoning_list):
    """Form for creating Refusal capsules."""
    with st.form("refusal_form"):
        st.subheader("Refusal Capsule Details")

        reason = st.text_area("Reason for Rejection", "Ethical policy violation")
        policy_id = st.text_input("Ethical Policy ID", "policy-001")
        refusal_category = st.selectbox(
            "Refusal Category",
            options=["ethical", "operational", "legal", "safety", "security", "other"],
        )

        # Alternative suggestions
        alt_suggestions = st.text_area("Alternative Suggestions (one per line)")
        alt_suggestions_list = [
            s.strip() for s in alt_suggestions.split("\n") if s.strip()
        ]

        if st.form_submit_button("Create Refusal Capsule"):
            try:
                # Use the standard create_capsule method with Refusal type
                capsule = engine.create_capsule(
                    capsule_type="Refusal",
                    confidence=confidence,
                    reasoning_trace=reasoning_list
                    or ["Refusing to perform the requested action."],
                    fields={
                        "reason_for_rejection": reason,
                        "ethical_policy_id": policy_id,
                        "refusal_category": refusal_category,
                        "alternative_suggestions": alt_suggestions_list,
                    },
                )
                st.success(
                    f"[OK] Refusal Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_introspective_form(engine, confidence, reasoning_list):
    """Form for creating Introspective capsules."""
    with st.form("introspective_form"):
        st.subheader("Introspective Capsule Details")

        # Uncertainty factors
        uncertainty = st.text_area("Uncertainty Factors (one per line)")
        uncertainty_list = [u.strip() for u in uncertainty.split("\n") if u.strip()]

        # Epistemic state
        epistemic_state = st.text_area(
            "Epistemic State", "Uncertain due to limited data"
        )

        # Alternative paths
        alt_paths = st.text_area("Alternative Reasoning Paths (JSON format)")
        try:
            import json

            alt_paths_list = json.loads(alt_paths) if alt_paths else []
            if not isinstance(alt_paths_list, list):
                alt_paths_list = [alt_paths_list]
        except Exception:
            alt_paths_list = [{"path": alt_paths}] if alt_paths else []

        if st.form_submit_button("Create Introspective Capsule"):
            try:
                capsule = engine.create_capsule(
                    capsule_type="Introspective",
                    confidence=confidence,
                    reasoning_trace=reasoning_list
                    or ["Introspective analysis of reasoning process."],
                    fields={
                        "uncertainty_factors": uncertainty_list,
                        "epistemic_state": epistemic_state,
                        "alternative_paths": alt_paths_list,
                    },
                )
                st.success(
                    f"[OK] Introspective Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_joint_form(engine, confidence, reasoning_list):
    """Form for creating Joint capsules."""
    with st.form("joint_form"):
        st.subheader("Joint Capsule Details")

        human_id = st.text_input("Human ID", "user-001")
        agreement = st.text_area(
            "Agreement Terms", "Both parties agree on this decision."
        )

        # Collaboration context
        context = st.text_area(
            "Collaboration Context (JSON format)",
            '{"session": "1", "task": "decision-making"}',
        )
        try:
            import json

            context_dict = json.loads(context) if context else {}
        except Exception:
            context_dict = {"raw_context": context}

        # Mock human signature (in a real system, this would be cryptographically generated)
        human_signature = st.text_input(
            "Human Signature",
            value=f"mock-human-sig-{uuid.uuid4().hex[:8]}",
            help="In a real system, this would be cryptographically generated",
        )

        if st.form_submit_button("Create Joint Capsule"):
            try:
                capsule = engine.create_capsule(
                    capsule_type="Joint",
                    confidence=confidence,
                    reasoning_trace=reasoning_list
                    or ["Joint decision between human and AI."],
                    fields={
                        "human_id": human_id,
                        "agreement_terms": agreement,
                        "collaboration_context": context_dict,
                        "human_signature": human_signature,
                    },
                )
                st.success(f"[OK] Joint Capsule created with ID: {capsule.capsule_id}")
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_meta_form(engine, confidence, reasoning_list):
    """Form for creating Meta capsules."""
    with st.form("meta_form"):
        st.subheader("Meta Capsule Details")

        # Target capsule IDs
        target_ids = st.text_area("Target Capsule IDs (one per line)")
        target_ids_list = [tid.strip() for tid in target_ids.split("\n") if tid.strip()]

        reflection_type = st.selectbox(
            "Reflection Type",
            options=["contradiction", "drift", "quality", "ethics", "other"],
        )

        # Issues and resolutions (simple implementation, could be enhanced)
        issues = st.text_area(
            "Detected Issues (JSON format)",
            '[{"type": "contradiction", "description": "Conflicting claims"}]',
        )
        resolutions = st.text_area(
            "Suggested Resolutions (JSON format)",
            '[{"action": "clarify", "details": "Reconcile conflicting claims"}]',
        )

        try:
            import json

            issues_list = json.loads(issues) if issues else []
            resolutions_list = json.loads(resolutions) if resolutions else []
        except Exception as e:
            st.warning(f"JSON parsing error: {e}. Using fallback format.")
            issues_list = [{"description": issues}] if issues else []
            resolutions_list = [{"description": resolutions}] if resolutions else []

        if st.form_submit_button("Create Meta Capsule"):
            if not target_ids_list:
                st.error("[ERROR] At least one target capsule ID is required")
                return

            try:
                if hasattr(engine, "create_meta_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_meta_capsule(
                        target_capsule_ids=target_ids_list,
                        reflection_type=reflection_type,
                        detected_issues=issues_list,
                        suggested_resolutions=resolutions_list,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Meta reflection on {len(target_ids_list)} capsules"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="Meta",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Meta reflection on {len(target_ids_list)} capsules"],
                        fields={
                            "target_capsule_ids": target_ids_list,
                            "reflection_type": reflection_type,
                            "detected_issues": issues_list,
                            "suggested_resolutions": resolutions_list,
                        },
                    )
                st.success(f"[OK] Meta Capsule created with ID: {capsule.capsule_id}")
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_influence_form(engine, confidence, reasoning_list):
    """Form for creating Influence capsules."""
    with st.form("influence_form"):
        st.subheader("Influence Capsule Details")

        influence_type = st.selectbox(
            "Influence Type",
            options=["persuasion", "emotion", "education", "information", "other"],
        )

        target_audience = st.text_input("Target Audience", "General public")
        intended_effect = st.text_area(
            "Intended Effect", "Raise awareness about climate change"
        )

        # Ethical considerations
        considerations = st.text_area(
            "Ethical Considerations (one per line)",
            "Avoid manipulative language\nPresent balanced viewpoints\nRespect autonomy",
        )
        considerations_list = [
            c.strip() for c in considerations.split("\n") if c.strip()
        ]

        # Influence measurement
        measurements = st.text_area(
            "Influence Measurements (JSON format)",
            '{"persuasiveness": 0.7, "emotional_impact": 0.5, "information_value": 0.9}',
        )
        try:
            import json

            measurements_dict = json.loads(measurements) if measurements else {}
        except Exception:
            measurements_dict = {"raw_measurement": measurements}

        if st.form_submit_button("Create Influence Capsule"):
            try:
                if hasattr(engine, "create_influence_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_influence_capsule(
                        influence_type=influence_type,
                        target_audience=target_audience,
                        intended_effect=intended_effect,
                        ethical_considerations=considerations_list,
                        influence_measurement=measurements_dict,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Influence analysis: {intended_effect}"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="Influence",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Influence analysis: {intended_effect}"],
                        fields={
                            "influence_type": influence_type,
                            "target_audience": target_audience,
                            "intended_effect": intended_effect,
                            "ethical_considerations": considerations_list,
                            "influence_measurement": measurements_dict,
                        },
                    )
                st.success(
                    f"[OK] Influence Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_perspective_form(engine, confidence, reasoning_list):
    """Form for creating Perspective capsules."""
    with st.form("perspective_form"):
        st.subheader("Perspective Capsule Details")

        perspective_type = st.selectbox(
            "Perspective Type",
            options=[
                "epistemic",
                "cultural",
                "ideological",
                "disciplinary",
                "ethical",
                "other",
            ],
        )

        description = st.text_area(
            "Perspective Description", "Western scientific materialist perspective"
        )

        # Fork information
        is_fork = st.checkbox("Create as fork of existing capsule")
        fork_of = ""
        fork_reason = ""

        if is_fork:
            fork_of = st.text_input("Fork of Capsule ID")
            fork_reason = st.text_area("Fork Reason", "Alternative perspective needed")

        # Alternative perspectives
        alternatives = st.text_area(
            "Alternative Perspectives (JSON format)",
            '[{"type": "cultural", "description": "Indigenous knowledge framework"}]',
        )
        try:
            import json

            alternatives_list = json.loads(alternatives) if alternatives else []
        except Exception:
            alternatives_list = [{"description": alternatives}] if alternatives else []

        if st.form_submit_button("Create Perspective Capsule"):
            try:
                if hasattr(engine, "create_perspective_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_perspective_capsule(
                        perspective_type=perspective_type,
                        perspective_description=description,
                        fork_of=fork_of if is_fork and fork_of else None,
                        fork_reason=fork_reason if is_fork and fork_reason else None,
                        alternative_perspectives=alternatives_list,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Perspective declaration: {description}"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="Perspective",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Perspective declaration: {description}"],
                        fields={
                            "perspective_type": perspective_type,
                            "perspective_description": description,
                            "fork_of": fork_of if is_fork and fork_of else None,
                            "fork_reason": fork_reason
                            if is_fork and fork_reason
                            else None,
                            "alternative_perspectives": alternatives_list,
                        },
                    )
                st.success(
                    f"[OK] Perspective Capsule created with ID: {capsule.capsule_id}"
                )

                # If this is a fork, offer to simulate a perspective fork
                if (
                    is_fork
                    and fork_of
                    and hasattr(engine, "simulate_perspective_fork_with_reasoning")
                ):
                    if st.button("Simulate Perspective Fork Chain"):
                        fork_capsule = engine.simulate_perspective_fork_with_reasoning(
                            fork_reason=fork_reason,
                            perspective_type=perspective_type,
                            perspective_description=description,
                        )
                        st.success(
                            f"[OK] Perspective fork chain simulated with ID: {fork_capsule.capsule_id}"
                        )

            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_lifecycle_form(engine, confidence, reasoning_list):
    """Form for creating Lifecycle capsules."""
    with st.form("lifecycle_form"):
        st.subheader("Lifecycle Capsule Details")

        event_type = st.selectbox(
            "Event Type",
            options=[
                "startup",
                "shutdown",
                "memory_operation",
                "upgrade",
                "checkpoint",
                "other",
            ],
        )

        # Affected components
        components = st.text_area(
            "Affected Components (one per line)",
            "core_processor\nmemory_module\ninterface",
        )
        components_list = [c.strip() for c in components.split("\n") if c.strip()]

        trigger = st.text_input("Event Trigger", "User initiated shutdown")
        duration = st.text_input("Expected Duration", "30 seconds")

        # System state
        system_state = st.text_area(
            "System State (JSON format)",
            '{"cpu_usage": 0.3, "memory_usage": 0.6, "active_sessions": 2}',
        )
        try:
            import json

            state_dict = json.loads(system_state) if system_state else {}
        except Exception:
            state_dict = {"raw_state": system_state}

        if st.form_submit_button("Create Lifecycle Capsule"):
            try:
                if hasattr(engine, "create_lifecycle_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_lifecycle_capsule(
                        event_type=event_type,
                        system_state=state_dict,
                        affected_components=components_list,
                        event_trigger=trigger,
                        expected_duration=duration,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Lifecycle event: {event_type}"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="Lifecycle",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Lifecycle event: {event_type}"],
                        fields={
                            "event_type": event_type,
                            "system_state": state_dict,
                            "affected_components": components_list,
                            "event_trigger": trigger,
                            "expected_duration": duration,
                        },
                    )
                st.success(
                    f"[OK] Lifecycle Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_embodied_form(engine, confidence, reasoning_list):
    """Form for creating Embodied capsules."""
    with st.form("embodied_form"):
        st.subheader("Embodied Capsule Details")

        interaction_type = st.selectbox(
            "Interaction Type",
            options=[
                "visual",
                "auditory",
                "tactile",
                "movement",
                "multi-modal",
                "other",
            ],
        )

        # Sensor data
        sensor_data = st.text_area(
            "Sensor Data (JSON format)",
            '{"camera": "active", "microphone": "inactive", "image_data": "base64-encoded-data-would-go-here"}',
        )
        try:
            import json

            sensor_data_dict = json.loads(sensor_data) if sensor_data else {}
        except Exception:
            sensor_data_dict = {"raw_sensor_data": sensor_data}

        # Physical context
        physical_context = st.text_area(
            "Physical Context (JSON format)",
            '{"location": "indoor", "lighting": "artificial", "environment": "office"}',
        )
        try:
            import json

            context_dict = json.loads(physical_context) if physical_context else {}
        except Exception:
            context_dict = {"raw_context": physical_context}

        # Temporal sequence
        has_temporal = st.checkbox("Add temporal sequence")
        temporal_sequence = None
        if has_temporal:
            temporal_data = st.text_area(
                "Temporal Sequence (JSON format)",
                '[{"time": "t-1", "action": "detected object"}, {"time": "t", "action": "identified object"}]',
            )
            try:
                import json

                temporal_sequence = json.loads(temporal_data) if temporal_data else []
            except Exception:
                temporal_sequence = (
                    [{"sequence": temporal_data}] if temporal_data else []
                )

        # Spatial reference
        has_spatial = st.checkbox("Add spatial reference")
        spatial_reference = None
        if has_spatial:
            spatial_data = st.text_area(
                "Spatial Reference (JSON format)",
                '{"x": 10.5, "y": 20.1, "z": 0.5, "orientation": 45}',
            )
            try:
                import json

                spatial_reference = json.loads(spatial_data) if spatial_data else {}
            except Exception:
                spatial_reference = (
                    {"raw_spatial": spatial_data} if spatial_data else {}
                )

        if st.form_submit_button("Create Embodied Capsule"):
            try:
                if hasattr(engine, "create_embodied_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_embodied_capsule(
                        interaction_type=interaction_type,
                        sensor_data=sensor_data_dict,
                        physical_context=context_dict,
                        temporal_sequence=temporal_sequence,
                        spatial_reference=spatial_reference,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Physical interaction: {interaction_type}"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="Embodied",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Physical interaction: {interaction_type}"],
                        fields={
                            "interaction_type": interaction_type,
                            "sensor_data": sensor_data_dict,
                            "physical_context": context_dict,
                            "temporal_sequence": temporal_sequence,
                            "spatial_reference": spatial_reference,
                        },
                    )
                st.success(
                    f"[OK] Embodied Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")


def create_ancestral_knowledge_form(engine, confidence, reasoning_list):
    """Form for creating Ancestral Knowledge capsules."""
    with st.form("ancestral_form"):
        st.subheader("Ancestral Knowledge Capsule Details")

        knowledge_source = st.text_input(
            "Knowledge Source", "Public domain scientific literature"
        )
        knowledge_domain = st.text_input("Knowledge Domain", "Physics")

        # Attribution
        attribution = st.text_area(
            "Attribution (JSON format)",
            '[{"name": "Albert Einstein", "work": "Theory of Relativity"}, {"institution": "CERN", "publication": "Particle Data"}]',
        )
        try:
            import json

            attribution_list = json.loads(attribution) if attribution else []
            if not isinstance(attribution_list, list):
                attribution_list = [attribution_list]
        except Exception:
            attribution_list = [{"attribution": attribution}] if attribution else []

        # Access rights
        access_rights = st.text_area(
            "Access Rights (JSON format)",
            '{"license": "CC-BY-4.0", "attribution_required": true, "commercial_use": true}',
        )
        try:
            import json

            rights_dict = json.loads(access_rights) if access_rights else {}
        except Exception:
            rights_dict = {"raw_rights": access_rights}

        knowledge_confidence = st.slider("Knowledge Confidence", 0.0, 1.0, 0.95, 0.01)
        canonical_reference = st.text_input(
            "Canonical Reference", "https://example.org/reference/123"
        )

        if st.form_submit_button("Create Ancestral Knowledge Capsule"):
            try:
                if hasattr(engine, "create_ancestral_knowledge_capsule"):
                    # Use specialized method if available
                    capsule = engine.create_ancestral_knowledge_capsule(
                        knowledge_source=knowledge_source,
                        knowledge_domain=knowledge_domain,
                        attribution=attribution_list,
                        access_rights=rights_dict,
                        knowledge_confidence=knowledge_confidence,
                        canonical_reference=canonical_reference,
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Knowledge source: {knowledge_source}"],
                    )
                else:
                    # Fallback to standard method
                    capsule = engine.create_capsule(
                        capsule_type="AncestralKnowledge",
                        confidence=confidence,
                        reasoning_trace=reasoning_list
                        or [f"Knowledge source: {knowledge_source}"],
                        fields={
                            "knowledge_source": knowledge_source,
                            "knowledge_domain": knowledge_domain,
                            "attribution": attribution_list,
                            "access_rights": rights_dict,
                            "knowledge_confidence": knowledge_confidence,
                            "canonical_reference": canonical_reference,
                        },
                    )
                st.success(
                    f"[OK] Ancestral Knowledge Capsule created with ID: {capsule.capsule_id}"
                )
            except Exception as e:
                st.error(f"[ERROR] Error creating capsule: {str(e)}")
