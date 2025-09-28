"""Pydantic models and enumerations shared across the application."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyName(str, Enum):
    """Enumeration of supported companies."""

    META = "meta"
    AMAZON = "amazon"
    APPLE = "apple"
    NETFLIX = "netflix"
    GOOGLE = "google"


class JobCategory(str, Enum):
    """Supported job categories for classification."""

    TECHNOLOGY = "technology"
    DATA = "data"
    PRODUCT = "product"
    DESIGN = "design"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HR = "hr"
    LEGAL = "legal"
    CUSTOMER_SUCCESS = "customer_success"
    CONSULTING = "consulting"
    OTHER = "other"


class JobType(str, Enum):
    """Employment types."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    FREELANCE = "freelance"


class ExperienceLevel(str, Enum):
    """Supported experience levels."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class WorkplaceType(str, Enum):
    """Workplace environment types."""

    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class JobCategorizationResult(BaseModel):
    """Result of running the job categorizer."""

    category: JobCategory = JobCategory.OTHER
    confidence: float = 0.0
    keyword_matches: Dict[str, int] = Field(default_factory=dict)
    department_match: bool = False
    reasoning: Optional[str] = None

    model_config = ConfigDict(use_enum_values=False)


class Job(BaseModel):
    """Core job model used by the scraping pipeline."""

    id: str
    title: str
    company: CompanyName
    location: str
    description: str
    department: Optional[str] = None
    category: JobCategory = JobCategory.OTHER
    job_type: JobType = JobType.FULL_TIME
    experience_level: ExperienceLevel = ExperienceLevel.MID
    workplace_type: WorkplaceType = WorkplaceType.UNKNOWN
    posted_date: Optional[datetime] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)


__all__ = [
    "CompanyName",
    "JobCategory",
    "JobType",
    "ExperienceLevel",
    "WorkplaceType",
    "JobCategorizationResult",
    "Job",
]
