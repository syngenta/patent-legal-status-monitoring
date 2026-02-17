import time
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import logging

from backend.report.weekly_report import HeaderExtraction
from backend.utils.utils import is_red_span_tag_present, reduce_html_content
from backend.prompt.prompt import chain

# ---------------- CONFIG ---------------- #

cpu_count = os.cpu_count() or 2
DEFAULT_MAX_WORKERS = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- HELPERS ---------------- #

def safe_invoke(payload: Dict, timeout: int = 60):
    """Safely invoke the chain with a timeout."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(chain.invoke, input=payload)
        return future.result(timeout=timeout)

# ---------------- CORE ---------------- #

def _process_single_soup(index: int, soup: BeautifulSoup) -> Tuple[int, List[Dict]]:
    """Process a single soup object and return results."""
    results = []
    headers = HeaderExtraction(soup).headers

    if not headers:
        return (index, results)

    has_red_span = is_red_span_tag_present(soup)

    if not has_red_span:
        for header in headers:
            results.append({"header": header, "content": None})
        return (index, results)

    reduced_html = reduce_html_content(soup)
    html_entity = safe_invoke({"html_text": reduced_html})

    for header in headers:
        results.append({"header": header, "content": html_entity})

    return (index, results)

def html_parser_optimized(
    soup_list: List[BeautifulSoup],
    max_workers: Optional[int] = 4,
    max_retries: int = 8
) -> List[Dict]:
    """Process soups with multiprocessing and retry failed ones up to max_retries."""
    if max_workers is None:
        max_workers = DEFAULT_MAX_WORKERS

    indexed_results: Dict[int, List[Dict]] = {}
    retry_counts: Dict[int, int] = {idx: 0 for idx in range(len(soup_list))}
    to_process = [(idx, soup) for idx, soup in enumerate(soup_list)]

    while to_process:
        logging.info(f"Processing {len(to_process)} items...")
        retry_queue = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(_process_single_soup, idx, soup): (idx, soup)
                for idx, soup in to_process
            }

            for future in as_completed(future_to_item):
                idx, soup = future_to_item[future]
                try:
                    index, results = future.result()
                    indexed_results[index] = results
                    logging.info(f"✅ Soup {idx} succeeded")
                except Exception as e:
                    retry_counts[idx] += 1
                    logging.warning(f"❌ Soup {idx} failed (attempt {retry_counts[idx]}): {e}")
                    if retry_counts[idx] > max_retries:
                        raise RuntimeError(f"Soup {idx} failed more than {max_retries} times") from e
                    retry_queue.append((idx, soup))

        to_process = retry_queue
        if to_process:
            logging.info(f"Retrying {len(to_process)} failed items after 1s...")

    # Combine results in original order
    output_list = []
    for idx in sorted(indexed_results.keys()):
        output_list.extend(indexed_results[idx])

    return output_list

# ---------------- SUMMARY ---------------- #

def get_author_summary(parsed_results: List[Dict]) -> Dict[str, int]:
    """Summarize author counts from parsed results."""
    author_counts = {}
    for result in parsed_results:
        author_name = result['header'].get('Author Name', 'Unknown')
        author_counts[author_name] = author_counts.get(author_name, 0) + 1
    return author_counts