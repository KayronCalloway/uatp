"""
Uncertainty Quantification
Bayesian confidence intervals, risk estimation, and probability distributions
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class UncertaintyEstimate:
    """Comprehensive uncertainty estimate for a prediction or reasoning step."""

    point_estimate: float  # Single best guess (mean/median)
    confidence_interval: Tuple[float, float]  # (lower, upper) bounds
    credible_interval: Tuple[float, float]  # Bayesian credible interval
    confidence_level: float  # 0.95 for 95% CI

    # Uncertainty decomposition
    epistemic_uncertainty: float  # Uncertainty due to lack of knowledge
    aleatoric_uncertainty: float  # Irreducible randomness
    total_uncertainty: float  # Combined uncertainty

    # Risk metrics
    risk_score: float  # Overall risk level (0-1)
    worst_case: float  # Pessimistic estimate
    best_case: float  # Optimistic estimate

    # Distribution characteristics
    variance: float
    skewness: float  # Asymmetry of distribution
    is_symmetric: bool


@dataclass
class RiskAssessment:
    """Assessment of risks in a reasoning chain."""

    overall_risk: float  # 0 (low) to 1 (high)
    risk_factors: List[Dict[str, Any]]  # Identified risk factors
    risk_mitigation: List[str]  # Suggested mitigations
    confidence_in_assessment: float


class UncertaintyQuantifier:
    """
    Quantifies uncertainty in reasoning and predictions using Bayesian methods.
    """

    @staticmethod
    def estimate_confidence_uncertainty(
        confidence: float,
        sample_size: int = 10,
        prior_mean: float = 0.8,
        prior_strength: float = 5.0,
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty around a confidence score using Bayesian inference.

        Uses Beta distribution as conjugate prior for binary outcomes.

        Args:
            confidence: Point estimate of confidence
            sample_size: Number of observations
            prior_mean: Prior expected confidence
            prior_strength: Strength of prior belief

        Returns:
            UncertaintyEstimate with intervals and risk metrics
        """
        # Convert prior to Beta parameters
        alpha_prior = prior_mean * prior_strength
        beta_prior = (1 - prior_mean) * prior_strength

        # Update with observed data (approximate)
        successes = confidence * sample_size
        failures = (1 - confidence) * sample_size

        alpha_post = alpha_prior + successes
        beta_post = beta_prior + failures

        # Posterior mean
        posterior_mean = alpha_post / (alpha_post + beta_post)

        # Posterior variance
        n = alpha_post + beta_post
        variance = (alpha_post * beta_post) / (n * n * (n + 1))
        std_dev = math.sqrt(variance)

        # 95% credible interval (approximation using normal)
        z_score = 1.96  # 95% confidence
        ci_lower = max(0.0, posterior_mean - z_score * std_dev)
        ci_upper = min(1.0, posterior_mean + z_score * std_dev)

        # Decompose uncertainty
        # Epistemic: uncertainty due to limited data (reduces with more data)
        epistemic = std_dev * math.sqrt(prior_strength / (prior_strength + sample_size))

        # Aleatoric: irreducible uncertainty
        aleatoric = std_dev * math.sqrt(sample_size / (prior_strength + sample_size))

        total_uncertainty = std_dev

        # Risk score: how much could we be wrong?
        risk_score = min(1.0, std_dev * 3)  # 3-sigma rule

        # Worst/best case (10th and 90th percentiles approximation)
        z_10 = 1.28
        worst_case = max(0.0, posterior_mean - z_10 * std_dev)
        best_case = min(1.0, posterior_mean + z_10 * std_dev)

        # Skewness (for Beta distribution)
        skewness_val = (2 * (beta_post - alpha_post) * math.sqrt(n + 1)) / (
            (n + 2) * math.sqrt(alpha_post * beta_post)
        )

        return UncertaintyEstimate(
            point_estimate=posterior_mean,
            confidence_interval=(ci_lower, ci_upper),
            credible_interval=(ci_lower, ci_upper),
            confidence_level=0.95,
            epistemic_uncertainty=epistemic,
            aleatoric_uncertainty=aleatoric,
            total_uncertainty=total_uncertainty,
            risk_score=risk_score,
            worst_case=worst_case,
            best_case=best_case,
            variance=variance,
            skewness=skewness_val,
            is_symmetric=abs(skewness_val) < 0.1,
        )

    @staticmethod
    def propagate_uncertainty(
        step_uncertainties: List[UncertaintyEstimate],
        dependencies: Optional[List[List[int]]] = None,
    ) -> UncertaintyEstimate:
        """
        Propagate uncertainty through a chain of reasoning steps.

        Args:
            step_uncertainties: Uncertainty estimates for each step
            dependencies: Optional dependency structure

        Returns:
            Combined uncertainty estimate for the chain
        """
        if not step_uncertainties:
            return UncertaintyEstimate(
                point_estimate=0.0,
                confidence_interval=(0.0, 0.0),
                credible_interval=(0.0, 0.0),
                confidence_level=0.95,
                epistemic_uncertainty=0.0,
                aleatoric_uncertainty=0.0,
                total_uncertainty=0.0,
                risk_score=1.0,
                worst_case=0.0,
                best_case=0.0,
                variance=0.0,
                skewness=0.0,
                is_symmetric=True,
            )

        # Combine point estimates (geometric mean for probabilities)
        point_estimates = [u.point_estimate for u in step_uncertainties]
        combined_point = math.prod(point_estimates) ** (1 / len(point_estimates))

        # Combine variances (assuming independence)
        combined_variance = sum(u.variance for u in step_uncertainties)
        combined_std = math.sqrt(combined_variance)

        # Combined epistemic and aleatoric
        combined_epistemic = math.sqrt(
            sum(u.epistemic_uncertainty**2 for u in step_uncertainties)
        )
        combined_aleatoric = math.sqrt(
            sum(u.aleatoric_uncertainty**2 for u in step_uncertainties)
        )

        # Confidence interval
        ci_lower = max(0.0, combined_point - 1.96 * combined_std)
        ci_upper = min(1.0, combined_point + 1.96 * combined_std)

        # Risk score: maximum risk in chain
        combined_risk = max(u.risk_score for u in step_uncertainties)

        # Worst/best case
        worst_case = min(u.worst_case for u in step_uncertainties)
        best_case = min(u.best_case for u in step_uncertainties)  # Conservative

        return UncertaintyEstimate(
            point_estimate=combined_point,
            confidence_interval=(ci_lower, ci_upper),
            credible_interval=(ci_lower, ci_upper),
            confidence_level=0.95,
            epistemic_uncertainty=combined_epistemic,
            aleatoric_uncertainty=combined_aleatoric,
            total_uncertainty=combined_std,
            risk_score=combined_risk,
            worst_case=worst_case,
            best_case=best_case,
            variance=combined_variance,
            skewness=0.0,  # Simplified
            is_symmetric=True,
        )

    @staticmethod
    def assess_reasoning_risk(
        reasoning_steps: List[Dict], confidence_history: List[float]
    ) -> RiskAssessment:
        """
        Assess risks in a reasoning chain.

        Args:
            reasoning_steps: List of reasoning step dictionaries
            confidence_history: Historical confidence scores

        Returns:
            RiskAssessment with identified risks and mitigations
        """
        risk_factors = []
        risk_score = 0.0

        # Risk factor 1: Low confidence
        if confidence_history:
            avg_confidence = sum(confidence_history) / len(confidence_history)
            if avg_confidence < 0.7:
                risk_factors.append(
                    {
                        "factor": "low_confidence",
                        "severity": 0.3,
                        "description": f"Average confidence is low ({avg_confidence:.2f})",
                    }
                )
                risk_score += 0.3

        # Risk factor 2: High variance in confidence
        if len(confidence_history) > 1:
            variance = sum(
                (c - sum(confidence_history) / len(confidence_history)) ** 2
                for c in confidence_history
            ) / len(confidence_history)
            if variance > 0.05:
                risk_factors.append(
                    {
                        "factor": "confidence_variance",
                        "severity": 0.2,
                        "description": f"High variance in confidence ({variance:.3f})",
                    }
                )
                risk_score += 0.2

        # Risk factor 3: Missing validation
        has_validation = any(
            isinstance(step, dict) and step.get("validation")
            for step in reasoning_steps
        )
        if not has_validation:
            risk_factors.append(
                {
                    "factor": "no_validation",
                    "severity": 0.2,
                    "description": "No validation steps present",
                }
            )
            risk_score += 0.2

        # Risk factor 4: No measurements
        has_measurements = any(
            isinstance(step, dict) and step.get("measurements")
            for step in reasoning_steps
        )
        if not has_measurements:
            risk_factors.append(
                {
                    "factor": "no_measurements",
                    "severity": 0.15,
                    "description": "No objective measurements present",
                }
            )
            risk_score += 0.15

        # Risk factor 5: Short reasoning chain
        if len(reasoning_steps) < 3:
            risk_factors.append(
                {
                    "factor": "short_chain",
                    "severity": 0.1,
                    "description": "Reasoning chain is very short",
                }
            )
            risk_score += 0.1

        # Risk factor 6: No alternatives considered
        has_alternatives = any(
            isinstance(step, dict) and step.get("alternatives_considered")
            for step in reasoning_steps
        )
        if not has_alternatives:
            risk_factors.append(
                {
                    "factor": "no_alternatives",
                    "severity": 0.15,
                    "description": "No alternative approaches considered",
                }
            )
            risk_score += 0.15

        # Generate mitigations
        mitigations = []
        for factor in risk_factors:
            if factor["factor"] == "low_confidence":
                mitigations.append("Add more evidence and validation steps")
            elif factor["factor"] == "confidence_variance":
                mitigations.append(
                    "Investigate sources of uncertainty and stabilize reasoning"
                )
            elif factor["factor"] == "no_validation":
                mitigations.append("Add explicit validation and verification steps")
            elif factor["factor"] == "no_measurements":
                mitigations.append("Include objective measurements and metrics")
            elif factor["factor"] == "short_chain":
                mitigations.append("Expand reasoning with more detailed analysis")
            elif factor["factor"] == "no_alternatives":
                mitigations.append("Consider multiple approaches before deciding")

        # Confidence in assessment depends on data available
        assessment_confidence = min(1.0, len(confidence_history) / 10.0)

        return RiskAssessment(
            overall_risk=min(1.0, risk_score),
            risk_factors=risk_factors,
            risk_mitigation=mitigations,
            confidence_in_assessment=assessment_confidence,
        )

    @staticmethod
    def monte_carlo_prediction(
        base_confidence: float, uncertainty: float, num_samples: int = 10000
    ) -> Dict[str, Any]:
        """
        Monte Carlo simulation for outcome prediction.

        Args:
            base_confidence: Expected confidence
            uncertainty: Uncertainty (standard deviation)
            num_samples: Number of Monte Carlo samples

        Returns:
            Dictionary with percentiles and distribution
        """
        import random

        samples = []
        for _ in range(num_samples):
            # Sample from normal distribution, clamp to [0, 1]
            sample = random.gauss(base_confidence, uncertainty)
            sample = max(0.0, min(1.0, sample))
            samples.append(sample)

        # Calculate percentiles
        sorted_samples = sorted(samples)
        percentiles = {
            "p05": sorted_samples[int(0.05 * num_samples)],
            "p25": sorted_samples[int(0.25 * num_samples)],
            "p50": sorted_samples[int(0.50 * num_samples)],
            "p75": sorted_samples[int(0.75 * num_samples)],
            "p95": sorted_samples[int(0.95 * num_samples)],
        }

        # Probability of success (>0.5)
        success_prob = sum(1 for s in samples if s > 0.5) / num_samples

        return {
            "percentiles": percentiles,
            "mean": sum(samples) / len(samples),
            "std": math.sqrt(
                sum((s - sum(samples) / len(samples)) ** 2 for s in samples)
                / len(samples)
            ),
            "success_probability": success_prob,
            "samples": len(samples),
        }


# Example usage
if __name__ == "__main__":
    print("[OK] Uncertainty Quantification Ready")
    print("\nCapabilities:")
    print("  - Bayesian confidence intervals")
    print("  - Epistemic vs. aleatoric uncertainty decomposition")
    print("  - Uncertainty propagation through reasoning chains")
    print("  - Risk assessment with identified factors")
    print("  - Monte Carlo outcome prediction")
    print("  - Worst/best case scenario analysis")
