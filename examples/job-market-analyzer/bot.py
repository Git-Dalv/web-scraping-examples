import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

import telebot
from telebot import types
from telebot.types import Message, CallbackQuery
from dotenv import load_dotenv

from scr.models.database import Database
from scr.analysis.analytics import Analytics
from scr.scrapers.scraper import scrape_jobs, get_jobs_page, create_client
from scr.plugins.llm_module.create_analysis import parse_jobs
from scr.plugins.workers_module.workers import JobScraper
from scr.plugins.save import save_results
from scr.models.job_saver import JobSaver

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = "job_market.db"
CHARTS_DIR = "reports/charts"
ITEMS_PER_PAGE = 10
SEARCHES_PER_PAGE = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}

STATE_MAIN = 'main'
STATE_WAITING_JOB = 'waiting_job'
STATE_WAITING_LOCATION = 'waiting_location'
STATE_SCRAPING = 'scraping'
STATE_SEARCH_SELECTED = 'search_selected'


def get_state(user_id: int) -> dict:
    if user_id not in user_states:
        user_states[user_id] = {
            'state': STATE_MAIN,
            'job_title': None,
            'location': None,
            'current_search': None,
            'page': 0,
            'filter_type': None,
            'filter_value': None,
            'last_message_id': None
        }
    return user_states[user_id]


def set_state(user_id: int, state: str = None, **kwargs):
    user_data = get_state(user_id)
    if state:
        user_data['state'] = state
    for key, value in kwargs.items():
        user_data[key] = value


def update_state(user_id: int, **kwargs):
    user_data = get_state(user_id)
    for key, value in kwargs.items():
        user_data[key] = value


def get_db() -> Database:
    return Database(DB_PATH)


def get_jobs_filtered(db: Database, filter_type: str = None, filter_value: str = None,
                      limit: int = 100, offset: int = 0) -> list[dict]:
    with db._get_cursor() as cursor:
        base_query = """
            SELECT j.*, c.name as company_name
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE 1=1
        """
        params = []

        if filter_type == 'seniority' and filter_value:
            base_query += " AND j.seniority = ?"
            params.append(filter_value)
        elif filter_type == 'work_mode' and filter_value:
            base_query += " AND j.work_mode = ?"
            params.append(filter_value)
        elif filter_type == 'location' and filter_value:
            base_query += " AND j.location LIKE ?"
            params.append(f"%{filter_value}%")
        elif filter_type == 'company' and filter_value:
            base_query += " AND c.name LIKE ?"
            params.append(f"%{filter_value}%")

        base_query += " ORDER BY j.scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_jobs_count(db: Database, filter_type: str = None, filter_value: str = None) -> int:
    with db._get_cursor() as cursor:
        base_query = """
            SELECT COUNT(*) as count
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE 1=1
        """
        params = []

        if filter_type == 'seniority' and filter_value:
            base_query += " AND j.seniority = ?"
            params.append(filter_value)
        elif filter_type == 'work_mode' and filter_value:
            base_query += " AND j.work_mode = ?"
            params.append(filter_value)
        elif filter_type == 'location' and filter_value:
            base_query += " AND j.location LIKE ?"
            params.append(f"%{filter_value}%")
        elif filter_type == 'company' and filter_value:
            base_query += " AND c.name LIKE ?"
            params.append(f"%{filter_value}%")

        cursor.execute(base_query, params)
        return cursor.fetchone()['count']


def get_filter_options(db: Database, filter_type: str) -> list[tuple]:
    with db._get_cursor() as cursor:
        if filter_type == 'seniority':
            cursor.execute("""
                SELECT seniority, COUNT(*) as count
                FROM jobs WHERE seniority IS NOT NULL
                GROUP BY seniority ORDER BY count DESC
            """)
        elif filter_type == 'work_mode':
            cursor.execute("""
                SELECT work_mode, COUNT(*) as count
                FROM jobs WHERE work_mode IS NOT NULL
                GROUP BY work_mode ORDER BY count DESC
            """)
        elif filter_type == 'location':
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN location LIKE 'Praha%' OR location LIKE 'Prague%' THEN 'Prague'
                        WHEN location LIKE 'Brno%' THEN 'Brno'
                        ELSE location 
                    END as loc,
                    COUNT(*) as count
                FROM jobs WHERE location IS NOT NULL
                GROUP BY loc ORDER BY count DESC LIMIT 10
            """)
        elif filter_type == 'company':
            cursor.execute("""
                SELECT c.name, COUNT(*) as count
                FROM companies c
                JOIN jobs j ON c.id = j.company_id
                WHERE c.name NOT IN ('Unknown', 'null', 'Not specified')
                GROUP BY c.name ORDER BY count DESC LIMIT 10
            """)
        else:
            return []

        return [(row[0], row[1]) for row in cursor.fetchall()]


def get_job_by_id(db: Database, job_id: int) -> Optional[dict]:
    with db._get_cursor() as cursor:
        cursor.execute("""
            SELECT j.*, c.name as company_name
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE j.id = ?
        """, (job_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_job_skills(db: Database, job_id: int) -> list[str]:
    with db._get_cursor() as cursor:
        cursor.execute("""
            SELECT s.name FROM skills s
            JOIN job_skills js ON s.id = js.skill_id
            WHERE js.job_id = ?
            ORDER BY s.count DESC
        """, (job_id,))
        return [row['name'] for row in cursor.fetchall()]


def main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("Find in Database"),
        types.KeyboardButton("New Search")
    )
    return keyboard


def search_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    keyboard.add(
        types.KeyboardButton("Analytics"),
        types.KeyboardButton("Job Search"),
        types.KeyboardButton("Back")
    )
    return keyboard


def analytics_inline_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("General Stats", callback_data="analytics:stats"),
        types.InlineKeyboardButton("Charts", callback_data="analytics:charts")
    )
    keyboard.add(
        types.InlineKeyboardButton("Back", callback_data="menu:back")
    )
    return keyboard


def charts_inline_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("Skills", callback_data="charts:skills"),
        types.InlineKeyboardButton("Locations", callback_data="chart:locations")
    )
    keyboard.row(
        types.InlineKeyboardButton("Companies", callback_data="chart:companies"),
        types.InlineKeyboardButton("Seniority", callback_data="chart:seniority")
    )
    keyboard.row(
        types.InlineKeyboardButton("Work Mode", callback_data="chart:workmode"),
        types.InlineKeyboardButton("Salary", callback_data="charts:salary")
    )
    keyboard.row(
        types.InlineKeyboardButton("Heatmap", callback_data="chart:heatmap"),
        types.InlineKeyboardButton("Timeline", callback_data="chart:timeline")
    )
    keyboard.row(
        types.InlineKeyboardButton("Back", callback_data="analytics:back")
    )
    return keyboard


def skills_charts_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("All Skills", callback_data="chart:skills"),
        types.InlineKeyboardButton("Junior", callback_data="chart:skills_junior")
    )
    keyboard.row(
        types.InlineKeyboardButton("Mid", callback_data="chart:skills_mid"),
        types.InlineKeyboardButton("Senior", callback_data="chart:skills_senior")
    )
    keyboard.row(
        types.InlineKeyboardButton("Compare Jr/Sr", callback_data="chart:compare_jr_sr"),
        types.InlineKeyboardButton("Compare Mid/Sr", callback_data="chart:compare_mid_sr")
    )
    keyboard.row(
        types.InlineKeyboardButton("Back", callback_data="charts:back")
    )
    return keyboard

def salary_charts_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("By Seniority", callback_data="chart:salary"),
        types.InlineKeyboardButton("By Work Mode", callback_data="chart:salary_workmode")
    )
    keyboard.row(
        types.InlineKeyboardButton("Back", callback_data="charts:back")
    )
    return keyboard


def jobs_filter_keyboard(db: Database) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    total = get_jobs_count(db)

    keyboard.add(
        types.InlineKeyboardButton(f"All Jobs ({total})", callback_data="jobs:all")
    )
    keyboard.row(
        types.InlineKeyboardButton("By Seniority", callback_data="jobs:seniority"),
        types.InlineKeyboardButton("By Work Mode", callback_data="jobs:work_mode")
    )
    keyboard.row(
        types.InlineKeyboardButton("By Location", callback_data="jobs:location"),
        types.InlineKeyboardButton("By Company", callback_data="jobs:company")
    )
    keyboard.add(
        types.InlineKeyboardButton("Back", callback_data="menu:back")
    )
    return keyboard


def filter_options_keyboard(filter_type: str, options: list[tuple]) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for value, count in options:
        if value:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{value} ({count})",
                    callback_data=f"filter:{filter_type}:{value}"
                )
            )

    keyboard.add(types.InlineKeyboardButton("Back", callback_data="jobs:back"))
    return keyboard


def jobs_list_keyboard(jobs: list[dict], page: int, total: int,
                       filter_type: str = None, filter_value: str = None) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for job in jobs:
        title = job['title'][:35] + "..." if len(job['title']) > 35 else job['title']
        company = (job.get('company_name') or 'Unknown')[:15]
        keyboard.add(
            types.InlineKeyboardButton(
                f"{title} - {company}",
                callback_data=f"job:{job['id']}"
            )
        )

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    nav_buttons = []

    ft = filter_type or ''
    fv = filter_value or ''

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("<", callback_data=f"page:{page - 1}:{ft}:{fv}"))

    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(">", callback_data=f"page:{page + 1}:{ft}:{fv}"))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.add(types.InlineKeyboardButton("Back", callback_data="jobs:back"))

    return keyboard


def job_detail_keyboard(job: dict) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if job.get('url'):
        keyboard.add(
            types.InlineKeyboardButton("Open Link", url=job['url'])
        )

    keyboard.add(
        types.InlineKeyboardButton("Back to List", callback_data="job:back")
    )
    return keyboard


def format_job_detail(job: dict, skills: list[str]) -> str:
    lines = [
        f"*{job['title']}*",
        "",
        f"Company: {job.get('company_name') or 'Unknown'}",
        f"Location: {job.get('location') or 'Unknown'}",
    ]

    if job.get('work_mode'):
        lines.append(f"Work Mode: {job['work_mode']}")

    if job.get('seniority'):
        lines.append(f"Seniority: {job['seniority']}")

    if job.get('job_type'):
        lines.append(f"Job Type: {job['job_type']}")

    if job.get('salary_min') or job.get('salary_max'):
        salary = ""
        if job.get('salary_min') and job.get('salary_max'):
            salary = f"{job['salary_min']:,.0f} - {job['salary_max']:,.0f}"
        elif job.get('salary_min'):
            salary = f"from {job['salary_min']:,.0f}"
        elif job.get('salary_max'):
            salary = f"up to {job['salary_max']:,.0f}"

        currency = job.get('salary_currency') or 'CZK'
        period = job.get('salary_period') or 'month'
        lines.append(f"Salary: {salary} {currency}/{period}")
    elif job.get('salary_estimate'):
        lines.append(f"Salary: ~{job['salary_estimate']:,.0f} CZK/month (estimated)")

    if skills:
        skills_text = ", ".join(skills[:10])
        if len(skills) > 10:
            skills_text += f" +{len(skills) - 10} more"
        lines.append(f"\nSkills: {skills_text}")

    return "\n".join(lines)


def format_stats(db: Database) -> str:
    stats = db.get_stats()

    with db._get_cursor() as cursor:
        cursor.execute("SELECT name FROM skills ORDER BY count DESC LIMIT 5")
        top_skills = [row['name'] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT location FROM jobs 
            WHERE location IS NOT NULL 
            GROUP BY location ORDER BY COUNT(*) DESC LIMIT 1
        """)
        row = cursor.fetchone()
        top_location = row['location'] if row else 'N/A'

        cursor.execute("""
            SELECT AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg
            FROM jobs
            WHERE salary_estimate IS NOT NULL OR salary_min IS NOT NULL
        """)
        row = cursor.fetchone()
        avg_salary = float(row['avg']) if row and row['avg'] else 0

    lines = [
        "*Job Market Statistics*",
        "",
        f"Total Jobs: {stats['total_jobs']}",
        f"Archived: {stats['archived_jobs']}",
        f"Companies: {stats['total_companies']}",
        f"Skills: {stats['total_skills']}",
        "",
        f"Top Skills: {', '.join(top_skills)}",
        f"Top Location: {top_location}",
        f"Avg Salary: {avg_salary:,.0f} CZK/month",
        "",
        "By Status:"
    ]

    for status, count in stats.get('jobs_by_status', {}).items():
        lines.append(f"  {status}: {count}")

    return "\n".join(lines)


@bot.message_handler(commands=['start'])
def cmd_start(message: Message):
    user_id = message.from_user.id
    set_state(user_id, STATE_MAIN)

    text = """Welcome to Job Market Analyzer Bot.

I can help you:
- Search and analyze job postings
- View market statistics and charts
- Find jobs by various filters

Select an option below:"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(commands=['help'])
def cmd_help(message: Message):
    text = """Job Market Analyzer Bot

Commands:
/start - Main menu
/help - This message

Features:
- New Search: Scrape new jobs from jobs.cz
- Find in Database: Browse existing jobs
- Analytics: View statistics and charts
- Job Search: Filter and browse jobs"""

    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "Back")
def handle_back(message: Message):
    user_id = message.from_user.id
    set_state(user_id, STATE_MAIN)

    bot.send_message(
        message.chat.id,
        "Main menu:",
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "New Search")
def handle_new_search(message: Message):
    user_id = message.from_user.id
    set_state(user_id, STATE_WAITING_JOB)

    bot.send_message(
        message.chat.id,
        "Enter job title (e.g., DevOps, Python Developer, Data Engineer):",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda m: get_state(m.from_user.id)['state'] == STATE_WAITING_JOB)
def handle_job_title_input(message: Message):
    user_id = message.from_user.id
    job_title = message.text.strip()

    set_state(user_id, STATE_WAITING_LOCATION, job_title=job_title)

    bot.send_message(
        message.chat.id,
        f"Job title: {job_title}\n\nEnter location (e.g., Praha, Brno, Remote):"
    )


@bot.message_handler(func=lambda m: get_state(m.from_user.id)['state'] == STATE_WAITING_LOCATION)
def handle_location_input(message: Message):
    user_id = message.from_user.id
    user_data = get_state(user_id)
    location = message.text.strip()
    job_title = user_data['job_title']

    set_state(user_id, STATE_SCRAPING, location=location)

    status_msg = bot.send_message(
        message.chat.id,
        f"Starting search for \"{job_title}\" in \"{location}\"...\n"
        "This may take 5-15 minutes. I will notify you when done."
    )

    asyncio.run(run_scraping(message.chat.id, user_id, job_title, location, status_msg.message_id))


async def run_scraping(chat_id: int, user_id: int, job_title: str, location: str, status_msg_id: int):
    db = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    try:
        async with create_client() as phantom:
            session = await phantom.new_session()

            try:
                jobs_page = await get_jobs_page(session, job_title, location)
                listings = await scrape_jobs(jobs_page, session)

                bot.edit_message_text(
                    f"Found {len(listings)} listings. Processing...",
                    chat_id,
                    status_msg_id
                )

                sync = db.sync_jobs_from_listing("jobs.cz", listings)

                if sync['new']:
                    scraper = JobScraper(session=session, max_workers=3)
                    raw = await scraper.scrape_all(sync['new'])

                    bot.edit_message_text(
                        f"Scraped {len(raw)} jobs. Parsing with AI...",
                        chat_id,
                        status_msg_id
                    )

                    parsed = await parse_jobs(raw)

                    saver = JobSaver(job_title=job_title, location=location, db=db, source="jobs.cz")
                    stats = saver.save_batch(parsed)

                    result_text = (
                        f"Search complete!\n\n"
                        f"Job: {job_title}\n"
                        f"Location: {location}\n\n"
                        f"Found: {len(listings)} listings\n"
                        f"New: {len(sync['new'])}\n"
                        f"Saved: {stats['saved']}\n"
                        f"Skipped: {stats['skipped']}"
                    )
                else:
                    result_text = (
                        f"Search complete!\n\n"
                        f"Job: {job_title}\n"
                        f"Location: {location}\n\n"
                        f"Found: {len(listings)} listings\n"
                        f"All jobs already in database."
                    )

                bot.edit_message_text(result_text, chat_id, status_msg_id)

            finally:
                await session.close()

    except Exception as e:
        logger.error(f"Scraping error: {e}")
        bot.edit_message_text(
            f"Error during scraping: {str(e)[:100]}",
            chat_id,
            status_msg_id
        )

    finally:
        db.close()
        set_state(user_id, STATE_MAIN)
        bot.send_message(
            chat_id,
            "Select an option:",
            reply_markup=main_menu_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "Find in Database")
def handle_find_in_database(message: Message):
    user_id = message.from_user.id
    set_state(user_id, STATE_SEARCH_SELECTED)

    bot.send_message(
        message.chat.id,
        "Select category:",
        reply_markup=search_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "Analytics")
def handle_analytics(message: Message):
    bot.send_message(
        message.chat.id,
        "Select analytics type:",
        reply_markup=analytics_inline_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "Job Search")
def handle_job_search(message: Message):
    db = get_db()
    keyboard = jobs_filter_keyboard(db)
    db.close()

    bot.send_message(
        message.chat.id,
        "Select filter:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda c: c.data == "noop")
def handle_noop(call: CallbackQuery):
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "menu:back")
def handle_menu_back(call: CallbackQuery):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("analytics:"))
def handle_analytics_callback(call: CallbackQuery):
    action = call.data.split(":")[1]

    if action == "stats":
        db = get_db()
        text = format_stats(db)
        db.close()

        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=analytics_inline_keyboard()
            )
        except:
            pass

    elif action == "charts":
        try:
            bot.edit_message_text(
                "Select chart:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=charts_inline_keyboard()
            )
        except:
            pass

    elif action == "back":
        try:
            bot.edit_message_text(
                "Select analytics type:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=analytics_inline_keyboard()
            )
        except:
            pass

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("chart:"))
def handle_chart_callback(call: CallbackQuery):
    chart_name = call.data.split(":")[1]

    db = get_db()
    analytics = Analytics(db, output_dir=CHARTS_DIR)

    chart_methods = {
        'skills': analytics.top_skills_chart,
        'skills_junior': lambda: analytics.top_skills_by_seniority_chart('junior'),
        'skills_mid': lambda: analytics.top_skills_by_seniority_chart('mid'),
        'skills_senior': lambda: analytics.top_skills_by_seniority_chart('senior'),
        'locations': analytics.locations_chart,
        'companies': analytics.top_companies_chart,
        'seniority': analytics.seniority_chart,
        'workmode': analytics.work_mode_chart,
        'salary': analytics.salary_by_seniority_chart,
        'salary_workmode': analytics.salary_by_work_mode_chart,
        'heatmap': analytics.seniority_workmode_heatmap,
        'timeline': analytics.jobs_timeline_chart,
        'compare_jr_sr': lambda: analytics.skills_comparison_chart('junior', 'senior'),
        'compare_mid_sr': lambda: analytics.skills_comparison_chart('mid', 'senior'),
    }

    if chart_name in chart_methods:
        bot.answer_callback_query(call.id, "Generating chart...")

        try:
            path = chart_methods[chart_name]()

            with open(path, 'rb') as photo:
                bot.send_photo(
                    call.message.chat.id,
                    photo,
                    caption=f"{chart_name.replace('_', ' ').title()} Chart"
                )
        except Exception as e:
            logger.error(f"Chart error: {e}")
            bot.send_message(call.message.chat.id, f"Error generating chart: {str(e)[:100]}")
    else:
        bot.answer_callback_query(call.id, "Unknown chart")

    db.close()


@bot.callback_query_handler(func=lambda c: c.data.startswith("jobs:"))
def handle_jobs_callback(call: CallbackQuery):
    action = call.data.split(":")[1]
    user_id = call.from_user.id

    db = get_db()

    try:
        if action == "all":
            jobs = get_jobs_filtered(db, limit=ITEMS_PER_PAGE, offset=0)
            total = get_jobs_count(db)

            update_state(user_id, page=0, filter_type=None, filter_value=None)

            keyboard = jobs_list_keyboard(jobs, 0, total)

            bot.edit_message_text(
                f"All Jobs ({total} total):",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )

        elif action == "back":
            keyboard = jobs_filter_keyboard(db)

            bot.edit_message_text(
                "Select filter:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )

        elif action in ['seniority', 'work_mode', 'location', 'company']:
            options = get_filter_options(db, action)
            keyboard = filter_options_keyboard(action, options)

            bot.edit_message_text(
                f"Select {action.replace('_', ' ')}:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Jobs callback error: {e}")

    db.close()
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("filter:"))
def handle_filter_callback(call: CallbackQuery):
    parts = call.data.split(":")
    filter_type = parts[1]
    filter_value = parts[2]
    user_id = call.from_user.id

    db = get_db()

    try:
        jobs = get_jobs_filtered(db, filter_type, filter_value, limit=ITEMS_PER_PAGE, offset=0)
        total = get_jobs_count(db, filter_type, filter_value)

        update_state(user_id, page=0, filter_type=filter_type, filter_value=filter_value)

        keyboard = jobs_list_keyboard(jobs, 0, total, filter_type, filter_value)

        bot.edit_message_text(
            f"{filter_type.replace('_', ' ').title()}: {filter_value} ({total} jobs):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Filter callback error: {e}")

    db.close()
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("page:"))
def handle_page_callback(call: CallbackQuery):
    parts = call.data.split(":")
    page = int(parts[1])
    filter_type = parts[2] if len(parts) > 2 and parts[2] else None
    filter_value = parts[3] if len(parts) > 3 and parts[3] else None
    user_id = call.from_user.id

    db = get_db()

    try:
        offset = page * ITEMS_PER_PAGE
        jobs = get_jobs_filtered(db, filter_type, filter_value, limit=ITEMS_PER_PAGE, offset=offset)
        total = get_jobs_count(db, filter_type, filter_value)

        update_state(user_id, page=page)

        keyboard = jobs_list_keyboard(jobs, page, total, filter_type, filter_value)

        title = "All Jobs" if not filter_type else f"{filter_type}: {filter_value}"

        bot.edit_message_text(
            f"{title} ({total} total):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Page callback error: {e}")

    db.close()
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("job:"))
def handle_job_callback(call: CallbackQuery):
    action = call.data.split(":")[1]
    user_id = call.from_user.id

    if action == "back":
        user_data = get_state(user_id)
        page = user_data.get('page', 0)
        filter_type = user_data.get('filter_type')
        filter_value = user_data.get('filter_value')

        db = get_db()

        try:
            offset = page * ITEMS_PER_PAGE
            jobs = get_jobs_filtered(db, filter_type, filter_value, limit=ITEMS_PER_PAGE, offset=offset)
            total = get_jobs_count(db, filter_type, filter_value)

            keyboard = jobs_list_keyboard(jobs, page, total, filter_type, filter_value)

            title = "All Jobs" if not filter_type else f"{filter_type}: {filter_value}"

            bot.edit_message_text(
                f"{title} ({total} total):",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Job back error: {e}")

        db.close()

    else:
        job_id = int(action)

        db = get_db()
        job = get_job_by_id(db, job_id)
        skills = get_job_skills(db, job_id)
        db.close()

        if job:
            text = format_job_detail(job, skills)
            keyboard = job_detail_keyboard(job)

            try:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Job detail error: {e}")
        else:
            bot.answer_callback_query(call.id, "Job not found")
            return

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("charts:"))
def handle_charts_submenu(call: CallbackQuery):
    action = call.data.split(":")[1]

    try:
        if action == "skills":
            bot.edit_message_text(
                "Select skills chart:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=skills_charts_keyboard()
            )
        elif action == "salary":
            bot.edit_message_text(
                "Select salary chart:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=salary_charts_keyboard()
            )
        elif action == "back":
            bot.edit_message_text(
                "Select chart:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=charts_inline_keyboard()
            )
    except Exception as e:
        logger.error(f"Charts submenu error: {e}")

    bot.answer_callback_query(call.id)


def main():
    logger.info("Starting Job Market Bot...")

    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return

    if not os.path.exists(DB_PATH):
        logger.warning(f"Database not found: {DB_PATH}")
        logger.warning("Run main.py first to collect job data")

    logger.info("Bot is running. Press Ctrl+C to stop.")

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == '__main__':
    main()