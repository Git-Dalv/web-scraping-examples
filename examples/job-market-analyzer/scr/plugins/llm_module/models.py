from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

import re


class GeneralInfo(BaseModel):
    JobTitle: str
    Company: str
    Location: Optional[str] = None
    JobType: Optional[Literal["full-time", "part-time", "contract", "internship", "temporary"]] = None
    WorkMode: Optional[Literal["on-site", "hybrid", "remote"]] = None
    Seniority: Optional[Literal["junior", "mid", "senior", "lead"]] = None
    ExperienceYearsMin: Optional[int] = None
    EmploymentLanguage: Optional[Literal["Czech", "English", "Mixed"]] = None

    @field_validator("JobType", "WorkMode", "Seniority", "EmploymentLanguage", mode="before")
    @classmethod
    def convert_null_string(cls, v):
        if v == "null" or v == "None" or v == "":
            return None
        return v

    @field_validator("ExperienceYearsMin", mode="before")
    @classmethod
    def parse_experience(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            match = re.search(r"\d+", v)
            return int(match.group()) if match else None
        return None


class SalaryInfo(BaseModel):
    Min: Optional[float] = None
    Max: Optional[float] = None
    Currency: Optional[str] = None
    Period: Optional[Literal["hour", "day", "month", "year"]] = None  # добавил "day"

    @field_validator("Period", mode="before")
    @classmethod
    def convert_null_string(cls, v):
        if v == "null" or v == "None" or v == "":
            return None
        return v

class SalaryEstimateInfo(BaseModel):
    Avg: Optional[float] = None
    Currency: str = Field(default="CZK")
    Period: Literal["hour", "month", "year"] = Field(default="month")
    IsInferred: bool = Field(default=True)
    Confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class JobPosting(BaseModel):
    General: GeneralInfo = Field(default_factory=GeneralInfo)
    Salary: SalaryInfo = Field(default_factory=SalaryInfo)
    Salary_Estimate: SalaryEstimateInfo = Field(default_factory=SalaryEstimateInfo)
    Requirements: list[str] = Field(default_factory=list, max_length=50)
    Benefits: list[str] = Field(default_factory=list, max_length=30)
    Technologies: list[str] = Field(default_factory=list, max_length=40)
    Description: list[str] = Field(default_factory=list, max_length=60)

    @field_validator("Technologies", mode="before")
    @classmethod
    def dedupe_technologies(cls, v):
        if not v:
            return []
        seen = set()
        result = []
        for tech in v:
            normalized = tech.strip()
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                result.append(normalized)
        return result[:40]

    @field_validator("Requirements", "Benefits", "Description", mode="before")
    @classmethod
    def clean_list_items(cls, v):
        if not v:
            return []
        return [item.strip() for item in v if item and item.strip()]

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @property
    def has_salary(self) -> bool:
        return self.Salary.Min is not None or self.Salary.Max is not None

    @property
    def salary_range_text(self) -> Optional[str]:
        if not self.has_salary:
            return None
        s = self.Salary
        if s.Min and s.Max:
            return f"{s.Min:,.0f} - {s.Max:,.0f} {s.Currency}/{s.Period}"
        elif s.Min:
            return f"from {s.Min:,.0f} {s.Currency}/{s.Period}"
        elif s.Max:
            return f"up to {s.Max:,.0f} {s.Currency}/{s.Period}"
        return None