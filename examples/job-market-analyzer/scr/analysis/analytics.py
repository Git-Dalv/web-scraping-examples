"""
Analytics module for Job Market.
Generates PNG charts for Telegram bot.
"""

import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# No GUI
matplotlib.use('Agg')

# Chart style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.facecolor'] = 'white'


class Analytics:
    """Generates analytical charts."""

    def __init__(self, db, output_dir: str = "reports/charts"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_chart(self, fig, name: str) -> str:
        """Saves chart and returns path."""
        path = self.output_dir / f"{name}.png"
        fig.savefig(path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        return str(path)

    # ==================== Skills ====================

    def top_skills_chart(self, limit: int = 15) -> str:
        """Top skills — horizontal bar chart."""
        skills = self.db.get_top_skills(limit)
        
        if not skills:
            return self._empty_chart("No skills data", "top_skills")

        names = [s['name'] for s in reversed(skills)]
        counts = [s['count'] for s in reversed(skills)]

        fig, ax = plt.subplots(figsize=(10, max(6, limit * 0.4)))
        
        bars = ax.barh(names, counts, color='#2196F3')
        ax.bar_label(bars, padding=5)
        
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} In-Demand Skills')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, "top_skills")

    def skills_by_category_chart(self) -> str:
        """Skills by category — pie chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT category, SUM(count) as total
                FROM skills
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY total DESC
            """)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No category data", "skills_by_category")

        categories = [r['category'] or 'other' for r in data]
        totals = [r['total'] for r in data]

        fig, ax = plt.subplots(figsize=(8, 8))
        
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336', '#00BCD4']
        ax.pie(totals, labels=categories, autopct='%1.1f%%', colors=colors[:len(categories)])
        ax.set_title('Skills by Category')

        return self._save_chart(fig, "skills_by_category")

    # ==================== Locations ====================

    def locations_chart(self, limit: int = 10) -> str:
        """Jobs by location — horizontal bar chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT location, COUNT(*) as count
                FROM jobs
                WHERE location IS NOT NULL AND location != ''
                GROUP BY location
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No location data", "locations")

        locations = [r['location'][:30] for r in reversed(data)]
        counts = [r['count'] for r in reversed(data)]

        fig, ax = plt.subplots(figsize=(10, max(6, limit * 0.4)))
        
        bars = ax.barh(locations, counts, color='#4CAF50')
        ax.bar_label(bars, padding=5)
        
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Locations')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, "locations")

    # ==================== Companies ====================

    def top_companies_chart(self, limit: int = 10) -> str:
        """Top companies by job count."""
        companies = self.db.get_top_companies(limit)

        if not companies:
            return self._empty_chart("No company data", "top_companies")

        names = [c['name'][:25] for c in reversed(companies)]
        counts = [c['count'] for c in reversed(companies)]

        fig, ax = plt.subplots(figsize=(10, max(6, limit * 0.4)))
        
        bars = ax.barh(names, counts, color='#FF9800')
        ax.bar_label(bars, padding=5)
        
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Hiring Companies')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, "top_companies")

    # ==================== Seniority ====================

    def seniority_chart(self) -> str:
        """Distribution by seniority — pie chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT seniority, COUNT(*) as count
                FROM jobs
                WHERE seniority IS NOT NULL
                GROUP BY seniority
            """)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No seniority data", "seniority")

        labels = [r['seniority'] for r in data]
        counts = [r['count'] for r in data]

        color_map = {
            'junior': '#81C784',
            'mid': '#64B5F6', 
            'senior': '#FFB74D',
            'lead': '#E57373'
        }
        colors = [color_map.get(l, '#90A4AE') for l in labels]

        fig, ax = plt.subplots(figsize=(8, 8))
        
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.02] * len(labels)
        )
        ax.set_title('Distribution by Seniority Level')

        return self._save_chart(fig, "seniority")

    # ==================== Work Mode ====================

    def work_mode_chart(self) -> str:
        """Distribution by work mode — pie chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT work_mode, COUNT(*) as count
                FROM jobs
                WHERE work_mode IS NOT NULL
                GROUP BY work_mode
            """)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No work mode data", "work_mode")

        labels = [r['work_mode'] for r in data]
        counts = [r['count'] for r in data]

        color_map = {
            'remote': '#4CAF50',
            'hybrid': '#2196F3',
            'on-site': '#FF9800'
        }
        colors = [color_map.get(l, '#90A4AE') for l in labels]

        fig, ax = plt.subplots(figsize=(8, 8))
        
        ax.pie(counts, labels=labels, autopct='%1.1f%%', colors=colors)
        ax.set_title('Work Mode Distribution')

        return self._save_chart(fig, "work_mode")

    # ==================== Requirements ====================

    def top_requirements_chart(self, limit: int = 10) -> str:
        """Top requirements."""
        requirements = self.db.get_top_requirements(limit)

        if not requirements:
            return self._empty_chart("No requirements data", "top_requirements")

        texts = [r['text'][:40] + '...' if len(r['text']) > 40 else r['text'] for r in reversed(requirements)]
        counts = [r['count'] for r in reversed(requirements)]

        fig, ax = plt.subplots(figsize=(12, max(6, limit * 0.5)))
        
        bars = ax.barh(texts, counts, color='#9C27B0')
        ax.bar_label(bars, padding=5)
        
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Requirements')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, "top_requirements")

    # ==================== Benefits ====================

    def top_benefits_chart(self, limit: int = 10) -> str:
        """Top benefits."""
        benefits = self.db.get_top_benefits(limit)

        if not benefits:
            return self._empty_chart("No benefits data", "top_benefits")

        texts = [b['text'][:40] + '...' if len(b['text']) > 40 else b['text'] for b in reversed(benefits)]
        counts = [b['count'] for b in reversed(benefits)]

        fig, ax = plt.subplots(figsize=(12, max(6, limit * 0.5)))
        
        bars = ax.barh(texts, counts, color='#00BCD4')
        ax.bar_label(bars, padding=5)
        
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Benefits')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, "top_benefits")

    # ==================== Timeline ====================

    def jobs_timeline_chart(self, days: int = 30) -> str:
        """New jobs by day — line chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM jobs
                WHERE scraped_at >= DATE('now', ?)
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """, (f'-{days} days',))
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No timeline data", "jobs_timeline")

        dates = [r['date'] for r in data]
        counts = [r['count'] for r in data]

        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(dates, counts, marker='o', linewidth=2, markersize=6, color='#2196F3')
        ax.fill_between(dates, counts, alpha=0.3, color='#2196F3')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of jobs')
        ax.set_title(f'New Jobs Over Last {days} Days')
        
        plt.xticks(rotation=45, ha='right')

        return self._save_chart(fig, "jobs_timeline")

    # ==================== Salary ====================

    def salary_by_seniority_chart(self) -> str:
        """Salary by seniority — bar chart."""
        with self.db._get_cursor() as cursor:
            cursor.execute("""
                SELECT seniority, 
                       AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg_salary,
                       COUNT(*) as count
                FROM jobs
                WHERE seniority IS NOT NULL 
                  AND (salary_estimate IS NOT NULL OR salary_min IS NOT NULL)
                GROUP BY seniority
                ORDER BY avg_salary
            """)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No salary data", "salary_by_seniority")

        levels = [r['seniority'] for r in data]
        salaries = [r['avg_salary'] / 1000 for r in data]

        color_map = {
            'junior': '#81C784',
            'mid': '#64B5F6',
            'senior': '#FFB74D',
            'lead': '#E57373'
        }
        colors = [color_map.get(l, '#90A4AE') for l in levels]

        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(levels, salaries, color=colors)
        ax.bar_label(bars, fmt='%.0fk', padding=5)
        
        ax.set_ylabel('Average Salary (thousands)')
        ax.set_title('Estimated Salary by Seniority (CZK/month)')
        ax.set_ylim(0, max(salaries) * 1.2)

        ax.text(0.5, -0.12, '* estimated data', transform=ax.transAxes, 
                ha='center', fontsize=9, style='italic', color='gray')

        return self._save_chart(fig, "salary_by_seniority")

    # ==================== Summary ====================

    def summary_stats(self) -> dict:
        """Get summary statistics."""
        stats = self.db.get_stats()
        
        with self.db._get_cursor() as cursor:
            # Top 3 skills
            cursor.execute("SELECT name FROM skills ORDER BY count DESC LIMIT 3")
            top_skills = [r['name'] for r in cursor.fetchall()]
            
            # Top location
            cursor.execute("""
                SELECT location FROM jobs 
                WHERE location IS NOT NULL 
                GROUP BY location ORDER BY COUNT(*) DESC LIMIT 1
            """)
            top_location = cursor.fetchone()
            
            # Average salary
            cursor.execute("""
                SELECT AVG(COALESCE(salary_estimate, (salary_min + salary_max) / 2)) as avg
                FROM jobs
                WHERE salary_estimate IS NOT NULL OR salary_min IS NOT NULL
            """)
            avg_salary = cursor.fetchone()

        return {
            'total_jobs': stats['total_jobs'],
            'total_companies': stats['total_companies'],
            'total_skills': stats['total_skills'],
            'archived_jobs': stats['archived_jobs'],
            'top_skills': top_skills,
            'top_location': top_location['location'] if top_location else 'N/A',
            'avg_salary': f"{avg_salary['avg']:,.0f}" if avg_salary and avg_salary['avg'] else 'N/A',
            'jobs_by_status': stats['jobs_by_status'],
        }

    def summary_text(self) -> str:
        """Formatted text summary for Telegram."""
        s = self.summary_stats()
        
        text = f"""📊 *Job Market Statistics*

📋 *Jobs:* {s['total_jobs']} active, {s['archived_jobs']} archived
🏢 *Companies:* {s['total_companies']}
🛠 *Skills:* {s['total_skills']}

🔥 *Top Skills:* {', '.join(s['top_skills'])}
📍 *Top Location:* {s['top_location']}
💰 *Avg Salary:* {s['avg_salary']} CZK/month

📈 *By Status:*
"""
        for status, count in s['jobs_by_status'].items():
            text += f"  • {status}: {count}\n"

        return text

    # ==================== Helpers ====================

    def _empty_chart(self, message: str, name: str) -> str:
        """Creates empty chart with message."""
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        return self._save_chart(fig, name)

    def generate_all(self) -> list[str]:
        """Generates all charts. Returns list of paths."""
        charts = [
            self.top_skills_chart(),
            self.locations_chart(),
            self.top_companies_chart(),
            self.seniority_chart(),
            self.work_mode_chart(),
            self.salary_by_seniority_chart(),
            self.jobs_timeline_chart(),
        ]
        return charts
