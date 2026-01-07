"""
Subscriptions handler for Telegram bot
"""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db import Database

SUBS_FILE = Path(__file__).parent.parent / "data" / "subscriptions.json"


def load_subscriptions() -> dict:
    """Load subscriptions from file"""
    SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SUBS_FILE.exists():
        with open(SUBS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_subscriptions(subs: dict):
    """Save subscriptions to file"""
    SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBS_FILE, 'w') as f:
        json.dump(subs, f, indent=2, ensure_ascii=False)


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /subscribe"""
    keyboard = [
        [InlineKeyboardButton("New Listings", callback_data="sub_new")],
        [InlineKeyboardButton("Price Drops", callback_data="sub_price_drop")],
        [InlineKeyboardButton("Daily Digest", callback_data="sub_digest")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "*Subscriptions*\n\nSelect notification type:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def cmd_my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /my_subscriptions"""
    user_id = str(update.effective_user.id)
    subs = load_subscriptions()
    user_subs = subs.get(user_id, {})
    
    if not user_subs:
        text = "You have no active subscriptions."
    else:
        text = "*Your Subscriptions:*\n\n"
        
        if user_subs.get("new_listings"):
            filters = user_subs["new_listings"].get("filters", {})
            text += "*New Listings*\n"
            if filters.get("region_id"):
                text += f"   Region: {filters['region_id']}\n"
            else:
                text += "   All regions\n"
            text += "\n"
        
        if user_subs.get("price_drop"):
            min_drop = user_subs["price_drop"].get("min_percent", 5)
            text += f"*Price Drops* (>{min_drop}%)\n\n"
        
        if user_subs.get("digest"):
            time = user_subs["digest"].get("time", "09:00")
            text += f"*Daily Digest* at {time}\n"
    
    keyboard = [
        [InlineKeyboardButton("Add", callback_data="menu_subscriptions")],
        [InlineKeyboardButton("Delete All", callback_data="sub_delete_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def show_subscriptions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscriptions menu"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    subs = load_subscriptions()
    user_subs = subs.get(user_id, {})
    
    new_mark = "[ON]" if user_subs.get("new_listings") else ""
    price_mark = "[ON]" if user_subs.get("price_drop") else ""
    digest_mark = "[ON]" if user_subs.get("digest") else ""
    
    keyboard = [
        [InlineKeyboardButton(f"New Listings {new_mark}", callback_data="sub_new")],
        [InlineKeyboardButton(f"Price Drops {price_mark}", callback_data="sub_price_drop")],
        [InlineKeyboardButton(f"Daily Digest {digest_mark}", callback_data="sub_digest")],
        [InlineKeyboardButton("My Subscriptions", callback_data="sub_my")],
        [InlineKeyboardButton("<< Back", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "*Subscriptions*\n\n"
        "Set up notifications for new listings, "
        "price changes and daily reports."
    )
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def handle_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "sub_new":
        await show_new_listings_sub(update, context)
    elif data == "sub_price_drop":
        await show_price_drop_sub(update, context)
    elif data == "sub_digest":
        await toggle_digest_sub(update, context)
    elif data == "sub_my":
        await show_my_subscriptions(update, context)
    elif data == "sub_delete_all":
        await delete_all_subscriptions(update, context)
    elif data.startswith("sub_new_region_"):
        region_id = data.replace("sub_new_region_", "")
        await save_new_listing_sub(update, context, region_id=region_id)
    elif data == "sub_new_all":
        await save_new_listing_sub(update, context)
    elif data.startswith("sub_drop_"):
        percent = int(data.replace("sub_drop_", ""))
        await save_price_drop_sub(update, context, percent)


async def show_new_listings_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show new listings subscription options"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM regions ORDER BY name")
        regions = cursor.fetchall()
    
    keyboard = [[InlineKeyboardButton("All Regions", callback_data="sub_new_all")]]
    
    for r in regions:
        keyboard.append([
            InlineKeyboardButton(r[1], callback_data=f"sub_new_region_{r[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*New Listings Subscription*\n\n"
        "Select region or all:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def save_new_listing_sub(update: Update, context: ContextTypes.DEFAULT_TYPE, region_id: str = None):
    """Save new listing subscription"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    subs = load_subscriptions()
    if user_id not in subs:
        subs[user_id] = {}
    
    subs[user_id]["new_listings"] = {
        "enabled": True,
        "filters": {
            "region_id": region_id
        }
    }
    
    save_subscriptions(subs)
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Subscription saved!*\n\n"
        "You will receive notifications about new listings.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_price_drop_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show price drop subscription options"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("Any drop", callback_data="sub_drop_1")],
        [InlineKeyboardButton("> 5%", callback_data="sub_drop_5")],
        [InlineKeyboardButton("> 10%", callback_data="sub_drop_10")],
        [InlineKeyboardButton("> 15%", callback_data="sub_drop_15")],
        [InlineKeyboardButton("> 20%", callback_data="sub_drop_20")],
        [InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Price Drop Notifications*\n\n"
        "Select minimum drop percentage:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def save_price_drop_sub(update: Update, context: ContextTypes.DEFAULT_TYPE, percent: int):
    """Save price drop subscription"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    subs = load_subscriptions()
    if user_id not in subs:
        subs[user_id] = {}
    
    subs[user_id]["price_drop"] = {
        "enabled": True,
        "min_percent": percent
    }
    
    save_subscriptions(subs)
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*Subscription saved!*\n\n"
        f"You will receive notifications when price drops > {percent}%.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def toggle_digest_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle daily digest subscription"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    subs = load_subscriptions()
    if user_id not in subs:
        subs[user_id] = {}
    
    if subs[user_id].get("digest", {}).get("enabled"):
        del subs[user_id]["digest"]
        text = "*Digest disabled*"
    else:
        subs[user_id]["digest"] = {
            "enabled": True,
            "time": "09:00"
        }
        text = "*Digest enabled!*\n\nYou will receive daily report at 09:00."
    
    save_subscriptions(subs)
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def show_my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's subscriptions"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    subs = load_subscriptions()
    user_subs = subs.get(user_id, {})
    
    if not user_subs:
        text = "You have no active subscriptions."
    else:
        text = "*Your Subscriptions:*\n\n"
        
        if user_subs.get("new_listings"):
            region_id = user_subs["new_listings"].get("filters", {}).get("region_id")
            text += "*New Listings*"
            if region_id:
                text += f" (region {region_id})"
            text += "\n\n"
        
        if user_subs.get("price_drop"):
            min_drop = user_subs["price_drop"].get("min_percent", 5)
            text += f"*Price Drops* (>{min_drop}%)\n\n"
        
        if user_subs.get("digest"):
            time = user_subs["digest"].get("time", "09:00")
            text += f"*Daily Digest* at {time}\n"
    
    keyboard = [
        [InlineKeyboardButton("Delete All", callback_data="sub_delete_all")],
        [InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def delete_all_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all user subscriptions"""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    subs = load_subscriptions()
    if user_id in subs:
        del subs[user_id]
        save_subscriptions(subs)
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_subscriptions")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "All subscriptions deleted.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
