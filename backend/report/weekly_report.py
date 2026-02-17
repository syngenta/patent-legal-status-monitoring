import re 
from bs4 import BeautifulSoup
from typing import List, Dict
import os
class HTMLParser:
    def __init__(self, file_name: str):
        self.file_name: str = file_name
        self.html_file: BeautifulSoup = self.load_file()
        
    @staticmethod
    def split_individual_author_sections(html_file: BeautifulSoup) -> List[BeautifulSoup]:
        try:
            individual_author_section = list()
            # Corrected to use self.html_file
            for i in html_file.find_all("p", style="page-break-after: always"):
                individual_author_section.append(i)
            return individual_author_section
        except Exception as e:
            raise Exception
    def load_file(self) -> BeautifulSoup:
     
        try:
            with open(self.file_name, "r") as f:
                html_file = f.read()
            soup = BeautifulSoup(html_file, "html.parser")
            return soup
        except Exception as e:
            raise FileNotFoundError

    def split_file_as_individual_author_sections(self) -> List[BeautifulSoup]:
       
        try:
            individual_author_section = list()
            # Corrected to use self.html_file
            for i in self.html_file.find_all("p", style="page-break-after: always"):
                individual_author_section.append(i)
            return individual_author_section
        except Exception as e:
            raise Exception
    
   
    
class HeaderExtraction:
    # Define the valid author abbreviations as a class constant
    VALID_AUTHORS = os.getenv("VALID_AUTHOR", "").split(", ")
    def __init__(self, individual_author_section: BeautifulSoup):
        self.individual_author_section: BeautifulSoup = individual_author_section
        self.headers: List[Dict] = self._parse_header_information() 

    @classmethod
    def extract_author_initials_from_heading(cls, header_text: str) -> List[str]:
        """
        Extracts all author initials from a heading string using the predefined author list.
        
        Args:
            header_text: The heading text to parse
            
        Returns:
            List of author initials as strings
        """
        authors = []
        
        # Split by backslash to get segments
        segments = header_text.split('\\')
        
        if segments:
            # First segment typically contains authors
            first_segment = segments[0].strip()
            
            # Extract all potential uppercase sequences
            # Look for word boundaries to avoid partial matches
            words = first_segment.split()
            
            for word in words:
                # Clean the word of any special characters
                cleaned_word = re.sub(r'[^A-Z]', '', word.upper())
                
                # Check if this cleaned word is in our valid authors list
                if cleaned_word in cls.VALID_AUTHORS:
                    authors.append(cleaned_word)
            
            # Alternative approach: use regex to find all potential matches
            # and then filter by valid authors
            if not authors:
                potential_matches = re.findall(r'\b([A-Z]{2,})\b', first_segment)
                for match in potential_matches:
                    if match in cls.VALID_AUTHORS:
                        authors.append(match)
        
        return authors if authors else ['']

    @staticmethod
    def extract_patent_ids_from_heading(text: str) -> List[str]:
        """
        Extracts patent IDs from a heading string.
        
        Args:
            text: The heading text to parse
            
        Returns:
            List of patent IDs found in the text
        """
        ids = re.findall(r'\(([a-zA-Z]{2,}\d+)\)', text)
        ids = [i.replace('IF', '').replace('if', '') for i in ids] if ids else []
        return ids
    
    @staticmethod
    def extract_publication_number(text: str) -> str:
        """Extract publication number from the text"""
        pattern = r'Publication number:\s*([A-Z0-9]+)'
        match = re.search(pattern, text)
        return match.group(1) if match else ""

    @staticmethod
    def extract_title(text: str) -> str:
        """Extract title from the text"""
        # Match Title: followed by content, stopping at Applicant(s): (with or without <b> tags)
        pattern = r'Title:\s*(?:\r?\n)?\s*(.+?)(?=\s*(?:<b>)?Applicant\(s\):)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Clean up: remove extra whitespace and newlines
            return ' '.join(match.group(1).strip().split())
        return ""

    @staticmethod
    def extract_applicants(text: str) -> str:
        """Extracts Applicant(s) from the text."""
        # Match Applicant(s): followed by content, stopping at Date of report: (with or without <b> tags)
        pattern = r'Applicant\(s\):\s*(?:\r?\n)?\s*(.+?)(?=\s*(?:<b>)?Date of report:)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Clean up: remove extra whitespace and newlines
            return ' '.join(match.group(1).strip().split())
        return ""

    @staticmethod
    def extract_dates(text: str) -> Dict[str, str]:
        """Extract both Date of report and Last report sent"""
        date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'
        
        date_of_report = ""
        last_report_sent = ""

        # Extract Date of report
        report_date_pattern = r'Date of report:\s*' + date_pattern
        report_match = re.search(report_date_pattern, text)
        if report_match:
            date_of_report = report_match.group(1)
        
        # Extract Last report sent
        last_report_pattern = r'Last report sent:\s*(?:' + date_pattern + r'|Not previously checked)'
        last_match = re.search(last_report_pattern, text)
        if last_match:
            # Check if it matched a date or "Not previously checked"
            if last_match.group(1):
                last_report_sent = last_match.group(1)
            else:
                last_report_sent = "Not previously checked"
        
        return {
            'date_of_report': date_of_report,
            'last_report_sent': last_report_sent
        }

    @staticmethod
    def extract_register_link(soup_section: BeautifulSoup) -> str:
        """Extracts the register link from the BeautifulSoup object."""
        font_tag = soup_section.find("center")
        if font_tag:
            font_tag_inner = font_tag.find("font", {'color': "navy", 'face': "verdana, arial", "size": 2})
            if font_tag_inner:
                link_tag = font_tag_inner.find("a")
                if link_tag:
                    return link_tag.get("href", "")
        return ""

    @staticmethod
    def extract_patent_tracker_id(title_text: str) -> str:
        """Extracts the patent ID from a 'PatentTracker - ID' string."""
        pattern = r'PatentTracker - ([A-Z0-9]+)'
        match = re.search(pattern, title_text)
        return match.group(1) if match else title_text

    def _parse_header_information(self) -> List[Dict]:
        """
        Parses the HTML section to extract header details.
        Returns a list of dictionaries, one for each author found.
        """
        header_title_tag = self.individual_author_section.find("h3", align="center")
        header_title = header_title_tag.text.strip() if header_title_tag else ""

        # Extract all authors using the valid author list
        author_names = self.extract_author_initials_from_heading(header_title)
        patent_number_in_header = self.extract_patent_ids_from_heading(header_title)

        patent_tracker_title_tag = self.individual_author_section.find('title')
        raw_patent_tracker_text = patent_tracker_title_tag.text.strip() if patent_tracker_title_tag else ""
        patent_tracker = self.extract_patent_tracker_id(raw_patent_tracker_text)

        other_details_font_tag = self.individual_author_section.find("center")
        other_details_text = ""
        if other_details_font_tag:
            font_tag_inner = other_details_font_tag.find("font", {'color': "navy", 'face': "verdana, arial", "size": 2})
            if font_tag_inner:
                other_details_text = font_tag_inner.get_text(separator='\n').strip()

        publication_number = self.extract_publication_number(other_details_text)
        title = self.extract_title(other_details_text)
        applicants = self.extract_applicants(other_details_text)
        dates = self.extract_dates(other_details_text)
        register_link = self.extract_register_link(self.individual_author_section)

        # Create a header dictionary for each author
        headers = []
        for author_name in author_names:
            header_dict = {
                "Header Title": header_title,
                "Author Name": author_name,
                "Patent Tracker": patent_tracker,
                "Publication Number": publication_number,
                "Title": title,
                "Applicant(s)": applicants,
                "Date of report": dates['date_of_report'],
                "Last report sent": dates['last_report_sent'],
                "Register": register_link,
                "Patent Number in Header": patent_number_in_header
            }
            headers.append(header_dict)
        
        # If no authors found, return a single header with empty author name
        if not headers:
            headers.append({
                "Header Title": header_title,
                "Author Name": "",
                "Patent Tracker": patent_tracker,
                "Publication Number": publication_number,
                "Title": title,
                "Applicant(s)": applicants,
                "Date of report": dates['date_of_report'],
                "Last report sent": dates['last_report_sent'],
                "Register": register_link,
                "Patent Number in Header": patent_number_in_header
            })
        
        return headers