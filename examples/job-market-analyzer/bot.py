"""
Telegram Bot for Job Market Analytics.

Commands:
    /start - Welcome message
    /stats - Summary statistics
    /skills - Top skills chart
    /locations - Jobs by location chart
    /companies - Top hiring companies chart
    /seniority - Seniority distribution chart
    /workmode - Work mode distribution chart
    /salary - Salary by seniority chart
    /benefits - Top benefits chart
    /requirements - Top requirements chart
    /all - All charts at once
    /help - List of commands
"""

import os
import logging
import telebot
from telebot import types
from dotenv import load_dotenv

from scr.models.database import Database
from scr.analytics import Analytics

# Load environment variables
load_dotenv()

# Config
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = "job_market.db"
CHARTS_DIR = "reports/charts"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)


def get_db():
    """Get database connection."""
    return Database(DB_PATH)


def get_analytics(db):
    """Get analytics instance."""
    return Analytics(db, output_dir=CHARTS_DIR)


def send_chart(chat_id, chart_path: str, caption: str):
    """Send chart image to chat."""
    try:
        with open(chart_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
    except FileNotFoundError:
        bot.send_message(chat_id, f"❌ Chart not found: {chart_path}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error sending chart: {e}")


# ==================== Commands ====================

@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Welcome message."""
    text = """👋 *Welcome to Job Market Bot!*

I analyze job postings and provide insights about:
🛠 In-demand skills
📍 Job locations  
🏢 Hiring companies
💰 Salary estimates
📊 Market trends

Use /help to see available commands.
"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['help'])
def cmd_help(message):
    """List of commands."""
    text = """📋 *Available Commands*

*Statistics:*
/stats - Summary statistics

*Charts:*
/skills - Top 15 in-demand skills
/locations - Jobs by location
/companies - Top hiring companies
/seniority - Junior/Mid/Senior distribution
/workmode - Remote/Hybrid/On-site
/salary - Salary by seniority
/benefits - Top benefits
/requirements - Top requirements

*Other:*
/all - Send all charts
/help - This message
"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    """Summary statistics."""
    db = get_db()
    analytics = get_analytics(db)
    
    text = analytics.summary_text()
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    
    db.close()


@bot.message_handler(commands=['skills'])
def cmd_skills(message):
    """Top skills chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.top_skills_chart(15)
    send_chart(message.chat.id, chart_path, "🛠 Top 15 In-Demand Skills")
    
    db.close()


@bot.message_handler(commands=['locations'])
def cmd_locations(message):
    """Locations chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.locations_chart(10)
    send_chart(message.chat.id, chart_path, "📍 Top 10 Job Locations")
    
    db.close()


@bot.message_handler(commands=['companies'])
def cmd_companies(message):
    """Top companies chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.top_companies_chart(10)
    send_chart(message.chat.id, chart_path, "🏢 Top 10 Hiring Companies")
    
    db.close()


@bot.message_handler(commands=['seniority'])
def cmd_seniority(message):
    """Seniority distribution chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.seniority_chart()
    send_chart(message.chat.id, chart_path, "📊 Distribution by Seniority Level")
    
    db.close()


@bot.message_handler(commands=['workmode'])
def cmd_workmode(message):
    """Work mode distribution chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.work_mode_chart()
    send_chart(message.chat.id, chart_path, "🏠 Work Mode Distribution")
    
    db.close()


@bot.message_handler(commands=['salary'])
def cmd_salary(message):
    """Salary by seniority chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.salary_by_seniority_chart()
    send_chart(message.chat.id, chart_path, "💰 Estimated Salary by Seniority\n_(CZK/month)_")
    
    db.close()


@bot.message_handler(commands=['benefits'])
def cmd_benefits(message):
    """Top benefits chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.top_benefits_chart(10)
    send_chart(message.chat.id, chart_path, "🎁 Top 10 Benefits")
    
    db.close()


@bot.message_handler(commands=['requirements'])
def cmd_requirements(message):
    """Top requirements chart."""
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    chart_path = analytics.top_requirements_chart(10)
    send_chart(message.chat.id, chart_path, "📝 Top 10 Requirements")
    
    db.close()


@bot.message_handler(commands=['all'])
def cmd_all(message):
    """Send all charts."""
    bot.send_message(message.chat.id, "📊 Generating all charts...")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    db = get_db()
    analytics = get_analytics(db)
    
    charts = [
        (analytics.top_skills_chart(15), "🛠 Top Skills"),
        (analytics.locations_chart(10), "📍 Locations"),
        (analytics.top_companies_chart(10), "🏢 Companies"),
        (analytics.seniority_chart(), "📊 Seniority"),
        (analytics.work_mode_chart(), "🏠 Work Mode"),
        (analytics.salary_by_seniority_chart(), "💰 Salary"),
    ]
    
    for chart_path, caption in charts:
        send_chart(message.chat.id, chart_path, caption)
    
    # Send summary
    bot.send_message(message.chat.id, analytics.summary_text(), parse_mode='Markdown')
    
    db.close()


@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """Handle unknown messages."""
    bot.send_message(
        message.chat.id, 
        "🤔 Unknown command. Use /help to see available commands."
    )


# ==================== Main ====================

def main():
    """Start the bot."""
    logger.info("Starting Job Market Bot...")
    
    # Check token
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return
    
    # Check database
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database not found: {DB_PATH}")
        logger.warning("Run main.py first to collect job data")
    
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    # Start polling
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == '__main__':
    main()
