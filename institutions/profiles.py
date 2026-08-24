"""Institution policy profiles loaded by coordinator and agents."""
PROFILES = {
    "hospital_a": {
        "institution": "hospital_a",
        "name": "Hospital A",
        "privacy": {"minimum_cohort": 10, "differential_privacy": False, "epsilon": 1.0},
        "allowed_roles": ["researcher", "clinician", "admin"],
        "allowed_query_types": ["aggregate_count", "aggregate_statistics"],
        "canonical_model_version": "1.0",
        "schema_version": "1.2",
    },
    "hospital_b": {
        "institution": "hospital_b",
        "name": "Hospital B",
        "privacy": {"minimum_cohort": 12, "differential_privacy": False, "epsilon": 0.8},
        "allowed_roles": ["researcher", "admin"],
        "allowed_query_types": ["aggregate_count"],
        "canonical_model_version": "1.0",
        "schema_version": "1.1",
    },
    "diagnostic_lab": {
        "institution": "diagnostic_lab",
        "name": "Diagnostic Laboratory",
        "privacy": {"minimum_cohort": 10, "differential_privacy": True, "epsilon": 1.0},
        "allowed_roles": ["researcher", "clinician", "admin"],
        "allowed_query_types": ["aggregate_count"],
        "canonical_model_version": "1.0",
        "schema_version": "1.0",
    },
    "research_institute": {
        "institution": "research_institute",
        "name": "Research Institute",
        "privacy": {"minimum_cohort": 15, "differential_privacy": True, "epsilon": 0.5},
        "allowed_roles": ["researcher", "admin"],
        "allowed_query_types": ["aggregate_count"],
        "canonical_model_version": "1.0",
        "schema_version": "1.0",
    },
}


def strictest_k(ids: list[str]) -> int:
    ks = [PROFILES[i]["privacy"]["minimum_cohort"] for i in ids if i in PROFILES]
    return max(ks) if ks else 10
