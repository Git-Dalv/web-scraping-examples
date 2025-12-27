"""
SQL queries for Job Market database.
"""

# ==================== CREATE TABLES ====================

CREATE_COMPANIES = """
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_normalized TEXT NOT NULL UNIQUE,
        count INTEGER DEFAULT 1,
        first_seen DATE,
        last_seen DATE
    )
"""

CREATE_SKILLS = """
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_normalized TEXT NOT NULL UNIQUE,
        category TEXT,
        count INTEGER DEFAULT 1,
        first_seen DATE,
        last_seen DATE
    )
"""

CREATE_REQUIREMENTS = """
    CREATE TABLE IF NOT EXISTS requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        text_normalized TEXT NOT NULL UNIQUE,
        count INTEGER DEFAULT 1
    )
"""

CREATE_BENEFITS = """
    CREATE TABLE IF NOT EXISTS benefits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        text_normalized TEXT NOT NULL UNIQUE,
        count INTEGER DEFAULT 1
    )
"""

CREATE_JOBS = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        url TEXT,
        
        title TEXT,
        company_id INTEGER,
        location TEXT,
        job_type TEXT,
        work_mode TEXT,
        seniority TEXT,
        experience_min INTEGER,
        employment_language TEXT,
        
        salary_min REAL,
        salary_max REAL,
        salary_currency TEXT,
        salary_period TEXT,
        salary_estimate REAL,
        salary_confidence REAL,
        
        description TEXT,
        parse_quality REAL DEFAULT 0,
        
        search_job_title TEXT,
        search_location TEXT,
        
        status TEXT DEFAULT 'new',
        deadline DATE,
        scraped_at DATETIME,
        parsed_at DATETIME,
        last_checked DATETIME,
        
        UNIQUE(source, source_id),
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
"""

CREATE_JOBS_ARCHIVE = """
    CREATE TABLE IF NOT EXISTS jobs_archive (
        id INTEGER PRIMARY KEY,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        url TEXT,
        
        title TEXT,
        company_id INTEGER,
        location TEXT,
        job_type TEXT,
        work_mode TEXT,
        seniority TEXT,
        experience_min INTEGER,
        employment_language TEXT,
        
        salary_min REAL,
        salary_max REAL,
        salary_currency TEXT,
        salary_period TEXT,
        salary_estimate REAL,
        salary_confidence REAL,
        
        description TEXT,
        parse_quality REAL DEFAULT 0,
        
        status TEXT,
        deadline DATE,
        scraped_at DATETIME,
        parsed_at DATETIME,
        last_checked DATETIME,
        
        archived_at DATETIME,
        close_reason TEXT,
        lifetime_days INTEGER,
        
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
"""

CREATE_JOB_SKILLS = """
    CREATE TABLE IF NOT EXISTS job_skills (
        job_id INTEGER,
        skill_id INTEGER,
        PRIMARY KEY (job_id, skill_id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (skill_id) REFERENCES skills(id)
    )
"""

CREATE_JOB_REQUIREMENTS = """
    CREATE TABLE IF NOT EXISTS job_requirements (
        job_id INTEGER,
        requirement_id INTEGER,
        PRIMARY KEY (job_id, requirement_id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (requirement_id) REFERENCES requirements(id)
    )
"""

CREATE_JOB_BENEFITS = """
    CREATE TABLE IF NOT EXISTS job_benefits (
        job_id INTEGER,
        benefit_id INTEGER,
        PRIMARY KEY (job_id, benefit_id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (benefit_id) REFERENCES benefits(id)
    )
"""

# All tables in creation order
ALL_TABLES = [
    CREATE_COMPANIES,
    CREATE_SKILLS,
    CREATE_REQUIREMENTS,
    CREATE_BENEFITS,
    CREATE_JOBS,
    CREATE_JOBS_ARCHIVE,
    CREATE_JOB_SKILLS,
    CREATE_JOB_REQUIREMENTS,
    CREATE_JOB_BENEFITS,
]

# ==================== INDEXES ====================

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source, source_id)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name_normalized)",
    "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name_normalized)",
]

# ==================== COMPANIES ====================

SELECT_COMPANY_BY_NAME = "SELECT id FROM companies WHERE name_normalized = ?"
UPDATE_COMPANY_COUNT = "UPDATE companies SET count = count + 1, last_seen = ? WHERE id = ?"
INSERT_COMPANY = "INSERT INTO companies (name, name_normalized, first_seen, last_seen) VALUES (?, ?, ?, ?)"
SELECT_COMPANY_BY_ID = "SELECT * FROM companies WHERE id = ?"
SELECT_TOP_COMPANIES = """
    SELECT * FROM companies 
    WHERE name NOT IN ('Unknown', 'null', 'Not specified')
    ORDER BY count DESC 
    LIMIT ?
"""

# ==================== SKILLS ====================

SELECT_SKILL_BY_NAME = "SELECT id FROM skills WHERE name_normalized = ?"
UPDATE_SKILL_COUNT = "UPDATE skills SET count = count + 1, last_seen = ? WHERE id = ?"
INSERT_SKILL = "INSERT INTO skills (name, name_normalized, category, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)"
SELECT_TOP_SKILLS = "SELECT * FROM skills ORDER BY count DESC LIMIT ?"
SELECT_SKILLS_BY_CATEGORY = "SELECT * FROM skills WHERE category = ? ORDER BY count DESC"

# ==================== REQUIREMENTS ====================

SELECT_REQUIREMENT_BY_TEXT = "SELECT id FROM requirements WHERE text_normalized = ?"
UPDATE_REQUIREMENT_COUNT = "UPDATE requirements SET count = count + 1 WHERE id = ?"
INSERT_REQUIREMENT = "INSERT INTO requirements (text, text_normalized) VALUES (?, ?)"
SELECT_TOP_REQUIREMENTS = "SELECT * FROM requirements ORDER BY count DESC LIMIT ?"

# ==================== BENEFITS ====================

SELECT_BENEFIT_BY_TEXT = "SELECT id FROM benefits WHERE text_normalized = ?"
UPDATE_BENEFIT_COUNT = "UPDATE benefits SET count = count + 1 WHERE id = ?"
INSERT_BENEFIT = "INSERT INTO benefits (text, text_normalized) VALUES (?, ?)"
SELECT_TOP_BENEFITS = "SELECT * FROM benefits ORDER BY count DESC LIMIT ?"

# ==================== JOBS ====================

SELECT_JOB_EXISTS = "SELECT 1 FROM jobs WHERE source = ? AND source_id = ?"
SELECT_JOB_BY_ID = "SELECT * FROM jobs WHERE id = ?"
SELECT_JOBS_BY_STATUS = "SELECT * FROM jobs WHERE status = ? ORDER BY scraped_at DESC LIMIT ?"
SELECT_RECENT_JOBS = "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ?"
UPDATE_JOB_STATUS = "UPDATE jobs SET status = ?, last_checked = ? WHERE id = ?"
SELECT_EXPIRED_JOBS = "SELECT id FROM jobs WHERE deadline IS NOT NULL AND deadline < ?"
DELETE_JOB = "DELETE FROM jobs WHERE id = ?"

INSERT_JOB = """
    INSERT INTO jobs (
        source, source_id, url, title, company_id, location,
        job_type, work_mode, seniority, experience_min, employment_language,
        salary_min, salary_max, salary_currency, salary_period,
        salary_estimate, salary_confidence,
        description, parse_quality, search_job_title, search_location,
        status, deadline, scraped_at, parsed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ==================== JOB RELATIONS ====================

INSERT_JOB_SKILL = "INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)"
INSERT_JOB_REQUIREMENT = "INSERT OR IGNORE INTO job_requirements (job_id, requirement_id) VALUES (?, ?)"
INSERT_JOB_BENEFIT = "INSERT OR IGNORE INTO job_benefits (job_id, benefit_id) VALUES (?, ?)"

SELECT_JOB_SKILLS = """
    SELECT s.* FROM skills s
    JOIN job_skills js ON s.id = js.skill_id
    WHERE js.job_id = ?
"""

SELECT_JOB_REQUIREMENTS = """
    SELECT r.* FROM requirements r
    JOIN job_requirements jr ON r.id = jr.requirement_id
    WHERE jr.job_id = ?
"""

SELECT_JOB_BENEFITS = """
    SELECT b.* FROM benefits b
    JOIN job_benefits jb ON b.id = jb.benefit_id
    WHERE jb.job_id = ?
"""

DELETE_JOB_SKILLS = "DELETE FROM job_skills WHERE job_id = ?"
DELETE_JOB_REQUIREMENTS = "DELETE FROM job_requirements WHERE job_id = ?"
DELETE_JOB_BENEFITS = "DELETE FROM job_benefits WHERE job_id = ?"

# ==================== ARCHIVE ====================

INSERT_JOB_ARCHIVE = """
    INSERT INTO jobs_archive (
        id, source, source_id, url, title, company_id, location,
        job_type, work_mode, seniority, experience_min, employment_language,
        salary_min, salary_max, salary_currency, salary_period,
        salary_estimate, salary_confidence,
        description, status, deadline, scraped_at, parsed_at, last_checked,
        archived_at, close_reason, lifetime_days
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ==================== STATISTICS ====================

COUNT_JOBS = "SELECT COUNT(*) as count FROM jobs"
COUNT_ARCHIVED = "SELECT COUNT(*) as count FROM jobs_archive"
COUNT_COMPANIES = "SELECT COUNT(*) as count FROM companies"
COUNT_SKILLS = "SELECT COUNT(*) as count FROM skills"
COUNT_REQUIREMENTS = "SELECT COUNT(*) as count FROM requirements"
COUNT_BENEFITS = "SELECT COUNT(*) as count FROM benefits"
COUNT_JOBS_BY_STATUS = "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"


# ==================== UPDATES ====================

CHECK_ID = "SELECT id, source_id FROM jobs WHERE source = ? AND status IN ('new', 'active')"

UPDATE_IT = "UPDATE jobs SET last_checked = ?, status = 'active' WHERE source = ? AND source_id = ?"

SELECT_LOW_QUALITY_JOBS = "SELECT * FROM jobs WHERE parse_quality < ? ORDER BY parse_quality ASC"

CHECK_JOBS_BY_SEARCH = """
    SELECT id, source_id FROM jobs 
    WHERE source = ? 
      AND status IN ('new', 'active')
      AND search_job_title = ?
      AND search_location = ?
"""