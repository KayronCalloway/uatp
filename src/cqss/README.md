# Capsule Quality Scoring System (CQSS)

## Overview

The Capsule Quality Scoring System (CQSS) is a component of the UATP Capsule Engine designed to provide an objective, quantitative measure of a capsule's integrity, reliability, and trustworthiness. By analyzing various attributes of a capsule, the CQSS generates a score that helps users and automated systems assess the quality of the information and reasoning contained within it.

This is crucial for applications where agent decisions must be auditable, transparent, and meet specific quality standards.

## Scoring Methodology

The `CQSSScorer` in `cqss/scorer.py` calculates a total quality score (out of 100) based on a weighted average of several key metrics. Each metric is scored independently and then combined to produce the final CQSS score.

### Core Metrics

1.  **Signature Verification (Weight: 40%)**
    - **Description**: Verifies the cryptographic signature of the capsule to ensure its authenticity and integrity.
    - **Calculation**: A binary score. If the capsule's signature is successfully verified against its public key (`metadata.verify_key_hex`), the score is 100. If verification fails, or if the signature or key is missing, the score is 0.
    - **Rationale**: This is the most critical metric. A valid signature proves that the capsule has not been tampered with and originates from the claimed agent.

2.  **Confidence Score (Weight: 30%)**
    - **Description**: Measures the agent's self-reported confidence in its action or conclusion.
    - **Calculation**: The raw confidence value (0.0 to 1.0) is scaled to a 0-100 score.
    - **Rationale**: An agent's confidence is a primary indicator of its own assessment of the task's success.

3.  **Reasoning Depth (Weight: 20%)**
    - **Description**: Evaluates the thoroughness of the agent's reasoning process.
    - **Calculation**: The score is based on the number of steps in the `reasoning_trace`.
        - 0 steps: 0 points
        - 1-2 steps: 50 points
        - 3-5 steps: 75 points
        - 6+ steps: 100 points
    - **Rationale**: A detailed reasoning trace enhances transparency and allows for better auditing.

4.  **Ethical Policy Adherence (Weight: 10%)**
    - **Description**: Checks whether the capsule explicitly references an ethical policy.
    - **Calculation**: A binary score (100 if `ethical_policy_id` is present, 0 otherwise).
    - **Rationale**: Demonstrates that the agent's actions were governed by a defined set of rules.

### Score Calculation

The total score is calculated as follows:

`Total Score = (Signature * 0.4) + (Confidence * 0.3) + (Reasoning Depth * 0.2) + (Ethical Policy * 0.1)`

## How to Use and Interpret Scores

The CQSS score is integrated directly into the Streamlit `visualizer.py`. Each capsule displayed in the visualizer shows its total CQSS score and a breakdown of the contributing metrics.

- **High Scores (80-100)**: Indicate a high-quality, trustworthy capsule with strong confidence, detailed reasoning, and adherence to ethical guidelines.
- **Medium Scores (50-79)**: Suggest a reasonably sound capsule that may be lacking in one area (e.g., a less detailed reasoning trace or lower confidence).
- **Low Scores (0-49)**: Signal a potential issue. These capsules should be reviewed with caution, as they may stem from low-confidence decisions, poor reasoning, or a lack of ethical oversight.

## Extensibility

The `CQSSScorer` is designed for easy extension. Future enhancements could include:

- **Signature Verification**: Factoring in whether the capsule's cryptographic signature is valid.
- **Hash Integrity**: Checking the integrity of the capsule's hash.
- **Contextual Analysis**: Using NLP to analyze the content of the `reasoning_trace` for quality and coherence, rather than just its length.
- **Reputation Scoring**: Incorporating the historical performance of the agent (`agent_id`) into the score.
