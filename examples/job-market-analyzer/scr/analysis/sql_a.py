SKILLS = """
                SELECT category, SUM(count) as total
                FROM skills
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY total DESC
            """

LOCATION = """
    SELECT 
    CASE 
        WHEN location LIKE 'Praha%' OR location = 'Prague' OR location LIKE 'Prague%' THEN 'Prague'
        WHEN location LIKE 'Brno%' THEN 'Brno'
        WHEN location LIKE 'Ostrava%' THEN 'Ostrava'
        WHEN location = 'Czechia' OR location = 'Czech Republic' THEN 'Czechia (remote)'
        ELSE location 
    END as location,  -- ← алиас 'location' вместо 'location_group'
    COUNT(*) as count
FROM jobs
WHERE location IS NOT NULL 
  AND location != ''
  AND location NOT IN ('null', 'None', 'Unknown')
GROUP BY 1
ORDER BY count DESC
LIMIT ?
"""

SENIORITY = """
                SELECT seniority, COUNT(*) as count
                FROM jobs
                WHERE seniority IS NOT NULL
                GROUP BY seniority
            """

WORK_MODE = """
                SELECT work_mode, COUNT(*) as count
                FROM jobs
                WHERE work_mode IS NOT NULL
                GROUP BY work_mode
            """

JOBS_TIMELINE = """
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM jobs
                WHERE scraped_at >= DATE('now', ?)
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """

SALARY = """
                SELECT seniority, 
                       AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg_salary,
                       COUNT(*) as count
                FROM jobs
                WHERE seniority IS NOT NULL 
                  AND (salary_estimate IS NOT NULL OR salary_min IS NOT NULL)
                GROUP BY seniority
                ORDER BY avg_salary
            """

#=====================================================================================================================
SUM_SKILLS = "SELECT name FROM skills ORDER BY count DESC LIMIT 3"

SUM_LOCATION = """
                SELECT location FROM jobs 
                WHERE location IS NOT NULL 
                GROUP BY location ORDER BY COUNT(*) DESC LIMIT 1
            """

SUM_AVG = """
                SELECT AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg
                FROM jobs
                WHERE salary_estimate IS NOT NULL OR salary_min IS NOT NULL
            """


# ==================== FILTERED QUERIES ====================

# Skills by seniority
SKILLS_BY_SENIORITY = """
    SELECT s.name, COUNT(*) as count
    FROM skills s
    JOIN job_skills js ON s.id = js.skill_id
    JOIN jobs j ON js.job_id = j.id
    WHERE j.seniority = ?
    GROUP BY s.name
    ORDER BY count DESC
    LIMIT ?
"""

# Skills by work_mode
SKILLS_BY_WORK_MODE = """
    SELECT s.name, COUNT(*) as count
    FROM skills s
    JOIN job_skills js ON s.id = js.skill_id
    JOIN jobs j ON js.job_id = j.id
    WHERE j.work_mode = ?
    GROUP BY s.name
    ORDER BY count DESC
    LIMIT ?
"""

# Salary by work_mode
SALARY_BY_WORK_MODE = """
    SELECT work_mode,
           AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg_salary,
           COUNT(*) as count
    FROM jobs
    WHERE work_mode IS NOT NULL
      AND (salary_estimate IS NOT NULL OR salary_min IS NOT NULL)
    GROUP BY work_mode
    ORDER BY avg_salary
"""

# Skills comparison (для двух seniority levels)
SKILLS_FOR_LEVEL = """
    SELECT s.name, COUNT(*) as count
    FROM skills s
    JOIN job_skills js ON s.id = js.skill_id
    JOIN jobs j ON js.job_id = j.id
    WHERE j.seniority = ?
    GROUP BY s.name
    ORDER BY count DESC
    LIMIT ?
"""

# Requirements by seniority
REQUIREMENTS_BY_SENIORITY = """
    SELECT r.text, COUNT(*) as count
    FROM requirements r
    JOIN job_requirements jr ON r.id = jr.requirement_id
    JOIN jobs j ON jr.job_id = j.id
    WHERE j.seniority = ?
    GROUP BY r.text
    ORDER BY count DESC
    LIMIT ?
"""

# Benefits by seniority
BENEFITS_BY_SENIORITY = """
    SELECT b.text, COUNT(*) as count
    FROM benefits b
    JOIN job_benefits jb ON b.id = jb.benefit_id
    JOIN jobs j ON jb.job_id = j.id
    WHERE j.seniority = ?
    GROUP BY b.text
    ORDER BY count DESC
    LIMIT ?
"""

# Jobs count by seniority and work_mode (for heatmap)
JOBS_HEATMAP = """
    SELECT seniority, work_mode, COUNT(*) as count
    FROM jobs
    WHERE seniority IS NOT NULL AND work_mode IS NOT NULL
    GROUP BY seniority, work_mode
"""

# Top companies by seniority
COMPANIES_BY_SENIORITY = """
    SELECT c.name, COUNT(*) as count
    FROM companies c
    JOIN jobs j ON c.id = j.company_id
    WHERE j.seniority = ?
      AND c.name NOT IN ('Unknown', 'null', 'Not specified')
    GROUP BY c.name
    ORDER BY count DESC
    LIMIT ?
"""

