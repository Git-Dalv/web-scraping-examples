# Crypto News & Price Alert System

A Python-based cryptocurrency monitoring system that tracks price movements and correlates them with news sentiment analysis. This project demonstrates professional API integration, data analysis, and automated report generation.

## Overview

This system monitors top cryptocurrencies, detects significant price movements, fetches related news articles, and generates comprehensive reports linking price changes with news sentiment. Built as a practical example of working with multiple REST APIs and processing real-time financial data.

## Key Features

- **Multi-API Integration**: Seamlessly combines data from CoinGecko (price data) and CoinDesk (news articles)
- **Intelligent Price Monitoring**: Configurable threshold detection for significant price movements
- **News Sentiment Analysis**: Automatically categorizes news as positive, negative, or neutral
- **Dual Report Generation**: Creates both human-readable Markdown digests and structured JSON reports
- **Professional HTTP Client**: Built on custom `http-client-core` with retry logic, rate limiting, and circuit breakers
- **Flexible Configuration**: YAML-based configuration for API clients with sensible defaults

## API Services

### CoinGecko API
- **Purpose**: Cryptocurrency market data and historical prices
- **Endpoint**: `https://api.coingecko.com/api/v3`
- **Free Tier**: 10,000-30,000 calls/month (Demo API key)
- **Documentation**: https://www.coingecko.com/en/api/documentation
- **Registration**: https://www.coingecko.com/en/api

### CoinDesk API
- **Purpose**: Cryptocurrency news articles with sentiment scoring
- **Endpoint**: `https://data-api.coindesk.com`
- **Free Tier**: Available with API key
- **Documentation**: https://developers.coindesk.com/
- **Rate Limit**: Configurable (default: 30 requests/minute)

> **Note**: Both APIs offer generous free tiers suitable for development and personal use. For production deployments, consider paid plans for higher rate limits and guaranteed uptime.

## Project Structure
```
crypto-news-price-alert/
├── scr/
│   ├── configs/
│   │   ├── coingecko.yaml       # CoinGecko HTTP client config
│   │   └── coindesk.yaml        # CoinDesk HTTP client config
│   ├── scrapers/
│   │   ├── coingecko.py         # Price data fetcher
│   │   └── coindesk.py          # News data fetcher
│   ├── analysis/
│   │   └── analysis.py          # Price movement & news analysis
│   ├── plugins/
│   │   └── save_to.py           # Report generation (Markdown, JSON)
│   └── main.py                  # Application entry point
├── reports/                     # Generated reports output directory
├── .env                         # API keys (not in repo)
├── requirements.txt             # Python dependencies
└── README.md
```

## Module Descriptions

### `scr/scrapers/`
- **coingecko.py**: Fetches top cryptocurrencies by market cap and historical price data
- **coindesk.py**: Retrieves news articles filtered by coin and time period

### `scr/analysis/`
- **analysis.py**: 
  - `find_price_changes()`: Detects movements exceeding threshold
  - `news_analysis()`: Cleans and deduplicates news articles
  - `convert_to_df()`: Utility for DataFrame conversion

### `scr/plugins/`
- **save_to.py**:
  - `save_digest_markdown()`: Human-readable report with price movements and news
  - `create_comprehensive_json_report()`: Structured JSON with all monitored coins

### `scr/configs/`
YAML configuration files for HTTP client behavior:
- Timeout settings (connect, read, total)
- Retry logic with exponential backoff
- Circuit breaker for fault tolerance
- Rate limiting (30 req/min default)
- SSL verification and logging

## HTTP Client Core

This project uses a custom HTTP client library: **[http-client-core](https://github.com/Git-Dalv/http-client-core)**

Features:
- Automatic retry with exponential backoff
- Rate limiting with token bucket algorithm
- Circuit breaker pattern for API protection
- Structured logging (JSON format)
- SSL verification and custom headers
- Configurable via YAML files

Configuration is loaded from `scr/configs/*.yaml` files, allowing fine-tuned control over API interaction behavior without code changes.

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto-news-price-alert
```

2. Create virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure API keys:

Create `.env` file in project root:
```env
COINGECKO_API_KEY=your_coingecko_api_key_here
API_KEY2=your_coindesk_api_key_here
```

## Usage

### Basic Command
```bash
python -m scr.main
```

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--top` | int | 10 | Number of top coins to monitor |
| `--days` | int | 7 | Historical data lookback window (days) |
| `--threshold` | float | 5.0 | Price change alert threshold (%) |

### Examples

Monitor top 15 coins with 5% threshold:
```bash
python -m scr.main --top 15 --days 7 --threshold 0.05
```

Monitor top 5 coins with 10% threshold:
```bash
python -m scr.main --top 5 --threshold 0.10
```

Analyze last 14 days for top 20 coins:
```bash
python -m scr.main --top 20 --days 14 --threshold 0.05
```

## Output Examples

### Example Run
```bash
python -m scr.main --top 15 --days 7 --threshold 0.05
```

**Sample Outputs:**
- [Markdown Digest Example](link-to-digest-example.md)
- [JSON Report Example](link-to-json-example.json)

### Generated Reports

**Markdown Digest** (`reports/digest.md`)
- Human-readable format
- Price movements grouped by coin
- Related news with sentiment indicators
- Direct links to full articles
- Timestamps and percentage changes

**JSON Report** (`reports/comprehensive_report_YYYYMMDD_HHMMSS.json`)
- Complete data for all monitored coins
- Coins with normal movement vs alerts
- News article counts by sentiment
- Machine-readable for further processing
- Suitable for database import or visualization

## Example Output Structure

### JSON Report Structure
```json
{
  "generated_at": "2025-12-15T14:30:00Z",
  "threshold_percent": 5.0,
  "summary": {
    "total_coins_monitored": 15,
    "coins_with_alerts": 4,
    "coins_normal": 11,
    "total_news_articles": 8
  },
  "coins": [
    {
      "coin": "Bitcoin",
      "symbol": "BTC",
      "status": "alert",
      "movements": [...],
      "total_news": 3,
      "total_positive": 2,
      "total_negative": 1
    }
  ]
}
```

## Dependencies

Core libraries:
- `requests>=2.31.0` - HTTP requests
- `pandas>=2.0.0` - Data manipulation
- `python-dotenv>=1.0.0` - Environment variables
- `pyyaml>=6.0` - YAML configuration parsing
- `http-client-core>=1.0.0` - Custom HTTP client

See `requirements.txt` for complete list.

## Configuration

### Adjusting Rate Limits

Edit `scr/configs/coindesk.yaml` or `scr/configs/coingecko.yaml`:
```yaml
rate_limit:
  max_requests: 30      # Requests per time window
  time_window: 60.0     # Time window in seconds
```

### Timeout Settings
```yaml
timeout:
  connect: 5     # Connection timeout (seconds)
  read: 45       # Read timeout (seconds)
  total: 60      # Total request timeout (seconds)
```

### Retry Configuration
```yaml
retry:
  max_attempts: 3
  backoff_base: 3
  backoff_factor: 2.0
  backoff_max: 60.0
  backoff_jitter: true
```

## Troubleshooting

### Common Issues

**API Key Errors**
```
Error: HTTP 401 Unauthorized
```
- Verify `.env` file exists with valid API keys
- Check API key format matches provider requirements
- Ensure no extra spaces or quotes in `.env`

**Rate Limit Exceeded**
```
Error: HTTP 429 Too Many Requests
```
- Reduce `--top` parameter
- Adjust `rate_limit` in YAML configs
- Wait for rate limit window to reset

**No Price Movements Detected**
- Lower `--threshold` value (try 0.03 for 3%)
- Increase `--days` to look at longer history
- Check if market is in low-volatility period

## Best Practices

1. **API Key Security**: Never commit `.env` file to version control
2. **Rate Limiting**: Respect API provider limits to avoid throttling
3. **Error Handling**: Review logs in `/var/log/myapp/` for debugging
4. **Data Validation**: Always verify JSON outputs before downstream processing
5. **Production Use**: Consider paid API tiers for critical applications

## Acknowledgments

This project demonstrates professional API integration patterns and data processing workflows. Built as an educational example for web scraping and financial data analysis.

**Special Thanks:**
- **CoinGecko** for providing comprehensive cryptocurrency market data
- **CoinDesk** for news articles with sentiment analysis
- The open-source community for excellent Python libraries

## Recommendations

**For Learning:**
- Excellent example of multi-API integration
- Demonstrates error handling and retry logic
- Shows data correlation between different sources

**For Production:**
- Consider containerization (Docker) for deployment
- Add database storage for historical data
- Implement alerting system (email/SMS notifications)
- Set up scheduled runs with cron/systemd timers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or support, please open an issue on GitHub.

---

**Disclaimer**: This tool is for educational and informational purposes only. Not financial advice. Always conduct your own research before making investment decisions.
