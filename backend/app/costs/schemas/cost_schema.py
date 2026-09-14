from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.costs.models.usage_cost import CostType


# ----------------------------------------------------
# Base Schema
# ----------------------------------------------------


class UsageCostBase(BaseModel):
    provider: str = Field(..., max_length=100)

    service: str = Field(..., max_length=100)

    model_name: Optional[str] = None

    cost_type: CostType

    usage_quantity: Decimal = Field(..., ge=0)

    unit: str

    unit_price: Decimal = Field(..., ge=0)

    currency: str = "USD"


# ----------------------------------------------------
# Create
# ----------------------------------------------------


class UsageCostCreate(UsageCostBase):
    organization_id: UUID

    project_id: UUID

    execution_id: Optional[UUID] = None


# ----------------------------------------------------
# Update
# ----------------------------------------------------


class UsageCostUpdate(BaseModel):
    provider: Optional[str] = None

    service: Optional[str] = None

    model_name: Optional[str] = None

    usage_quantity: Optional[Decimal] = Field(default=None, ge=0)

    unit_price: Optional[Decimal] = Field(default=None, ge=0)

    currency: Optional[str] = None

    unit: Optional[str] = None


# ----------------------------------------------------
# Response
# ----------------------------------------------------


class UsageCostResponse(UsageCostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    organization_id: UUID

    project_id: UUID

    execution_id: Optional[UUID]

    total_cost: Decimal

    created_at: datetime


# ----------------------------------------------------
# Cost Summary
# ----------------------------------------------------


class CostSummary(BaseModel):
    total_cost: Decimal

    total_requests: int

    total_usage: Decimal

    currency: str = "USD"


# ----------------------------------------------------
# Provider Summary
# ----------------------------------------------------


class ProviderCostSummary(BaseModel):
    provider: str

    service: str

    total_cost: Decimal

    total_usage: Decimal

    total_requests: int


# ----------------------------------------------------
# Daily Cost
# ----------------------------------------------------


class DailyCost(BaseModel):
    date: datetime

    total_cost: Decimal


# ----------------------------------------------------
# Monthly Cost
# ----------------------------------------------------


class MonthlyCost(BaseModel):
    month: str

    total_cost: Decimal


# ----------------------------------------------------
# Model Cost Breakdown
# ----------------------------------------------------


class ModelCostBreakdown(BaseModel):
    model_name: str

    provider: str

    total_cost: Decimal

    total_tokens_or_usage: Decimal

    request_count: int