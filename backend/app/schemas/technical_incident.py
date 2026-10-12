"""
PEVN Backend — Technical Incident & Support Case Schemas

Pydantic schemas for request validation and response serialization
governing technical support cases and operational incidents.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.technical_incident import (
    TechnicalIncidentCategory,
    TechnicalIncidentSeverity,
    TechnicalIncidentStatus,
)


class TechnicalIncidentCreateRequest(BaseModel):
    """Payload to record a new technical support case or incident."""

    title: str = Field(..., min_length=5, max_length=200, description="Resumen del incidente técnico")
    category: TechnicalIncidentCategory = Field(default=TechnicalIncidentCategory.SYSTEM, description="Categoría técnica")
    severity: TechnicalIncidentSeverity = Field(default=TechnicalIncidentSeverity.MEDIUM, description="Severidad operativa")
    affected_service: str = Field(default="platform", max_length=50, description="Servicio o subsistema afectado")
    institution_id: uuid.UUID | None = Field(default=None, description="Inquilino institucional relacionado (opcional)")
    description: str = Field(..., min_length=10, description="Descripción técnica detallada")
    technical_context: dict[str, Any] | None = Field(default=None, description="Contexto técnico sanitizado")
    assigned_operator: str | None = Field(default=None, max_length=100, description="Operador técnico asignado")


class TechnicalIncidentUpdateRequest(BaseModel):
    """Payload to update lifecycle, operator, or resolution of an incident."""

    status: TechnicalIncidentStatus | None = Field(default=None, description="Nuevo estado del ciclo de vida")
    severity: TechnicalIncidentSeverity | None = Field(default=None, description="Nueva severidad operativa")
    assigned_operator: str | None = Field(default=None, max_length=100, description="Operador técnico asignado")
    resolution_notes: str | None = Field(default=None, description="Notas de mitigación o resolución técnica")


class TechnicalIncidentResponse(BaseModel):
    """Detailed response representation of a technical incident."""

    id: uuid.UUID
    ticket_number: str
    title: str
    category: str
    severity: str
    status: str
    affected_service: str
    institution_id: uuid.UUID | None = None
    institution_name: str | None = None
    reporter_id: uuid.UUID | None = None
    assigned_operator: str | None = None
    description: str
    technical_context: dict[str, Any] | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class TechnicalIncidentListResponse(BaseModel):
    """Paginated list and summary counts of technical incidents."""

    items: list[TechnicalIncidentResponse]
    total: int
    open_count: int
    critical_count: int
