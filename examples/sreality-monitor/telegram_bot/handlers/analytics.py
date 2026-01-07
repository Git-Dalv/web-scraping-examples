"""
Analytics handler for Telegram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db import Database
from src.analysis.analytics import Analytics

CHARTS_DIR = Path(__file__).parent.parent.parent / "src" / "analysis" / "charts"


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /stats"""
    await send_general_stats(update, context, is_command=True)


async def show_analytics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics menu"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("General Statistics", callback_data="analytics_stats")],
        [
            InlineKeyboardButton("Prices by Region", callback_data="analytics_regions"),
            InlineKeyboardButton("Top Districts", callback_data="analytics_districts"),
        ],
        [
            InlineKeyboardButton("By Category", callback_data="analytics_categories"),
            InlineKeyboardButton("Price Distribution", callback_data="analytics_price_dist"),
        ],
        [
            InlineKeyboardButton("New This Week", callback_data="analytics_new"),
            InlineKeyboardButton("Price Changes", callback_data="analytics_changes"),
        ],
        [InlineKeyboardButton("-- Charts --", callback_data="analytics_charts_menu")],
        [InlineKeyboardButton("<< Back", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "*Analytics*\n\nSelect section:"
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def handle_analytics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle analytics callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "analytics_stats":
        await send_general_stats(update, context)
    elif data == "analytics_regions":
        await send_region_stats(update, context)
    elif data == "analytics_districts":
        await send_district_stats(update, context)
    elif data == "analytics_categories":
        await send_category_stats(update, context)
    elif data == "analytics_price_dist":
        await send_price_distribution(update, context)
    elif data == "analytics_new":
        await send_new_listings_stats(update, context)
    elif data == "analytics_changes":
        await send_price_changes(update, context)
    elif data == "analytics_charts_menu":
        await show_charts_menu(update, context)
    elif data.startswith("analytics_chart_"):
        chart_name = data.replace("analytics_chart_", "")
        await send_chart(update, context, chart_name)


async def show_charts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show charts menu"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("Price/m2 by Region", callback_data="analytics_chart_price_per_m2_by_region")],
        [InlineKeyboardButton("Price Distribution", callback_data="analytics_chart_price_distribution")],
        [InlineKeyboardButton("Price/m2 Distribution", callback_data="analytics_chart_price_per_m2_distribution")],
        [InlineKeyboardButton("Top Districts", callback_data="analytics_chart_top_districts")],
        [InlineKeyboardButton("Category Distribution", callback_data="analytics_chart_category_distribution")],
        [InlineKeyboardButton("New Listings Timeline", callback_data="analytics_chart_new_listings_timeline")],
        [InlineKeyboardButton("Price by Category", callback_data="analytics_chart_price_by_category")],
        [InlineKeyboardButton("<< Back", callback_data="menu_analytics")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Charts*\n\nSelect chart to view:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def send_chart(update: Update, context: ContextTypes.DEFAULT_TYPE, chart_name: str):
    """Send chart image"""
    query = update.callback_query
    
    chart_path = CHARTS_DIR / f"{chart_name}.png"
    
    keyboard = [[InlineKeyboardButton("<< Back to Charts", callback_data="analytics_charts_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if chart_path.exists():
        await query.message.reply_photo(
            photo=open(chart_path, 'rb'),
            reply_markup=reply_markup
        )
        await query.message.delete()
    else:
        await query.edit_message_text(
            f"Chart not found. Run chart generation first:\n`python -m src.analysis.charts`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


async def send_general_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, is_command: bool = False):
    """Send general statistics"""
    with Database() as db:
        analytics = Analytics(db)
        summary = analytics.get_summary()
    
    text = (
        "*General Statistics*\n\n"
        f"*Active listings:* {summary['total_active']:,}\n"
        f"*Closed:* {summary['total_closed']:,}\n\n"
        f"*Average price:* {summary['avg_price']:,} CZK\n"
        f"*Average price/m2:* {summary['avg_price_m2']:,} CZK\n\n"
        f"*Min price:* {summary['min_price']:,} CZK\n"
        f"*Max price:* {summary['max_price']:,} CZK\n\n"
        f"*Price changes:* {summary['total_price_changes']}\n"
        f"*Agencies:* {summary['total_agencies']}"
    )
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_command:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def send_region_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send price by region stats"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        regions = analytics.get_price_by_region()
    
    text = "*Average Price/m2 by Region*\n\n"
    
    for i, r in enumerate(regions[:10], 1):
        text += f"{i}. *{r['region']}*\n"
        text += f"   {r['avg_price_m2']:,} CZK/m2 ({r['count']:,} listings)\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def send_district_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send top districts stats"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        districts = analytics.get_top_districts(10)
    
    text = "*Top Districts by Listings*\n\n"
    
    for i, d in enumerate(districts, 1):
        text += f"{i}. *{d['district']}* ({d['region']})\n"
        text += f"   {d['count']:,} listings | {d['avg_price_m2']:,} CZK/m2\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def send_category_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send category breakdown"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        categories = analytics.get_price_by_category()
    
    text = "*By Category*\n\n"
    
    for c in categories[:10]:
        text += f"*{c['type']} - {c['category']}*\n"
        text += f"   {c['count']:,} listings | ~{c['avg_price']:,} CZK\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def send_price_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send price distribution"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        dist = analytics.get_price_distribution()
    
    text = "*Price Distribution (Sale)*\n\n"
    
    max_count = max(p['count'] for p in dist['sale_price']) or 1
    
    for p in dist['sale_price']:
        bar_len = int(p['count'] / max_count * 10)
        bar = "#" * bar_len + "." * (10 - bar_len)
        text += f"`{p['range']:>8}` {bar} {p['count']:,}\n"
    
    text += "\n*Price/m2 Distribution*\n\n"
    
    max_count = max(p['count'] for p in dist['price_per_m2']) or 1
    
    for p in dist['price_per_m2']:
        bar_len = int(p['count'] / max_count * 10)
        bar = "#" * bar_len + "." * (10 - bar_len)
        text += f"`{p['range']:>8}` {bar} {p['count']:,}\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def send_new_listings_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send new listings statistics"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        new_stats = analytics.get_new_listings_stats(7)
    
    text = f"*New Listings (Last 7 Days)*\n\n"
    text += f"Total: *{new_stats['total_new']:,}*\n\n"
    
    text += "*By Category:*\n"
    for c in new_stats['by_category']:
        text += f"  - {c['category']}: {c['count']}\n"
    
    text += "\n*Top Regions:*\n"
    for r in new_stats['top_regions']:
        text += f"  - {r['region']}: {r['count']}\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def send_price_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send recent price changes"""
    query = update.callback_query
    
    with Database() as db:
        analytics = Analytics(db)
        changes = analytics.get_recent_price_changes(10)
    
    if not changes:
        text = "*Price Changes*\n\nNo price changes recorded yet."
    else:
        text = "*Recent Price Changes*\n\n"
        
        for c in changes:
            arrow = "[UP]" if c['change_pct'] > 0 else "[DOWN]"
            sign = "+" if c['change_pct'] > 0 else ""
            text += f"{arrow} *{c['city']}*: {sign}{c['change_pct']}%\n"
            text += f"   {c['old_price']:,} > {c['new_price']:,} CZK\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_analytics")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
