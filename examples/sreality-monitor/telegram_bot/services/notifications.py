"""
Notification service for sending alerts to subscribers
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from telegram import Bot
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db import Database
from src.analysis.analytics import Analytics

SUBS_FILE = Path(__file__).parent.parent / "data" / "subscriptions.json"


class NotificationService:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
    
    def load_subscriptions(self) -> dict:
        if SUBS_FILE.exists():
            with open(SUBS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    async def send_new_listing_alerts(self, new_estates: list):
        """Send alerts for new listings"""
        subs = self.load_subscriptions()
        
        for user_id, user_subs in subs.items():
            if not user_subs.get("new_listings", {}).get("enabled"):
                continue
            
            filters = user_subs["new_listings"].get("filters", {})
            region_id = filters.get("region_id")
            
            matching = []
            for estate in new_estates:
                if region_id and str(estate.get("region_id")) != str(region_id):
                    continue
                matching.append(estate)
            
            if not matching:
                continue
            
            text = f"*New Listings* ({len(matching)})\n\n"
            
            for e in matching[:5]:
                price_str = f"{e['price']:,}".replace(",", " ") if e.get('price') else "Price on request"
                text += f"- {e.get('name', 'No title')[:40]}\n"
                text += f"  {e.get('city', '')} | {price_str} CZK\n\n"
            
            if len(matching) > 5:
                text += f"_...and {len(matching) - 5} more_"
            
            try:
                await self.bot.send_message(
                    chat_id=int(user_id),
                    text=text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
    
    async def send_price_drop_alerts(self, price_changes: list):
        """Send alerts for price drops"""
        subs = self.load_subscriptions()
        
        for user_id, user_subs in subs.items():
            if not user_subs.get("price_drop", {}).get("enabled"):
                continue
            
            min_percent = user_subs["price_drop"].get("min_percent", 5)
            
            drops = []
            for change in price_changes:
                if change.get("change_pct", 0) >= 0:
                    continue
                if abs(change["change_pct"]) < min_percent:
                    continue
                drops.append(change)
            
            if not drops:
                continue
            
            text = f"*Price Drops* ({len(drops)})\n\n"
            
            for d in drops[:5]:
                old_str = f"{d['old_price']:,}".replace(",", " ")
                new_str = f"{d['new_price']:,}".replace(",", " ")
                text += f"- {d.get('name', '')[:35]}\n"
                text += f"  {d.get('city', '')} | {d['change_pct']}%\n"
                text += f"  ~{old_str}~ > *{new_str}* CZK\n\n"
            
            try:
                await self.bot.send_message(
                    chat_id=int(user_id),
                    text=text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
    
    async def send_daily_digest(self):
        """Send daily digest to subscribers"""
        subs = self.load_subscriptions()
        
        with Database() as db:
            analytics = Analytics(db)
            summary = analytics.get_summary()
            new_stats = analytics.get_new_listings_stats(1)
            changes = analytics.get_recent_price_changes(5)
        
        text = (
            f"*Daily Digest*\n"
            f"_{datetime.now().strftime('%d.%m.%Y')}_\n\n"
            f"*Statistics:*\n"
            f"  - Active: {summary['total_active']:,}\n"
            f"  - New today: {new_stats['total_new']}\n"
            f"  - Price changes: {summary['total_price_changes']}\n\n"
        )
        
        if changes:
            text += "*Recent Price Changes:*\n"
            for c in changes[:3]:
                sign = "+" if c['change_pct'] > 0 else ""
                text += f"  - {c.get('city', 'N/A')}: {sign}{c['change_pct']}%\n"
        
        for user_id, user_subs in subs.items():
            if not user_subs.get("digest", {}).get("enabled"):
                continue
            
            try:
                await self.bot.send_message(
                    chat_id=int(user_id),
                    text=text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending digest to {user_id}: {e}")


async def run_notifications(bot_token: str, new_estates: list = None, price_changes: list = None):
    """Run notification sending"""
    service = NotificationService(bot_token)
    
    if new_estates:
        await service.send_new_listing_alerts(new_estates)
    
    if price_changes:
        await service.send_price_drop_alerts(price_changes)


async def run_daily_digest(bot_token: str):
    """Run daily digest"""
    service = NotificationService(bot_token)
    await service.send_daily_digest()
