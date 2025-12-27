# Project Challenges & Solutions

This document describes the key technical challenges encountered during development and the solutions implemented.

## Table of Contents

1. [External Redirects Problem](#1-external-redirects-problem)
2. [Anti-Bot Protection](#2-anti-bot-protection)
3. [Data Normalization](#3-data-normalization)
4. [Job Lifecycle Management](#4-job-lifecycle-management)
5. [Unstructured Data Extraction](#5-unstructured-data-extraction)

---

## 1. External Redirects Problem

### Problem

The target job board (jobs.cz) aggregates listings from multiple sources. When scraping job details, approximately 30-40% of listings redirect to external company websites instead of showing job details directly.

```
jobs.cz/listing → Click job → External site (company career page)
                           → Different HTML structure
                           → Different data format
                           → Sometimes requires authentication
```

**Challenges:**
- Each external site has unique HTML structure
- Writing parsers for hundreds of different sites is impractical
- Some sites block automated access
- Data fields vary significantly between sites

### Attempted Solutions

| Approach | Result |
|----------|--------|
| Multiple parsers | Too many sites, not scalable |
| Generic HTML extraction | Poor accuracy, missed data |
| CSS selector patterns | Inconsistent across sites |
| Headless browser only | Slow, still needs parsing logic |

### Final Solution

Implemented LLM-based extraction using GPT-4o-mini:

1. **Extract raw text** from any HTML structure
2. **Send to LLM** with structured prompt
3. **Receive normalized JSON** regardless of source

**Benefits:**
- Works with any HTML structure
- No site-specific code needed
- Handles multiple languages (Czech, English, German)
- Extracts implicit data (seniority from title, salary estimates)

**Trade-offs:**
- API cost (~$0.001-0.002 per job)
- Slower than direct parsing (~1-2s per job)
- Requires quality validation

See [LLM.md](LLM.md) for implementation details.

---

## 2. Anti-Bot Protection

### Problem

Modern job sites implement various anti-bot measures:

- Cloudflare protection
- Rate limiting
- Browser fingerprinting
- CAPTCHA challenges
- JavaScript-required rendering

### Solution

Used [phantom-persona](https://github.com/your-username/phantom-persona) library with:

**Browser Automation:**
```python
async with create_client() as phantom:
    session = await phantom.new_session()
    # Real browser with anti-detection
```

**Features used:**
- Real Chromium browser via Playwright
- Randomized user agents
- Human-like delays between requests
- Cookie/session persistence
- Proxy rotation support

**Rate Limiting:**
```python
# 3 concurrent workers with delays
scraper = JobScraper(session=session, max_workers=3)
await asyncio.sleep(random.uniform(1, 3))
```

---

## 3. Data Normalization

### Problem

Job data comes in inconsistent formats:

**Locations:**
```
"Praha - Stodůlky"
"Prague"
"Praha 5"
"Hlavní město Praha"
"Czech Republic"
```

**Companies:**
```
"Komerční banka, a.s."
"Komerční banka"
"KB"
```

**Skills:**
```
"k8s" vs "Kubernetes"
"ReactJS" vs "React" vs "React.js"
"AWS" vs "Amazon Web Services"
```

### Solution

**Database-level normalization:**
```sql
-- Normalized field for deduplication
name_normalized TEXT NOT NULL UNIQUE
```

**Application-level normalization:**
```python
@staticmethod
def _normalize(text: str) -> str:
    return text.strip().lower()
```

**Analytics-level grouping:**
```sql
CASE 
    WHEN location LIKE 'Praha%' OR location = 'Prague' THEN 'Prague'
    WHEN location LIKE 'Brno%' THEN 'Brno'
    ELSE location 
END as location
```

**LLM-level normalization:**
```
Prompt: "Normalize: k8s → Kubernetes, ReactJS → React"
```

---

## 4. Job Lifecycle Management

### Problem

Jobs appear and disappear from listings. Need to track:
- New jobs (first seen)
- Active jobs (still in listing)
- Closed jobs (removed from listing)
- Expired jobs (past deadline)

**Initial bug:** Running different search queries marked unrelated jobs as "closed":

```
Search "DevOps, Praha" → 100 jobs in DB
Search "Python, Brno" → DevOps jobs not found → Marked as closed ❌
```

### Solution

Added search context to job records:

```sql
ALTER TABLE jobs ADD COLUMN search_job_title TEXT;
ALTER TABLE jobs ADD COLUMN search_location TEXT;
```

Sync only compares jobs with matching search:

```python
def sync_jobs_from_listing(self, source, found_jobs, job_title, location):
    cursor.execute("""
        SELECT id, source_id FROM jobs 
        WHERE source = ? 
          AND status IN ('new', 'active')
          AND search_job_title = ?
          AND search_location = ?
    """, (source, job_title, location))
```

**Lifecycle:**
```
new → active → closed → archive
         ↓
      expired → archive
```

---

## 5. Unstructured Data Extraction

### Problem

Job postings contain unstructured text with embedded information:

```
"We're looking for a Senior Developer with 5+ years of experience
in Python, Django, and PostgreSQL. Remote-first company offering
competitive salary (80-120k CZK), MacBook, and flexible hours."
```

Need to extract:
- Seniority: Senior
- Experience: 5+ years
- Skills: Python, Django, PostgreSQL
- Work mode: Remote
- Salary: 80,000 - 120,000 CZK
- Benefits: MacBook, flexible hours

### Solution

Structured LLM prompt with explicit schema:

```json
{
    "General": {
        "Seniority": "junior | mid | senior | lead",
        "ExperienceYearsMin": "integer"
    },
    "Salary": {
        "Min": "number",
        "Max": "number"
    },
    "Technologies": ["string"],
    "Benefits": ["string"]
}
```

**Seniority inference rules:**
```
0-2 years → junior
3-4 years → mid
5+ years → senior
Title contains "lead/principal/staff" → lead
```

**Salary estimation** when not explicitly stated:
```
Junior: ~50,000 CZK/month
Mid: ~80,000 CZK/month
Senior: ~120,000 CZK/month
Lead: ~150,000 CZK/month
```

---

## Lessons Learned

1. **Flexibility over precision** — LLM extraction trades perfect accuracy for universal compatibility

2. **Normalize early** — Database normalization prevents duplicate data issues

3. **Context matters** — Search context prevents false "closed" status

4. **Real browsers work** — Anti-bot measures are designed for simple HTTP clients

5. **Quality tracking** — `parse_quality` field helps identify extraction issues

---

## Future Improvements

| Challenge | Potential Solution |
|-----------|-------------------|
| LLM cost | Local model (Llama) for simple extractions |
| Speed | Parallel LLM requests with rate limiting |
| Accuracy | Fine-tuned model on job posting data |
| Coverage | Additional job boards (LinkedIn, Indeed) |
