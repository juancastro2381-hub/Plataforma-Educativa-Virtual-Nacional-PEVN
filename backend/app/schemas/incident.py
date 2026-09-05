"""
PEVN Backend — School Coexistence & Student Incident Schemas (Phase 15)

Pydantic schemas for student coexistence situations, follow-up encounters, and agreements.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentStatus,
)
from app.schemas.academic import StudentResponse
from app.schemas.user import UserResponse


class IncidentFollowUpPayload(BaseModel):
    """Payload for creating a chronological follow-up note."""

    model_config = ConfigDict(extra="forbid")

    follow_up_date: datetime | None = Field(default=None, description="Encounter date")
    notes: str = Field(..., min_length=3, description="Follow-up notes and observations")


class IncidentFollowUpResponse(BaseModel):
    """Response representation of a follow-up log."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    author_user_id: uuid.UUID
    follow_up_date: datetime
    notes: str
    author: UserResponse | None = None
    created_at: datetime


class StudentIncidentCreateRequest(BaseModel):
    """Payload for recording a coexistence situation."""

    model_config = ConfigDict(extra="forbid")

    student_id: uuid.UUID = Field(..., description="Target enrolled student ID")
    situation_type: CoexistenceSituationType = Field(
        default=CoexistenceSituationType.TIPO_I,
        description="Ley 1620 situation type",
    )
    incident_date: datetime | None = Field(default=None, description="Occurrence timestamp")
    location: str | None = Field(default=None, max_length=150, description="Location")
    description: str = Field(..., min_length=5, description="Factual narrative")
    student_version: str | None = Field(default=None, description="Student statement / descargos")
    pedagogical_measures: str = Field(..., min_length=3, description="Pedagogical / restorative measures")
    commitments: str | None = Field(default=None, description="Agreements and commitments")
    status: IncidentStatus = Field(default=IncidentStatus.ABIERTO, description="Status")
    is_visible_to_guardian: bool = Field(default=True, description="Family visibility flag")
    is_visible_to_student: bool = Field(default=True, description="Student visibility flag (DECISION-15-01)")


class StudentIncidentUpdateRequest(BaseModel):
    """Payload for modifying an incident."""

    model_config = ConfigDict(extra="forbid")

    situation_type: CoexistenceSituationType | None = None
    incident_date: datetime | None = None
    location: str | None = None
    description: str | None = None
    student_version: str | None = None
    pedagogical_measures: str | None = None
    commitments: str | None = None
    status: IncidentStatus | None = None
    is_visible_to_guardian: bool | None = None
    is_visible_to_student: bool | None = None


class StudentIncidentCloseRequest(BaseModel):
    """Payload for formal resolution and closure of an incident."""

    model_config = ConfigDict(extra="forbid")

    resolution_notes: str | None = Field(default=None, description="Final resolution summary")


class StudentIncidentResponse(BaseModel):
    """Response representation of a student incident."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    student_id: uuid.UUID
    reporter_user_id: uuid.UUID
    situation_type: CoexistenceSituationType
    incident_date: datetime
    location: str | None = None
    description: str
    student_version: str | None = None
    pedagogical_measures: str
    commitments: str | None = None
    status: IncidentStatus
    is_visible_to_guardian: bool = True
    is_visible_to_student: bool = True
    closed_at: datetime | None = None
    closed_by_user_id: uuid.UUID | None = None
    reporter: UserResponse | None = None
    closed_by: UserResponse | None = None
    student: StudentResponse | None = None
    follow_ups: list[IncidentFollowUpResponse] = []
    created_at: datetime
    updated_at: datetime


class StudentIncidentListResponse(BaseModel):
    """List response for student incidents."""

    items: list[StudentIncidentResponse]
    total: int
