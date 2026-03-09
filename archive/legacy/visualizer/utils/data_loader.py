"""
Data loading utilities for the UATP Capsule Visualizer.
"""

import datetime
import json
from typing import List

import streamlit as st
from capsule_schema import Capsule


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def convert_to_serializable(obj):
    """Convert objects to JSON-serializable format, handling datetime objects."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj


@st.cache_data
def load_capsules(path: str) -> List[Capsule]:
    """Load capsules from a JSONL file, caching the result."""
    capsules = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    capsule_data = json.loads(line)
                    capsules.append(Capsule(**capsule_data))
    except FileNotFoundError:
        st.error(f"File not found: {path}")
    except json.JSONDecodeError as e:
        st.error(f"Error parsing file: {e}")
    return capsules
