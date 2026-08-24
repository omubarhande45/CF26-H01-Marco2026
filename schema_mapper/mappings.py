"""Heterogeneous schema → canonical clinical concepts."""

# Hospital A: diagnosis_code, drug, lab_name
# Hospital B: condition, medication_name, test
# Lab: fhir-inspired resource types

CONDITION_MAP = {
    "E11": "Type 2 Diabetes",
    "E11.9": "Type 2 Diabetes",
    "Type 2 Diabetes": "Type 2 Diabetes",
    "T2DM": "Type 2 Diabetes",
    "type-2-diabetes": "Type 2 Diabetes",
    "I10": "Hypertension",
    "Hypertension": "Hypertension",
    "J45": "Asthma",
    "Asthma": "Asthma",
    "E78.5": "Hyperlipidemia",
    "Hyperlipidemia": "Hyperlipidemia",
}

MEDICATION_MAP = {
    "Metformin": "Metformin",
    "metformin": "Metformin",
    "METFORMIN": "Metformin",
    "Glucophage": "Metformin",
    "Lisinopril": "Lisinopril",
    "Atorvastatin": "Atorvastatin",
    "Albuterol": "Albuterol",
    "Insulin": "Insulin",
}

LAB_MAP = {
    "HbA1c": "HbA1c",
    "hba1c": "HbA1c",
    "A1C": "HbA1c",
    "4548-4": "HbA1c",  # LOINC
    "Hemoglobin A1c": "HbA1c",
    "LDL": "LDL",
    "BP_SYS": "Systolic BP",
}


def canon_condition(raw: str) -> str:
    return CONDITION_MAP.get(raw, raw)


def canon_med(raw: str) -> str:
    return MEDICATION_MAP.get(raw, raw)


def canon_lab(raw: str) -> str:
    return LAB_MAP.get(raw, raw)


# Per-node SQL templates against local tables
NODE_SQL = {
    "hospital_a": {
        "count_cohort": """
            SELECT COUNT(DISTINCT p.pat_id) AS n
            FROM patients p
            WHERE p.age BETWEEN :age_min AND :age_max
              AND (:gender_filter = 0 OR p.sex IN ({genders}))
              AND (
                :need_dx = 0 OR EXISTS (
                  SELECT 1 FROM diagnoses d
                  WHERE d.pat_id = p.pat_id
                    AND d.diagnosis_code IN ({dx_codes})
                )
              )
              AND (
                :need_med = 0 OR EXISTS (
                  SELECT 1 FROM meds m
                  WHERE m.pat_id = p.pat_id
                    AND m.drug IN ({drugs})
                )
              )
              AND (
                :need_lab = 0 OR EXISTS (
                  SELECT 1 FROM labs l
                  WHERE l.pat_id = p.pat_id
                    AND l.lab_name IN ({labs})
                    AND l.result_val {lab_op} :lab_value
                    AND l.taken_on >= date('now', :window)
                )
              )
        """,
    },
    "hospital_b": {
        "count_cohort": """
            SELECT COUNT(DISTINCT p.patient_key) AS n
            FROM person p
            WHERE p.years_old BETWEEN :age_min AND :age_max
              AND (:gender_filter = 0 OR p.gender IN ({genders}))
              AND (
                :need_dx = 0 OR EXISTS (
                  SELECT 1 FROM conditions c
                  WHERE c.patient_key = p.patient_key
                    AND c.condition IN ({dx_codes})
                )
              )
              AND (
                :need_med = 0 OR EXISTS (
                  SELECT 1 FROM medications m
                  WHERE m.patient_key = p.patient_key
                    AND m.medication_name IN ({drugs})
                )
              )
              AND (
                :need_lab = 0 OR EXISTS (
                  SELECT 1 FROM observations o
                  WHERE o.patient_key = p.patient_key
                    AND o.test IN ({labs})
                    AND o.value_num {lab_op} :lab_value
                    AND o.observed_at >= date('now', :window)
                )
              )
        """,
    },
    "research_institute": {
        "count_cohort": """
            SELECT COUNT(DISTINCT s.sid) AS n
            FROM subject s
            WHERE s.age_y BETWEEN :age_min AND :age_max
              AND (:gender_filter = 0 OR s.sex_code IN ({genders}))
              AND (
                :need_dx = 0 OR EXISTS (
                  SELECT 1 FROM dx_list d WHERE d.sid = s.sid AND d.dx_label IN ({dx_codes})
                )
              )
              AND (
                :need_med = 0 OR EXISTS (
                  SELECT 1 FROM rx_list r WHERE r.sid = s.sid AND r.rx_label IN ({drugs})
                )
              )
              AND (
                :need_lab = 0 OR EXISTS (
                  SELECT 1 FROM assay a WHERE a.sid = s.sid AND a.assay_name IN ({labs})
                    AND a.numeric_result {lab_op} :lab_value
                    AND a.drawn >= date('now', :window)
                )
              )
        """,
    },
    "diagnostic_lab": {
        "count_cohort": """
            SELECT COUNT(DISTINCT p.resource_id) AS n
            FROM fhir_patient p
            WHERE p.age_years BETWEEN :age_min AND :age_max
              AND (:gender_filter = 0 OR p.gender IN ({genders}))
              AND (
                :need_dx = 0 OR EXISTS (
                  SELECT 1 FROM fhir_condition c
                  WHERE c.subject_id = p.resource_id
                    AND c.code_display IN ({dx_codes})
                )
              )
              AND (
                :need_med = 0 OR EXISTS (
                  SELECT 1 FROM fhir_medication m
                  WHERE m.subject_id = p.resource_id
                    AND m.medication IN ({drugs})
                )
              )
              AND (
                :need_lab = 0 OR EXISTS (
                  SELECT 1 FROM fhir_observation o
                  WHERE o.subject_id = p.resource_id
                    AND o.code IN ({labs})
                    AND o.value {lab_op} :lab_value
                    AND o.effective_date >= date('now', :window)
                )
              )
        """,
    },
}

# Local values that map TO a given canonical term
LOCAL_DX = {
    "hospital_a": {
        "Type 2 Diabetes": ["E11", "E11.9"],
        "Hypertension": ["I10"],
        "Asthma": ["J45"],
        "Hyperlipidemia": ["E78.5"],
    },
    "hospital_b": {
        "Type 2 Diabetes": ["Type 2 Diabetes", "T2DM"],
        "Hypertension": ["Hypertension"],
        "Asthma": ["Asthma"],
        "Hyperlipidemia": ["Hyperlipidemia"],
    },
    "diagnostic_lab": {
        "Type 2 Diabetes": ["Type 2 Diabetes", "type-2-diabetes"],
        "Hypertension": ["Hypertension"],
        "Asthma": ["Asthma"],
        "Hyperlipidemia": ["Hyperlipidemia"],
    },
    "research_institute": {
        "Type 2 Diabetes": ["DM2", "Type 2 Diabetes"],
        "Hypertension": ["HTN"],
        "Asthma": ["ASTH"],
        "Hyperlipidemia": ["HLP"],
    },
}

LOCAL_MED = {
    "hospital_a": {
        "Metformin": ["Metformin", "Glucophage"],
        "Lisinopril": ["Lisinopril"],
        "Atorvastatin": ["Atorvastatin"],
        "Albuterol": ["Albuterol"],
        "Insulin": ["Insulin"],
    },
    "hospital_b": {
        "Metformin": ["Metformin", "metformin"],
        "Lisinopril": ["Lisinopril"],
        "Atorvastatin": ["Atorvastatin"],
        "Albuterol": ["Albuterol"],
        "Insulin": ["Insulin"],
    },
    "diagnostic_lab": {
        "Metformin": ["Metformin"],
        "Lisinopril": ["Lisinopril"],
        "Atorvastatin": ["Atorvastatin"],
        "Albuterol": ["Albuterol"],
        "Insulin": ["Insulin"],
    },
    "research_institute": {
        "Metformin": ["METF"],
        "Lisinopril": ["LISI"],
        "Atorvastatin": ["ATOR"],
        "Albuterol": ["ALBU"],
        "Insulin": ["INS"],
    },
}

LOCAL_LAB = {
    "hospital_a": {"HbA1c": ["HbA1c", "A1C"]},
    "hospital_b": {"HbA1c": ["HbA1c", "Hemoglobin A1c"]},
    "diagnostic_lab": {"HbA1c": ["HbA1c", "4548-4"]},
}

GENDER_LOCAL = {
    "hospital_a": {"male": "M", "female": "F", "other": "O"},
    "hospital_b": {"male": "male", "female": "female", "other": "other"},
    "diagnostic_lab": {"male": "male", "female": "female", "other": "other"},
}
