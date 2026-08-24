"""Map canonical / ICD / short labels onto epidemiology CSV names."""
from __future__ import annotations

ALIASES = {
    "type 2 diabetes mellitus": {"type 2 diabetes mellitus", "type 2 diabetes", "t2dm", "diabetes", "e11"},
    "essential (primary) hypertension": {"essential (primary) hypertension", "hypertension", "i10"},
    "chronic kidney disease": {"chronic kidney disease", "ckd", "n18"},
    "ischemic heart disease": {"ischemic heart disease", "ihd", "i25"},
    "chronic obstructive pulmonary disease": {"chronic obstructive pulmonary disease", "copd", "j44"},
    "major depressive disorder": {"major depressive disorder", "depression", "f32"},
    "generalized anxiety disorder": {"generalized anxiety disorder", "anxiety", "f41"},
    "covid-19": {"covid-19", "covid", "u07.1"},
    "obesity": {"obesity", "e66"},
    "hyperlipidemia": {"hyperlipidemia", "e78", "e78.5"},
    "asthma": {"asthma", "j45"},
    "stroke": {"stroke", "i63"},
    "heart failure": {"heart failure", "i50"},
    "chronic liver disease": {"chronic liver disease", "k76"},
    "tuberculosis": {"tuberculosis", "a15"},
    "pneumonia": {"pneumonia", "j18"},
    "rheumatoid arthritis": {"rheumatoid arthritis", "m06"},
    "osteoporosis": {"osteoporosis", "m81"},
}


def norm(s: str) -> str:
    return " ".join((s or "").strip().lower().replace("_", " ").split())


def alias_set(name: str) -> set[str]:
    n = norm(name)
    for canon, als in ALIASES.items():
        if n == canon or n in als:
            return set(als) | {canon}
    return {n}


def names_match(a: str, b: str) -> bool:
    return bool(alias_set(a) & alias_set(b))


# Which source institutions live on which federation agent
NODE_INSTITUTIONS = {
    "hospital_a": ["INST001", "INST004", "INST005", "INST006", "INST010", "INST011"],
    "hospital_b": ["INST003", "INST008", "INST009"],
    "diagnostic_lab": ["INST002", "INST007", "INST012"],
}
