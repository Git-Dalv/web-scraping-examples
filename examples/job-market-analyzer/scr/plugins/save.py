from scr.plugins.helper_functions import get_project_root

import json


def load_jsonl(filepath: str) -> list[dict]:
    project_root = get_project_root()
    reports_dir = project_root / 'reports'
    file_full_path = reports_dir / filepath

    if not file_full_path.exists():
        print(f'File not found: {file_full_path}')
        return []

    jobs = []
    with open(file_full_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                jobs.append(json.loads(line))
    return jobs


def save_results(results: list[dict], filepath: str):
    project_root = get_project_root()
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)

    file_full_path = reports_dir / filepath

    with open(file_full_path, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
