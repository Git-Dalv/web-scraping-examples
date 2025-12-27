from scr.analysis.sql_a import *
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

matplotlib.use('Agg')

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.facecolor'] = 'white'

now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


class Analytics:
    def __init__(self, db, output_dir: str = "reports/charts"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_chart(self, fig, name: str) -> str:
        path = self.output_dir / f"{name}_{now}.png"
        fig.savefig(path, bbox_inches='tight', dpi=150, facecolor='white')
        plt.close(fig)
        return str(path)

    # ==================== Skills ====================

    def top_skills_chart(self, limit: int = 15) -> str:
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
        with self.db._get_cursor() as cursor:
            cursor.execute(SKILLS)
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
        with self.db._get_cursor() as cursor:
            cursor.execute(LOCATION, (limit,))
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
        with self.db._get_cursor() as cursor:
            cursor.execute(SENIORITY)
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
        with self.db._get_cursor() as cursor:
            cursor.execute(WORK_MODE)
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
            cursor.execute(JOBS_TIMELINE, (f'-{days} days',))
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
        with self.db._get_cursor() as cursor:
            cursor.execute(SALARY)
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
        stats = self.db.get_stats()

        with self.db._get_cursor() as cursor:
            # Top 3 skills
            cursor.execute(SUM_SKILLS)
            top_skills = [r['name'] for r in cursor.fetchall()]

            # Top location
            cursor.execute(SUM_LOCATION)
            top_location = cursor.fetchone()

            # Average salary
            cursor.execute(SUM_AVG)
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

        s = self.summary_stats()

        text = f""" *Job Market Statistics*

 *Jobs:* {s['total_jobs']} active, {s['archived_jobs']} archived
 *Companies:* {s['total_companies']}
 *Skills:* {s['total_skills']}

 *Top Skills:* {', '.join(s['top_skills'])}
 *Top Location:* {s['top_location']}
 *Avg Salary:* {s['avg_salary']} CZK/month

 *By Status:*
"""
        for status, count in s['jobs_by_status'].items():
            text += f"  • {status}: {count}\n"

        return text

    # ==================== Helpers ====================

    def _empty_chart(self, message: str, name: str) -> str:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        return self._save_chart(fig, name)

    # ==================== Filtered Skills ====================

    def top_skills_by_seniority_chart(self, seniority: str, limit: int = 15) -> str:
        with self.db._get_cursor() as cursor:
            cursor.execute(SKILLS_BY_SENIORITY, (seniority, limit))
            data = cursor.fetchall()

        if not data:
            return self._empty_chart(f"No skills data for {seniority}", f"top_skills_{seniority}")

        names = [r['name'] for r in reversed(data)]
        counts = [r['count'] for r in reversed(data)]

        fig, ax = plt.subplots(figsize=(10, max(6, limit * 0.4)))

        bars = ax.barh(names, counts, color='#2196F3')
        ax.bar_label(bars, padding=5)
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Skills for {seniority.capitalize()} Level')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, f"top_skills_{seniority}")

    def top_skills_by_work_mode_chart(self, work_mode: str, limit: int = 15) -> str:
        with self.db._get_cursor() as cursor:
            cursor.execute(SKILLS_BY_WORK_MODE, (work_mode, limit))
            data = cursor.fetchall()

        if not data:
            return self._empty_chart(f"No skills data for {work_mode}", f"top_skills_{work_mode}")

        names = [r['name'] for r in reversed(data)]
        counts = [r['count'] for r in reversed(data)]

        fig, ax = plt.subplots(figsize=(10, max(6, limit * 0.4)))

        bars = ax.barh(names, counts, color='#4CAF50')
        ax.bar_label(bars, padding=5)
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Skills for {work_mode.capitalize()} Jobs')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, f"top_skills_{work_mode}")

    # ==================== Salary by Work Mode ====================

    def salary_by_work_mode_chart(self) -> str:
        """Salary comparison by work mode."""
        with self.db._get_cursor() as cursor:
            cursor.execute(SALARY_BY_WORK_MODE)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No salary data", "salary_by_work_mode")

        modes = [r['work_mode'] for r in data]
        salaries = [r['avg_salary'] / 1000 for r in data]

        color_map = {
            'remote': '#4CAF50',
            'hybrid': '#2196F3',
            'on-site': '#FF9800'
        }
        colors = [color_map.get(m, '#90A4AE') for m in modes]

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(modes, salaries, color=colors)
        ax.bar_label(bars, fmt='%.0fk', padding=5)

        ax.set_ylabel('Average Salary (thousands)')
        ax.set_title('Estimated Salary by Work Mode (CZK/month)')
        ax.set_ylim(0, max(salaries) * 1.2)

        ax.text(0.5, -0.12, '* estimated data', transform=ax.transAxes,
                ha='center', fontsize=9, style='italic', color='gray')

        return self._save_chart(fig, "salary_by_work_mode")

    # ==================== Skills Comparison ====================

    def skills_comparison_chart(self, level1: str = 'junior', level2: str = 'senior', limit: int = 10) -> str:
        """Side-by-side comparison of skills between two seniority levels."""
        with self.db._get_cursor() as cursor:
            cursor.execute(SKILLS_FOR_LEVEL, (level1, limit))
            data1 = {r['name']: r['count'] for r in cursor.fetchall()}

            cursor.execute(SKILLS_FOR_LEVEL, (level2, limit))
            data2 = {r['name']: r['count'] for r in cursor.fetchall()}

        if not data1 and not data2:
            return self._empty_chart("No data for comparison", "skills_comparison")

        # Combine all skills
        all_skills = list(set(data1.keys()) | set(data2.keys()))[:limit]

        counts1 = [data1.get(s, 0) for s in all_skills]
        counts2 = [data2.get(s, 0) for s in all_skills]

        fig, ax = plt.subplots(figsize=(12, max(6, limit * 0.5)))

        y = range(len(all_skills))
        height = 0.35

        bars1 = ax.barh([i - height / 2 for i in y], counts1, height, label=level1.capitalize(), color='#81C784')
        bars2 = ax.barh([i + height / 2 for i in y], counts2, height, label=level2.capitalize(), color='#FFB74D')

        ax.set_yticks(y)
        ax.set_yticklabels(all_skills)
        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Skills Comparison: {level1.capitalize()} vs {level2.capitalize()}')
        ax.legend()

        ax.bar_label(bars1, padding=3, fontsize=8)
        ax.bar_label(bars2, padding=3, fontsize=8)

        return self._save_chart(fig, f"skills_comparison_{level1}_vs_{level2}")

    # ==================== Heatmap ====================

    def seniority_workmode_heatmap(self) -> str:
        with self.db._get_cursor() as cursor:
            cursor.execute(JOBS_HEATMAP)
            data = cursor.fetchall()

        if not data:
            return self._empty_chart("No data for heatmap", "heatmap")

        # Build matrix
        seniorities = ['junior', 'mid', 'senior', 'lead']
        work_modes = ['remote', 'hybrid', 'on-site']

        matrix = [[0 for _ in work_modes] for _ in seniorities]

        for row in data:
            if row['seniority'] in seniorities and row['work_mode'] in work_modes:
                i = seniorities.index(row['seniority'])
                j = work_modes.index(row['work_mode'])
                matrix[i][j] = row['count']

        fig, ax = plt.subplots(figsize=(8, 6))

        im = ax.imshow(matrix, cmap='Blues')

        ax.set_xticks(range(len(work_modes)))
        ax.set_yticks(range(len(seniorities)))
        ax.set_xticklabels(work_modes)
        ax.set_yticklabels(seniorities)

        for i in range(len(seniorities)):
            for j in range(len(work_modes)):
                text = ax.text(j, i, matrix[i][j], ha='center', va='center', color='black', fontsize=12)

        ax.set_title('Jobs by Seniority and Work Mode')
        fig.colorbar(im, ax=ax, label='Number of jobs')

        return self._save_chart(fig, "seniority_workmode_heatmap")

    # ==================== Requirements by Seniority ====================

    def requirements_by_seniority_chart(self, seniority: str, limit: int = 10) -> str:
        with self.db._get_cursor() as cursor:
            cursor.execute(REQUIREMENTS_BY_SENIORITY, (seniority, limit))
            data = cursor.fetchall()

        if not data:
            return self._empty_chart(f"No requirements for {seniority}", f"requirements_{seniority}")

        texts = [r['text'][:40] + '...' if len(r['text']) > 40 else r['text'] for r in reversed(data)]
        counts = [r['count'] for r in reversed(data)]

        fig, ax = plt.subplots(figsize=(12, max(6, limit * 0.5)))

        bars = ax.barh(texts, counts, color='#9C27B0')
        ax.bar_label(bars, padding=5)

        ax.set_xlabel('Number of jobs')
        ax.set_title(f'Top {limit} Requirements for {seniority.capitalize()} Level')
        ax.set_xlim(0, max(counts) * 1.15)

        return self._save_chart(fig, f"requirements_{seniority}")

    def generate_all(self) -> list[str]:
        charts = [
            self.top_skills_chart(),
            self.locations_chart(),
            self.top_companies_chart(),
            self.seniority_chart(),
            self.work_mode_chart(),
            self.salary_by_seniority_chart(),
            self.salary_by_work_mode_chart(),
            self.jobs_timeline_chart(),
            self.seniority_workmode_heatmap(),
        ]
        return charts

    def generate_for_seniority(self, seniority: str) -> list[str]:
        charts = [
            self.top_skills_by_seniority_chart(seniority),
            self.requirements_by_seniority_chart(seniority),
        ]
        return charts
