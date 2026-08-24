"""Canonical clinical model and query/result contracts."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResultStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    SUPPRESSED = "SUPPRESSED"
    INVALIDATED = "INVALIDATED"
    FAILED = "FAILED"
    DENIED = "DENIED"


class Role(str, Enum):
    RESEARCHER = "researcher"
    CLINICIAN = "clinician"
    DATA_STEWARD = "data_steward"
    AUDITOR = "auditor"
    ADMIN = "admin"


class ClinicalQuery(BaseModel):
    age_min: int = 0
    age_max: int = 120
    genders: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    lab_test: str | None = "HbA1c"
    lab_op: str = ">"
    lab_value: float | None = None
    window_months: int = 12
    year: int | None = None
    aggregation: str = "count_distinct_patients"
    requested_fields: list[str] = Field(default_factory=list)
    return_rows: bool = False
    differential_privacy: bool = False
    epsilon: float | None = None
    delta: float | None = 1e-5

    @field_validator("age_min", "age_max")
    @classmethod
    def _age(cls, v: int) -> int:
        if v < 0 or v > 120:
            raise ValueError("age out of range")
        return v


class NodeContribution(BaseModel):
    node_id: str
    node_name: str
    status: str
    count: int | None = None
    exact_eligible: bool | None = None
    k_suppressed: bool = False
    dp_applied: bool = False
    latency_ms: float | None = None
    schema_version: str | None = None
    error: str | None = None
    attempts: int = 1


class QueryResult(BaseModel):
    query_id: str
    status: ResultStatus
    aggregate: int | None
    aggregate_kind: str = "k_suppressed"
    completeness_guaranteed: bool
    completeness: float | None = None
    nodes_total: int | None = None
    nodes_successful: int | None = None
    nodes_failed: int | None = None
    contributions: list[NodeContribution]
    privacy: dict[str, Any]
    policy: dict[str, Any] | None = None
    provenance_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    executed_ms: float | None = None
    created_at: datetime


class NodeHealth(BaseModel):
    node_id: str
    name: str
    healthy: bool
    status: str = "AVAILABLE"
    schema_version: str
    patient_count: int | None = None
    latency_ms: float | None = None


class SecureQueryEnvelope(BaseModel):
    query_id: str
    schema_version: str = "1.0"
    canonical_conditions: dict[str, Any]
    privacy_policy: dict[str, Any]
    requested_fields: list[str] = Field(default_factory=list)
