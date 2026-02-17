import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import tempfile
from .templates import HTML_TEMPLATE


class PatentHTMLReportGenerator:
    """
    Generate simple black and white HTML reports for patent changes grouped by author.
    Preserves red span tags for strikethrough and underline with transition arrows.
    Also includes patents without red span changes (header-only entries).
    """
    
    def __init__(self):
        self.html_template = HTML_TEMPLATE

    @staticmethod
    def extract_clean_title(title_text: str) -> str:
        """Extract clean title from the Title field"""
        if not title_text:
            return "N/A"
        pattern = r'^(.+?)(?=\nApplicant\(s\):)'
        match = re.search(pattern, title_text, re.DOTALL)
        if match:
            return ' '.join(match.group(1).strip().split())
        return ' '.join(title_text.strip().split())

    @staticmethod
    def extract_clean_applicants(applicants_text: str) -> str:
        """Extract clean applicants from the Applicant(s) field"""
        if not applicants_text:
            return "N/A"
        pattern = r'^(.+?)(?=\s+Date of report:)'
        match = re.search(pattern, applicants_text, re.DOTALL)
        if match:
            return ' '.join(match.group(1).strip().split())
        return ' '.join(applicants_text.strip().split())

    @staticmethod
    def process_content_list_with_arrows(content_list: List[str]) -> str:
        """
        Process a list of content items and add arrows between consecutive
        strikethrough and underline items.
        """
        if not content_list:
            return ""
        
        html_parts = []
        i = 0
        
        while i < len(content_list):
            current_item = str(content_list[i])
            
            # Check if current item has strikethrough
            has_strikethrough = 'text-decoration:line-through' in current_item
            
            # Check if next item exists and has underline
            has_next_underline = False
            if i + 1 < len(content_list):
                next_item = str(content_list[i + 1])
                has_next_underline = 'text-decoration:underline' in next_item
            
            # Add current item
            html_parts.append(f'<div class="content-paragraph">{current_item}</div>\n')
            
            # Add arrow if current has strikethrough and next has underline
            if has_strikethrough and has_next_underline:
                html_parts.append('<div class="content-paragraph"><span class="change-arrow">→</span></div>\n')
            
            i += 1
        
        return ''.join(html_parts)

    @staticmethod
    def add_transition_arrows_inline(content: str) -> str:
        """
        Add transition arrows between strikethrough and underline spans in the same string.
        """
        if not content:
            return ""
        pattern = r'(<span style="color:red;text-decoration:line-through;">.*?</span>)\s*(<span style="color:red;text-decoration:underline;">.*?</span>)'
        
        def replace_with_arrow(match):
            strikethrough = match.group(1)
            underline = match.group(2)
            return f'{strikethrough}<span class="change-arrow">→</span>{underline}'
        
        return re.sub(pattern, replace_with_arrow, content)

    def has_changes(self, red_spans_content: Dict) -> bool:
        """Check if patent has any actual changes"""
        if not red_spans_content:
            return False
            
        sections = red_spans_content.get('sections', [])
        
        if not sections:
            return False
        
        for section in sections:
            table_content = section.get('table_content', {})
            table_tbody = table_content.get('table_tbody', [])
            
            for row in table_tbody:
                for cell in row:
                    if cell and 'color:red' in str(cell):
                        return True
            
            content_list = section.get('content', [])
            for content_item in content_list:
                if content_item and 'color:red' in str(content_item):
                    return True
        
        return False

    def extract_author_from_text(self, text: str) -> str:
        """Extract author from any text using multiple patterns"""
        if not text:
            return ""
        
        patterns = [
            r'Based on family \(INPADOC\) alert:\s*([A-Z]{1,4})\s*\\',
            r'alert:\s*([A-Z]{1,4})\s*\\',
            r'^([A-Z]{1,4})\s*\\',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                author = match.group(1)
                false_positives = {
                    'HTML', 'HEAD', 'BODY', 'META', 'HTTP', 'UTF', 'CSS', 
                    'DIV', 'TABLE', 'SPAN', 'HREF', 'SRC', 'CROP', 'PCT', 
                    'WO', 'EP', 'US', 'CN', 'CA', 'THE', 'AND', 'FOR'
                }
                if author not in false_positives:
                    return author
        
        return ""

    def create_patent_link(self, patent_number: str) -> Optional[str]:
        """Create PatBase link for patent number"""
        if not patent_number or patent_number == "N/A":
            return None
        return os.environ.get("PATENT_URL", "").format(patent_number=patent_number)

    def render_section_content(self, section: Dict) -> str:
        """Render section content with proper formatting and transition arrows"""
        section_name = section.get('header', '')
        sub_header = section.get('sub_header', '')
        table_content = section.get('table_content', {})
        content_list = section.get('content', [])
        
        html = ""
        
        # Section header
        if section_name:
            html += f'<div class="section-header">{section_name}</div>\n'
        
        # Sub-header
        if sub_header:
            html += f'<div class="sub-header">{sub_header}</div>\n'
        
        # Table content
        table_headers = table_content.get('table_headers', [])
        table_tbody = table_content.get('table_tbody', [])
        
        if table_headers or table_tbody:
            html += '<table>\n'
            
            # Headers
            if table_headers:
                html += '<thead>\n'
                for header_row in table_headers:
                    html += '<tr>'
                    for cell in header_row:
                        cell_str = str(cell) if cell else ""
                        cell_with_arrows = self.add_transition_arrows_inline(cell_str)
                        html += f'<th>{cell_with_arrows}</th>'
                    html += '</tr>\n'
                html += '</thead>\n'
            
            # Body
            if table_tbody:
                html += '<tbody>\n'
                for row in table_tbody:
                    html += '<tr>'
                    for cell in row:
                        cell_str = str(cell) if cell else ""
                        cell_with_arrows = self.add_transition_arrows_inline(cell_str)
                        html += f'<td>{cell_with_arrows}</td>'
                    html += '</tr>\n'
                html += '</tbody>\n'
            
            html += '</table>\n'
        
        # Text content - handle arrows between consecutive items
        if content_list:
            html += self.process_content_list_with_arrows(content_list)
        
        return html

    def generate_patent_section(self, patent_data: Dict, has_changes: bool = True) -> str:
        """Generate a single patent section HTML"""
        header_info = patent_data.get('header_info', {})
        red_spans_content = patent_data.get('red_spans_content', {})

        patent_number = header_info.get('publication_number', 'N/A')
        title_text = header_info.get('title', 'N/A')
        applicants_text = header_info.get('applicants', 'N/A')
        header_title = header_info.get('header_description', f'Patent {patent_number}')

        # Build links
        links_html = []
        patbase_link = self.create_patent_link(patent_number)
        if patbase_link:
            links_html.append(f'<a href="{patbase_link}" target="_blank">PatBase Family Explorer</a>')

        if header_info.get('register_url'):
            links_html.append(f'<a href="{header_info["register_url"]}" target="_blank">View Register</a>')

        # Add CSS class for patents without changes
        section_class = "patent-section" if has_changes else "patent-section no-changes"
        header_class = "header" if has_changes else "header no-changes"
        
        section_html = f"""<div class="{section_class}">
        <div class="{header_class}">
            <h2>{header_title}{' (No Changes)' if not has_changes else ''}</h2>
        </div>
        <div class="content">    
            <div class="header-info">
                <h3>Patent Information</h3>
                <p><strong>Patent Number:</strong>
                                <p><strong>Patent Number:</strong> {patent_number}</p>
                <p><strong>Title:</strong> {title_text}</p>
                <p><strong>Applicant(s):</strong> {applicants_text}</p>"""

        if header_info.get('date_of_report'):
            section_html += f'<p><strong>Date of Report:</strong> {header_info["date_of_report"]}</p>'

        if header_info.get('last_report_sent'):
            section_html += f'<p><strong>Last Report Sent:</strong> {header_info["last_report_sent"]}</p>'

        section_html += "</div>"

        if links_html:
            section_html += f'<div class="links">{"".join(links_html)}</div>'

        # Render sections or show no changes message
        if has_changes:
            sections = red_spans_content.get('sections', [])
            if sections:
                for section in sections:
                    section_content = self.render_section_content(section)
                    if section_content.strip():
                        section_html += f'<div class="change-group">{section_content}</div>'
        else:
            section_html += '<div class="no-content-message">No red span changes detected for this patent.</div>'

        section_html += "</div></div>"
        return section_html

    def generate_author_report(self, author: str, patents_data: List[Dict]) -> str:
        """Generate HTML report for a specific author"""
        patent_sections_html = []
        changes_count = 0
        no_changes_count = 0

        for patent in patents_data:
            has_changes = self.has_changes(patent.get('red_spans_content', {}))
            section_html = self.generate_patent_section(patent, has_changes)
            patent_sections_html.append(section_html)
            
            if has_changes:
                changes_count += 1
            else:
                no_changes_count += 1

        if not patent_sections_html:
            return self.html_template.format(
                author=author,
                date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                patent_count=0,
                changes_count=0,
                no_changes_count=0,
                patent_sections='<div class="no-content-message">No patents found for this author.</div>'
            )

        return self.html_template.format(
            author=author,
            date=datetime.now().strftime('%Y-%m-%d %H:%M'),
            patent_count=len(patent_sections_html),
            changes_count=changes_count,
            no_changes_count=no_changes_count,
            patent_sections=''.join(patent_sections_html)
        )

    def generate_all_reports(self, all_patents_data: List[Dict], output_dir: str = None) -> Tuple[List[str], str]:
        """
        Generate HTML reports for all authors in a temp directory.
        Includes ALL patents (with and without red span changes).
        
        Args:
            all_patents_data: List of patent data dictionaries
            output_dir: Optional output directory path. If None, uses tempfile.mkdtemp()
            
        Returns:
            Tuple[List[str], str]: (list of generated file paths, output directory path)
        """
        # Use a unique temp directory if output_dir not specified
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="patent_reports_")
        
        output_path = Path(output_dir).resolve()

        patents_by_author = defaultdict(list)
        print(f"\n{'='*60}")
        print("GROUPING PATENTS BY AUTHOR")
        print(f"{'='*60}")
        
        for i, patent in enumerate(all_patents_data):
            author = patent.get('header_info', {}).get('author_initial', '').strip()
            if not author:
                header_desc = patent.get('header_info', {}).get('header_description', '')
                author = self.extract_author_from_text(header_desc)
            
            has_red_spans = self.has_changes(patent.get('red_spans_content', {}))
            print(f"Patent {i+1}: Author='{author}', Has Changes={has_red_spans}")
            
            # Include ALL patents if author is found (regardless of changes)
            if author:
                patents_by_author[author].append(patent)

        print(f"\n{'='*60}")
        print("GROUPING SUMMARY")
        print(f"{'='*60}")
        for author, patents in patents_by_author.items():
            with_changes = sum(1 for p in patents if self.has_changes(p.get('red_spans_content', {})))
            without_changes = len(patents) - with_changes
            print(f"  Author '{author}': {len(patents)} total patents ({with_changes} with changes, {without_changes} without)")

        # Create output directory
        print(f"\nCreating output directory: {output_path}")
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Directory created/verified: {output_path}")
        except Exception as e:
            print(f"✗ Error creating directory: {e}")
            return [], str(output_path)

        generated_files = []
        
        if not patents_by_author:
            print("\n⚠️  WARNING: No authors found in the data!")
            return generated_files, str(output_path)

        print(f"\n{'='*60}")
        print("GENERATING REPORTS")
        print(f"{'='*60}")
        
        for author, patents in patents_by_author.items():
            with_changes = sum(1 for p in patents if self.has_changes(p.get('red_spans_content', {})))
            without_changes = len(patents) - with_changes
            print(f"\nGenerating report for author: {author} ({len(patents)} total patents: {with_changes} with changes, {without_changes} without)")
            try:
                html_content = self.generate_author_report(author, patents)
                
                # Sanitize filename
                safe_author = re.sub(r'[<>:"/\\|?*]', '_', author)
                filename = f"patent_report_{safe_author}.html"
                filepath = output_path / filename
                
                print(f"  Writing to: {filepath}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                generated_files.append(str(filepath))
                print(f"  ✓ Report saved: {filepath}")
                
            except Exception as e:
                print(f"  ✗ Error generating report for author {author}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: Generated {len(generated_files)} report(s)")
        print(f"Output directory: {output_path}")
        print(f"{'='*60}")
        
        return generated_files, str(output_path)


def process_patent_data_from_json(json_data: List[Dict]) -> List[Dict]:
    """
    Convert the raw JSON data format to the expected format for the generator
    
    Args:
        json_data: List of raw patent data dictionaries or objects
        
    Returns:
        List[Dict]: Processed patent data in the expected format
    """
    processed_data = []
    
    print(f"\n{'='*60}")
    print("PROCESSING PATENT DATA")
    print(f"{'='*60}")
    
    generator = PatentHTMLReportGenerator()
    
    for idx, item in enumerate(json_data):
        print(f"\nProcessing patent {idx+1}/{len(json_data)}...")
        
        # Handle both dict and object types
        if isinstance(item, dict):
            header = item.get('header', {})
            content_obj = item.get('content', None)
        else:
            try:
                header = item.header if hasattr(item, 'header') else {}
                content_obj = item.content if hasattr(item, 'content') else None
            except:
                print(f"  ⚠️  Warning: Could not extract header/content from item: {type(item)}")
                continue
        
        # Ensure header is a dictionary
        if not isinstance(header, dict):
            if hasattr(header, '__dict__'):
                header = header.__dict__
            elif hasattr(header, 'to_dict'):
                header = header.to_dict()
            else:
                print(f"  ⚠️  Warning: Could not convert header to dict: {type(header)}")
                header = {}
        
        # Extract red_span_parsers from the content object
        red_span_parsers = []
        if content_obj:
            # Check if it's a RedSpanScrapper object
            if hasattr(content_obj, 'red_span_parsers'):
                red_span_parsers = content_obj.red_span_parsers
            # Or if it's already a dict
            elif isinstance(content_obj, dict):
                red_span_parsers = content_obj.get('red_span_parsers', [])
        
        print(f"  Found {len(red_span_parsers)} sections with potential changes")
        
        # Convert to sections format
        sections = []
        for parser in red_span_parsers:
            # Handle both object and dict types for parser
            if hasattr(parser, '__dict__'):
                section_data = {
                    'header': getattr(parser, 'header', ''),
                    'sub_header': getattr(parser, 'sub_header', ''),
                    'table_content': getattr(parser, 'table_content', {}),
                    'content': getattr(parser, 'content', [])
                }
            elif isinstance(parser, dict):
                section_data = {
                    'header': parser.get('header', ''),
                    'sub_header': parser.get('sub_header', ''),
                    'table_content': parser.get('table_content', {}),
                    'content': parser.get('content', [])
                }
            else:
                continue
            
            # Convert table_content if it's an object
            if hasattr(section_data['table_content'], '__dict__'):
                section_data['table_content'] = {
                    'table_headers': getattr(section_data['table_content'], 'table_headers', []),
                    'table_tbody': getattr(section_data['table_content'], 'table_tbody', [])
                }
            
            sections.append(section_data)
        
        # Extract and clean title and applicants
        raw_title = header.get('Title', '')
        raw_applicants = header.get('Applicant(s)', '')
        
        clean_title = generator.extract_clean_title(raw_title)
        clean_applicants = generator.extract_clean_applicants(raw_applicants)
        
        print(f"  ✓ Patent Number: {header.get('Publication Number', 'N/A')}")
        print(f"  ✓ Author: {header.get('Author Name', '')}")
        
        # Check if there are actual changes
        has_red_spans = False
        for section in sections:
            # Check table content
            table_tbody = section.get('table_content', {}).get('table_tbody', [])
            for row in table_tbody:
                for cell in row:
                    if cell and 'color:red' in str(cell):
                        has_red_spans = True
                        break
                if has_red_spans:
                    break
            
            # Check content list
            if not has_red_spans:
                for content_item in section.get('content', []):
                    if content_item and 'color:red' in str(content_item):
                        has_red_spans = True
                        break
            
            if has_red_spans:
                break
        
        print(f"  ✓ Has red span changes: {has_red_spans}")
        
        # Build processed patent data (include ALL patents, not just those with changes)
        processed_patent = {
            'header_info': {
                'publication_number': header.get('Publication Number', 'N/A'),
                'header_description': header.get('Header Title', ''),
                'author_initial': header.get('Author Name', ''),
                'title': clean_title,
                'applicants': clean_applicants,
                'date_of_report': header.get('Date of report', ''),
                'last_report_sent': header.get('Last report sent', ''),
                'register_url': header.get('Register', '')
            },
            'red_spans_content': {
                'sections': sections
            }
        }
        
        processed_data.append(processed_patent)
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully processed {len(processed_data)} patents")
    print(f"{'='*60}")
    
    return processed_data


def main(results) -> Optional[Tuple[List[str], str]]:
    """
    Main function to generate patent reports
    
    Args:
        results: Raw patent data (list of dicts or objects)
        
    Returns:
        Tuple[List[str], str]: (list of generated file paths, temp directory path)
        Returns None if an error occurs
    """
    try:
        print("="*60)
        print("PATENT REPORT GENERATOR - BLACK & WHITE WITH ARROWS")
        print("="*60)
        
        # Validate input
        if not results:
            print("\n❌ ERROR: No data provided to process!")
            return None
        
        # Process the data
        processed_data = process_patent_data_from_json(results)
        
        if not processed_data:
            print("\n❌ ERROR: No data was processed!")
            return None
        
        # Generate reports in a temp directory
        generator = PatentHTMLReportGenerator()
        generated_files, temp_dir = generator.generate_all_reports(processed_data)
        
        if generated_files:
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS: Generated {len(generated_files)} report(s)")
            print(f"{'='*60}")
            for filepath in generated_files:
                print(f"   📄 {filepath}")
            print(f"\n💡 Open the HTML files in your browser to view the reports")
            print(f"📁 Reports saved in temp directory: {temp_dir}")
            
            return generated_files, temp_dir
        else:
            print(f"\n{'='*60}")
            print("⚠️  WARNING: No reports were generated")
            print("This could mean:")
            print("  - No authors were found in the data")
            print(f"{'='*60}")
            
            return [], temp_dir if 'temp_dir' in locals() else tempfile.gettempdir()
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR OCCURRED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        
        return None