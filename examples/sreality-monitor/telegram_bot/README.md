# Telegram Bot - Sreality Monitor

Telegram bot for real estate monitoring in Czech Republic.

## Setup

### 1. Create Bot

1. Open Telegram, find @BotFather
2. Send `/newbot`
3. Enter bot name: `Sreality Monitor`
4. Enter username: `sreality_monitor_bot`
5. Copy the token

### 2. Configure

Create `.env` file:

```bash
cp .env.example .env
```

Add token:

```
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Install Dependencies

```bash
pip install python-telegram-bot python-dotenv
```

### 4. Run

```bash
python bot.py
```

## Bot Structure

```
/start
    |
    v
+---------------------------------------------+
|  [Search]  [Analytics]  [Subscriptions]     |
|              [Map]                          |
+---------------------------------------------+

Search                      Analytics
|- By Region                |- General Statistics
|- By Type                  |- Prices by Region
|- By Category              |- Top Districts
|- By Price                 |- By Category
|- New Today                |- Price Distribution
|- Price Drops              |- New This Week
                            |- Price Changes

Subscriptions
|- New Listings
|- Price Drops (%)
|- Daily Digest
|- My Subscriptions
```

## Features

### Main Menu

| Button | Action |
|--------|--------|
| Search | Search properties with filters |
| Analytics | Statistics and charts |
| Subscriptions | Notification settings |
| Map | Link to web map |

### Search

- By region (with listing count)
- By type (sale/lease)
- By category (apartments/houses/land)
- By price range
- New today
- Price drops

### Analytics

- General statistics (active, closed, average price)
- Prices by region
- Top districts
- Price distribution (text histograms)
- New this week
- Price change history

### Subscriptions

| Type | Description |
|------|-------------|
| New Listings | Notifications for new properties |
| Price Drops | Notifications when price drops (configurable %) |
| Digest | Daily report at 09:00 |

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/help` | Help |
| `/search` | Search properties |
| `/stats` | Statistics |
| `/subscribe` | Subscriptions |
| `/my_subscriptions` | My subscriptions |

## Set Commands in BotFather

```
start - Main menu
help - Help
search - Search properties
stats - Statistics
subscribe - Subscriptions
my_subscriptions - My subscriptions
```

## Files

| File | Description |
|------|-------------|
| `bot.py` | Main bot code |
| `handlers/search.py` | Search handlers |
| `handlers/analytics.py` | Analytics handlers |
| `handlers/subscriptions.py` | Subscription handlers |
| `services/notifications.py` | Notification service |
| `data/subscriptions.json` | Subscriptions storage |
| `.env` | Configuration (token) |

## Integration with Main Script

To send notifications after scraping, add to `main.py`:

```python
import asyncio
from telegram_bot.services.notifications import run_notifications

# After scraping
if new_estates or price_changes:
    asyncio.run(run_notifications(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        new_estates=new_estates,
        price_changes=price_changes
    ))
```

For daily digest use cron:

```bash
# Every day at 09:00
0 9 * * * cd /path/to/project && python -c "import asyncio; from telegram_bot.services.notifications import run_daily_digest; asyncio.run(run_daily_digest('TOKEN'))"
```
