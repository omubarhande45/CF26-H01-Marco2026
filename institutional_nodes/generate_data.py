"""Generate synthetic clinical data with heterogeneous schemas."""
from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

RNG = random.Random(42)
DATA = Path(__file__).resolve().parent / "data"
DATA.mkdir(parents=True, exist_ok=True)

FIRST = ["Asha", "Rahul", "Priya", "Omar", "Mei", "Elena", "James", "Fatima", "Kenji", "Sofia"]
LAST = ["Patel", "Khan", "Garcia", "Chen", "Singh", "Okoye", "Rossi", "Kim", "Almeida", "Berg"]
DX_A = ["E11", "E11.9", "I10", "J45", "E78.5"]
DX_B = ["Type 2 Diabetes", "T2DM", "Hypertension", "Asthma", "Hyperlipidemia"]
DX_L = ["Type 2 Diabetes", "type-2-diabetes", "Hypertension", "Asthma", "Hyperlipidemia"]
MEDS = ["Metformin", "Glucophage", "Lisinopril", "Atorvastatin", "Albuterol", "Insulin"]


def _name() -> str:
    return f"{RNG.choice(FIRST)} {RNG.choice(LAST)}"


def _dob(age: int) -> str:
    return (date.today() - timedelta(days=age * 365 + RNG.randint(0, 300))).isoformat()


def _lab_date() -> str:
    return (date.today() - timedelta(days=RNG.randint(10, 400))).isoformat()


def hospital_a(n: int = 4000) -> Path:
    path = DATA / "hospital_a.db"
    if path.exists():
        path.unlink()
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE patients (pat_id INTEGER PRIMARY KEY, name TEXT, age INT, sex TEXT, dob TEXT);
        CREATE TABLE diagnoses (id INTEGER PRIMARY KEY, pat_id INT, diagnosis_code TEXT, onset TEXT);
        CREATE TABLE meds (id INTEGER PRIMARY KEY, pat_id INT, drug TEXT, started TEXT);
        CREATE TABLE labs (id INTEGER PRIMARY KEY, pat_id INT, lab_name TEXT, result_val REAL, taken_on TEXT);
        CREATE TABLE encounters (id INTEGER PRIMARY KEY, pat_id INT, visit_type TEXT, visit_on TEXT);
        """
    )
    for i in range(1, n + 1):
        age = RNG.randint(18, 90)
        sex = RNG.choice(["M", "F", "F", "M", "O"])
        c.execute(
            "INSERT INTO patients VALUES (?,?,?,?,?)",
            (i, _name(), age, sex, _dob(age)),
        )
        if RNG.random() < 0.42:
            code = RNG.choice(DX_A)
            c.execute(
                "INSERT INTO diagnoses (pat_id,diagnosis_code,onset) VALUES (?,?,?)",
                (i, code, _lab_date()),
            )
            if code.startswith("E11") and RNG.random() < 0.7:
                c.execute(
                    "INSERT INTO meds (pat_id,drug,started) VALUES (?,?,?)",
                    (i, RNG.choice(["Metformin", "Glucophage", "Insulin"]), _lab_date()),
                )
                c.execute(
                    "INSERT INTO labs (pat_id,lab_name,result_val,taken_on) VALUES (?,?,?,?)",
                    (i, RNG.choice(["HbA1c", "A1C"]), round(RNG.uniform(5.2, 12.5), 1), _lab_date()),
                )
        if RNG.random() < 0.3:
            c.execute(
                "INSERT INTO meds (pat_id,drug,started) VALUES (?,?,?)",
                (i, RNG.choice(MEDS), _lab_date()),
            )
        if RNG.random() < 0.25:
            c.execute(
                "INSERT INTO labs (pat_id,lab_name,result_val,taken_on) VALUES (?,?,?,?)",
                (i, "HbA1c", round(RNG.uniform(4.8, 11.0), 1), _lab_date()),
            )
        c.execute(
            "INSERT INTO encounters (pat_id,visit_type,visit_on) VALUES (?,?,?)",
            (i, RNG.choice(["OPD", "IPD", "ER"]), _lab_date()),
        )
    c.commit()
    c.close()
    return path


def hospital_b(n: int = 3500) -> Path:
    path = DATA / "hospital_b.db"
    if path.exists():
        path.unlink()
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE person (patient_key INTEGER PRIMARY KEY, full_name TEXT, years_old INT, gender TEXT);
        CREATE TABLE conditions (id INTEGER PRIMARY KEY, patient_key INT, condition TEXT, recorded TEXT);
        CREATE TABLE medications (id INTEGER PRIMARY KEY, patient_key INT, medication_name TEXT, start_date TEXT);
        CREATE TABLE observations (id INTEGER PRIMARY KEY, patient_key INT, test TEXT, value_num REAL, observed_at TEXT);
        """
    )
    for i in range(1, n + 1):
        age = RNG.randint(20, 88)
        gender = RNG.choice(["male", "female", "female", "male", "other"])
        c.execute(
            "INSERT INTO person VALUES (?,?,?,?)",
            (i, _name(), age, gender),
        )
        if RNG.random() < 0.38:
            cond = RNG.choice(DX_B)
            c.execute(
                "INSERT INTO conditions (patient_key,condition,recorded) VALUES (?,?,?)",
                (i, cond, _lab_date()),
            )
            if cond in ("Type 2 Diabetes", "T2DM") and RNG.random() < 0.72:
                c.execute(
                    "INSERT INTO medications (patient_key,medication_name,start_date) VALUES (?,?,?)",
                    (i, RNG.choice(["Metformin", "metformin", "Insulin"]), _lab_date()),
                )
                c.execute(
                    "INSERT INTO observations (patient_key,test,value_num,observed_at) VALUES (?,?,?,?)",
                    (i, RNG.choice(["HbA1c", "Hemoglobin A1c"]), round(RNG.uniform(5.0, 13.0), 1), _lab_date()),
                )
        if RNG.random() < 0.22:
            c.execute(
                "INSERT INTO observations (patient_key,test,value_num,observed_at) VALUES (?,?,?,?)",
                (i, "HbA1c", round(RNG.uniform(4.9, 10.5), 1), _lab_date()),
            )
    c.commit()
    c.close()
    return path


def diagnostic_lab(n: int = 2800) -> Path:
    path = DATA / "diagnostic_lab.db"
    if path.exists():
        path.unlink()
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE fhir_patient (resource_id INTEGER PRIMARY KEY, name TEXT, age_years INT, gender TEXT);
        CREATE TABLE fhir_condition (id INTEGER PRIMARY KEY, subject_id INT, code_display TEXT, onset TEXT);
        CREATE TABLE fhir_medication (id INTEGER PRIMARY KEY, subject_id INT, medication TEXT, authored TEXT);
        CREATE TABLE fhir_observation (id INTEGER PRIMARY KEY, subject_id INT, code TEXT, value REAL, effective_date TEXT);
        """
    )
    for i in range(1, n + 1):
        age = RNG.randint(16, 92)
        gender = RNG.choice(["male", "female", "male", "female", "other"])
        c.execute("INSERT INTO fhir_patient VALUES (?,?,?,?)", (i, _name(), age, gender))
        if RNG.random() < 0.35:
            cond = RNG.choice(DX_L)
            c.execute(
                "INSERT INTO fhir_condition (subject_id,code_display,onset) VALUES (?,?,?)",
                (i, cond, _lab_date()),
            )
        if RNG.random() < 0.4:
            c.execute(
                "INSERT INTO fhir_medication (subject_id,medication,authored) VALUES (?,?,?)",
                (i, RNG.choice(["Metformin", "Lisinopril", "Atorvastatin", "Insulin"]), _lab_date()),
            )
        # Lab-heavy node
        if RNG.random() < 0.75:
            c.execute(
                "INSERT INTO fhir_observation (subject_id,code,value,effective_date) VALUES (?,?,?,?)",
                (i, RNG.choice(["HbA1c", "4548-4"]), round(RNG.uniform(4.6, 12.8), 1), _lab_date()),
            )
    c.commit()
    c.close()
    return path


def centralized(n_a=4000, n_b=3500, n_l=2800) -> Path:
    """Flattened copy for baseline benchmarks (not used at query time by FCQF)."""
    path = DATA / "centralized.db"
    if path.exists():
        path.unlink()
    # Simple union of counts only — real baseline reads the three DBs independently
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE meta (k TEXT, v TEXT)")
    c.execute("INSERT INTO meta VALUES ('note','baseline uses same synthetic generators')")
    c.commit()
    c.close()
    return path


def research_institute(n: int = 2200) -> Path:
    """OMOP-inspired codes: sid, dx_label, rx_label, assay_name."""
    path = DATA / "research_institute.db"
    if path.exists():
        path.unlink()
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE subject (sid INTEGER PRIMARY KEY, label TEXT, age_y INT, sex_code TEXT);
        CREATE TABLE dx_list (id INTEGER PRIMARY KEY, sid INT, dx_label TEXT, onset TEXT);
        CREATE TABLE rx_list (id INTEGER PRIMARY KEY, sid INT, rx_label TEXT, start_d TEXT);
        CREATE TABLE assay (id INTEGER PRIMARY KEY, sid INT, assay_name TEXT, numeric_result REAL, drawn TEXT);
        """
    )
    for i in range(1, n + 1):
        age = RNG.randint(22, 85)
        c.execute(
            "INSERT INTO subject VALUES (?,?,?,?)",
            (i, _name(), age, RNG.choice(["1", "2", "2", "1", "9"])),
        )
        if RNG.random() < 0.4:
            dx = RNG.choice(["DM2", "Type 2 Diabetes", "HTN", "ASTH", "HLP"])
            c.execute("INSERT INTO dx_list (sid,dx_label,onset) VALUES (?,?,?)", (i, dx, _lab_date()))
            if dx in ("DM2", "Type 2 Diabetes") and RNG.random() < 0.68:
                c.execute("INSERT INTO rx_list (sid,rx_label,start_d) VALUES (?,?,?)", (i, "METF", _lab_date()))
                c.execute(
                    "INSERT INTO assay (sid,assay_name,numeric_result,drawn) VALUES (?,?,?,?)",
                    (i, "A1C_PCT", round(RNG.uniform(5.1, 12.2), 1), _lab_date()),
                )
        if RNG.random() < 0.2:
            c.execute(
                "INSERT INTO assay (sid,assay_name,numeric_result,drawn) VALUES (?,?,?,?)",
                (i, "A1C_PCT", round(RNG.uniform(4.7, 10.8), 1), _lab_date()),
            )
    c.commit()
    c.close()
    return path


def generate_all(patients: int = 10000, seed: int = 42) -> dict:
    global RNG
    RNG = random.Random(seed)
    # split patients across four institutions
    n_a = int(patients * 0.35)
    n_b = int(patients * 0.30)
    n_l = int(patients * 0.20)
    n_r = patients - n_a - n_b - n_l
    return {
        "hospital_a": str(hospital_a(n_a)),
        "hospital_b": str(hospital_b(n_b)),
        "diagnostic_lab": str(diagnostic_lab(n_l)),
        "research_institute": str(research_institute(max(n_r, 500))),
        "seed": seed,
        "patients": patients,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--patients", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    print(generate_all(args.patients, args.seed))
