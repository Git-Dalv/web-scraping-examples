# LLM Module

The LLM module extracts structured data from raw job posting HTML using OpenAI GPT-4o-mini.

## Overview

```
Raw HTML → Text Extraction → LLM Processing → Pydantic Validation → Structured Data
```

## Configuration

### Environment Variables

```
OPENAI_API_KEY=sk-your-key-here
```

### Model Settings

| Parameter | Value |
|-----------|-------|
| Model | gpt-4o-mini |
| Temperature | 0.1 |
| Max Tokens | 2000 |
| Response Format | JSON |

## Prompt Structure

The system uses two prompts:

### Main Prompt (`SYSTEM_PROMPT`)

Detailed extraction with full schema and examples. Used for first attempt.

### Fallback Prompt (`FALLBACK_PROMPT`)

Simplified extraction focusing on essential fields. Used when main prompt fails.

## Output Schema

```json
{
    "General": {
        "JobTitle": "string (REQUIRED)",
        "Company": "string (REQUIRED)",
        "Location": "string | null",
        "JobType": "full-time | part-time | contract | internship | temporary | null",
        "WorkMode": "on-site | hybrid | remote | null",
        "Seniority": "junior | mid | senior | lead | null",
        "ExperienceYearsMin": "integer | null",
        "EmploymentLanguage": "Czech | English | Mixed | null"
    },
    "Salary": {
        "Min": "number | null",
        "Max": "number | null",
        "Currency": "string | null",
        "Period": "hour | day | month | year | null"
    },
    "Salary_Estimate": {
        "Avg": "number | null",
        "Currency": "CZK",
        "Period": "month",
        "IsInferred": "boolean",
        "Confidence": "number 0.0-1.0"
    },
    "Requirements": ["string - max 10 items"],
    "Benefits": ["string - max 10 items"],
    "Technologies": ["string - max 20 items"],
    "Description": ["string - max 10 items"]
}
```

## Field Rules

### General

| Field | Rule |
|-------|------|
| JobTitle | First heading or title. Translate to English. **Never null** |
| Company | Company name from posting. **Never null** |
| Location | City or "Remote". Normalize "Czech Republic" → "Czechia" |
| Seniority | Infer from title/years: 0-2yr=junior, 3-4yr=mid, 5+yr=senior |
| ExperienceYearsMin | Minimum years only ("3-5 years" → 3) |

### Salary

- Only if **explicitly stated** with numbers
- Normalize: "80k" → 80000, "80 000" → 80000

### Salary_Estimate

- Only when Salary is null
- IsInferred: always true
- Confidence: 0.3-0.8 based on context

**Czech Market Rates:**

| Level | Estimated Salary |
|-------|------------------|
| Junior | 50,000 CZK/month |
| Mid | 80,000 CZK/month |
| Senior | 120,000 CZK/month |
| Lead | 150,000 CZK/month |

### Technologies

- Extract **ALL** mentioned: languages, frameworks, tools, cloud, databases
- Keep original casing: "Docker", "AWS", "Kubernetes"
- Normalize: "k8s" → "Kubernetes", "ReactJS" → "React"

## Pydantic Models

### Validation

```python
class GeneralInfo(BaseModel):
    JobTitle: str
    Company: str
    Location: Optional[str] = None
    JobType: Optional[Literal["full-time", "part-time", "contract", "internship", "temporary"]] = None
    WorkMode: Optional[Literal["on-site", "hybrid", "remote"]] = None
    Seniority: Optional[Literal["junior", "mid", "senior", "lead"]] = None
    ExperienceYearsMin: Optional[int] = None
    EmploymentLanguage: Optional[Literal["Czech", "English", "Mixed"]] = None
```

### Validators

- `"null"` string → `None`
- `"mid | senior"` → `"mid"` (first value)
- Experience parsing: `"3-5 years"` → `3`

## Example

### Input

```
Senior DevOps Engineer at CloudTech
Prague, hybrid model
5+ years experience, Terraform, AWS, Kubernetes, CI/CD
We offer: MacBook, flexible hours, 5 weeks vacation
```

### Output

```json
{
    "General": {
        "JobTitle": "Senior DevOps Engineer",
        "Company": "CloudTech",
        "Location": "Prague",
        "JobType": "full-time",
        "WorkMode": "hybrid",
        "Seniority": "senior",
        "ExperienceYearsMin": 5,
        "EmploymentLanguage": "English"
    },
    "Salary": {
        "Min": null,
        "Max": null,
        "Currency": null,
        "Period": null
    },
    "Salary_Estimate": {
        "Avg": 120000,
        "Currency": "CZK",
        "Period": "month",
        "IsInferred": true,
        "Confidence": 0.7
    },
    "Requirements": [
        "5+ years DevOps experience",
        "Terraform proficiency",
        "AWS experience",
        "Kubernetes knowledge",
        "CI/CD pipeline experience"
    ],
    "Benefits": [
        "MacBook provided",
        "Flexible working hours",
        "5 weeks vacation"
    ],
    "Technologies": [
        "Terraform",
        "AWS",
        "Kubernetes",
        "CI/CD"
    ],
    "Description": [
        "DevOps role in Prague office",
        "Hybrid work model"
    ]
}
```

## Parse Quality

Each job gets a `parse_quality` score (0.0 - 1.0):

| Component | Weight |
|-----------|--------|
| Technologies extracted | +0.4 |
| Requirements extracted | +0.3 |
| Benefits extracted | +0.2 |
| Valid company name | +0.1 |

Jobs with `parse_quality < 0.5` can be identified for re-processing:

```bash
python main.py --low-quality 0.5
```

## Error Handling

1. **JSON Parse Error** → Retry with fallback prompt
2. **Validation Error** → Log and skip field
3. **API Error** → Retry with exponential backoff
4. **Timeout** → Skip job, save to failed_jobs.jsonl

## Files

| File | Description |
|------|-------------|
| `prompts.py` | System prompts |
| `models.py` | Pydantic models with validators |
| `extractor.py` | LLM API calls and batch processing |
