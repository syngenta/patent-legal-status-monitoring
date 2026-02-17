import sys
import logging
from pathlib import Path

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.report import weekly_report
from backend.report import create_report 
from backend.process import weekly_report_core
def main(file_path: str)->tuple:
    """Main function to process the HTML file and generate the report."""
    soup = weekly_report.HTMLParser(file_path).split_file_as_individual_author_sections()
    result = weekly_report_core.html_parser_optimized(soup, max_workers=4, max_retries=8)
    file, dir = create_report.main(result)
    return file, dir

if __name__ == "__main__":
    main("")