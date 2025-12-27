# Job Market Analyzer — Project Brief

## What I Need

A tool to monitor the job market in Czech Republic. Main source — jobs.cz. I want to automatically collect job postings, analyze them, and get reports.

## Why I Need This

- Understand which skills are in demand right now
- Track salary levels by position
- See which companies are actively hiring
- Follow trends (remote vs office, junior vs senior)

## Main Features

### 1. Job Collection

Should be able to:
- Search jobs by title (DevOps, Python Developer, etc.)
- Filter by city (Prague, Brno, remote)
- Collect all result pages, not just the first one
- Go into each job posting and extract details

What data to collect:
- Job title
- Company
- City/Location
- Salary (if listed)
- Required skills/technologies
- Experience requirements
- Work mode (remote, hybrid, office)
- Benefits
- Link to the job posting

### 2. Data Storage

- Save to a database (SQLite should work)
- Don't duplicate the same job
- Track when a job appeared and when it disappeared
- On repeated runs — only add new ones

### 3. Analytics

I want to see:
- Top in-demand skills
- Average salaries by level (junior/mid/senior)
- Distribution by city
- How many remote vs office positions
- Which companies hire the most
- How the number of jobs changes over time

### 4. Reports

- Charts as images (PNG)
- Text summary with key numbers
- Ability to filter (only senior, only remote, etc.)

### 5. Easy Access

Would be nice to have:
- Command line to run scraping and generate reports
- Telegram bot to quickly check stats from my phone

## Technical Stuff

### Problem with the Site

Jobs.cz is an aggregator. Some jobs open directly on the site, but others redirect to company websites. Every company has their own site, their own structure. Writing a parser for each site is not realistic.

Need to figure out how to handle this.

### Bot Protection

The site might block automated requests. Need to:
- Add pauses between requests
- Simulate human behavior
- Might need to use a real browser instead of simple HTTP requests

### Data Quality

Not all jobs are filled in equally well. Some don't have salary, some don't specify level. Need to:
- Work with incomplete data
- If possible, determine level from title ("Senior Developer" → senior)
- Mark jobs with poor data quality

## What I Want to Get

### Minimum (MVP)

- [ ] Scraper that collects jobs from jobs.cz
- [ ] Database with jobs, no duplicates
- [ ] Basic statistics (top skills, average salary)
- [ ] A few charts
- [ ] Run from command line

### Full Version

- [ ] Everything from MVP
- [ ] Track job lifecycle (new → active → closed)
- [ ] Many different charts with filters
- [ ] Compare skills between levels
- [ ] Telegram bot
- [ ] Documentation

## Usage Examples

```
# Collect DevOps jobs in Prague
python main.py --job "DevOps" --location "Praha"

# Just generate charts
python main.py --analytics

# See top skills for senior positions  
python main.py --analytics skills --seniority senior

# Compare what's needed for junior vs senior
python main.py --compare junior senior
```

## Rough Timeline

Not sure exactly how long it will take, but roughly:
- Basic scraper: 1-2 days
- Database: 0.5-1 day
- Analytics and charts: 1-2 days
- Telegram bot: 1 day
- Testing and polish: 1 day

Total: about a week of work.

## Open Questions

1. How to parse external company sites? (different structure for each)
2. What to do if the site starts blocking?
3. How to determine seniority if not explicitly stated in the job?
4. Should I store the full job text or only structured data?

---

