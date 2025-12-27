# Job Market Analyzer

Automated job market monitoring system that scrapes job postings, extracts structured data using LLM, stores in database, and provides analytics via CLI and Telegram bot.

Built with [phantom-persona](https://github.com/your-username/phantom-persona) — a Playwright-based library for browser automation with anti-detection features.

## Features

- **Automated Scraping** — collects job postings from jobs.cz with anti-detection
- **LLM Parsing** — extracts skills, requirements, salary using GPT-4o-mini
- **Normalized Database** — SQLite with relations (companies, skills, requirements)
- **Analytics** — generates charts for skills demand, salary trends, locations
- **Telegram Bot** — instant access to analytics and job search
- **CLI Interface** — flexible command-line tool for all operations

## Quick Start

```bash
# Clone
git clone https://github.com/your-username/job-market-analyzer.git
cd job-market-analyzer

# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install
pip install -r requirements.txt
playwright install chromium

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
python main.py
```

## Configuration

Create `.env` file:

```
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
```

## Usage

### Full Pipeline

```bash
python main.py                                    # Default: DevOps in Praha
python main.py --job "Python Developer" --location "Brno"
```

### From Existing Data

```bash
python main.py --from-raw raw_jobs.jsonl          # Skip scraping
python main.py --from-parsed parsed_jobs.jsonl    # Skip scraping + LLM
```

### Analytics Only

```bash
python main.py --analytics                        # All charts
python main.py --analytics skills salary          # Specific charts
python main.py --analytics skills --seniority senior
python main.py --compare junior senior            # Skills comparison
```

### Database Info

```bash
python main.py --stats                            # Show statistics
python main.py --low-quality 0.5                  # Jobs with poor parsing
```

### Telegram Bot

```bash
python bot.py
```

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--job`, `-j` | Job title to search (default: DevOps) |
| `--location`, `-l` | Location to search (default: Praha) |
| `--from-raw FILE` | Parse from existing raw file |
| `--from-parsed FILE` | Save from existing parsed file |
| `--analytics [CHARTS]` | Generate analytics |
| `--seniority LEVEL` | Filter by seniority (junior/mid/senior/lead) |
| `--work-mode MODE` | Filter by work mode (remote/hybrid/on-site) |
| `--compare L1 L2` | Compare skills between levels |
| `--stats` | Show database statistics |
| `--low-quality N` | Show jobs with quality < N |
| `--skip-analytics` | Skip chart generation |
| `--db PATH` | Database path (default: job_market.db) |
| `--output-dir PATH` | Charts output directory |
| `--debug`, `-d` | Debug logging |
| `--quiet`, `-q` | Minimal output |

## Available Charts

| Chart | Command |
|-------|---------|
| Top Skills | `--analytics skills` |
| Skills by Seniority | `--analytics skills --seniority senior` |
| Skills Comparison | `--compare junior senior` |
| Locations | `--analytics locations` |
| Companies | `--analytics companies` |
| Seniority Distribution | `--analytics seniority` |
| Work Mode Distribution | `--analytics workmode` |
| Salary by Seniority | `--analytics salary` |
| Salary by Work Mode | `--analytics salary_workmode` |
| Seniority/WorkMode Heatmap | `--analytics heatmap` |
| Jobs Timeline | `--analytics timeline` |

## Project Structure

```
job-market-analyzer/
├── main.py                 # CLI entry point
├── bot.py                  # Telegram bot
├── scr/
│   ├── analysis/
│   │   ├── analytics.py    # Chart generation
│   │   └── sql_a.py        # Analytics SQL queries
│   ├── models/
│   │   ├── database.py     # Database operations
│   │   ├── sql.py          # SQL queries
│   │   ├── job_saver.py    # Save parsed jobs
│   │   └── enums.py        # Enums
│   ├── plugins/
│   │   ├── llm_module/
│   │   │   ├── extractor.py
│   │   │   ├── models.py
│   │   │   └── prompts.py
│   │   └── workers_module/
│   │       └── workers.py
│   └── scrapers/
│       └── scraper.py
├── docs/
│   ├── LLM.md
│   ├── DATABASE.md
│   ├── CHARTS.md
│   └── TGBOT.md
└── reports/charts/
```

## Documentation

| Document | Description |
|----------|-------------|
| [LLM.md](docs/LLM.md) | LLM parsing configuration and schema |
| [DATABASE.md](docs/DATABASE.md) | Database schema and queries |
| [CHARTS.md](docs/CHARTS.md) | Analytics and chart examples |
| [TGBOT.md](docs/TGBOT.md) | Telegram bot usage |

## Tech Stack

- **Scraping**: Playwright, BeautifulSoup, phantom-persona
- **LLM**: OpenAI GPT-4o-mini
- **Database**: SQLite
- **Analytics**: Matplotlib
- **Bot**: pyTelegramBotAPI

## License

MIT
