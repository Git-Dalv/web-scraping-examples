from enum import Enum


class JobType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class WorkMode(str, Enum):
    ON_SITE = "on-site"
    HYBRID = "hybrid"
    REMOTE = "remote"


class Seniority(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class EmploymentLanguage(str, Enum):
    CZECH = "czech"
    ENGLISH = "english"
    MIXED = "mixed"


class SalaryPeriod(str, Enum):
    HOUR = "hour"
    MONTH = "month"
    YEAR = "year"


class JobStatus(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"


class CloseReason(str, Enum):
    EXPIRED = "expired"
    CLOSED = "closed"
    NOT_FOUND = "404"
    DUPLICATE = "duplicate"


class SkillCategory(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    CLOUD = "cloud"
    DATABASE = "database"
    OTHER = "other"
