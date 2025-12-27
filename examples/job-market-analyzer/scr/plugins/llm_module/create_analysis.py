from scr.plugins.llm_module.extractor import JobExtractor

from dotenv import load_dotenv

import os


async def parse_jobs(data: list[dict]) -> list[dict]:
    load_dotenv()
    api_key = os.getenv("OPEN_AI_API")

    extractor = JobExtractor(
        api_key=api_key,
        max_workers=5
    )

    texts = [job['raw_text'] for job in data]
    parsed_list = await extractor.extract_batch(texts)

    parsed_results = []
    for job, parsed in zip(data, parsed_list):
        if parsed:
            result = {k: v for k, v in job.items() if k != 'raw_text'}
            result['parsed'] = parsed.to_dict()
            parsed_results.append(result)

    return parsed_results
