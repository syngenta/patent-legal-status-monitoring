from bs4 import BeautifulSoup
def reduce_html_content(soup: BeautifulSoup)->BeautifulSoup:
    return BeautifulSoup(str(soup)[str(soup).find("</center>"):], "html.parser")
def is_red_span_tag_present(soup:BeautifulSoup)->bool: 
   return True if soup.find("span", style="color:red;text-decoration:line-through;") or soup.find("span", style="color:red;text-decoration:underline;") else False
def extract_all_spans(soup) -> str:
    """
    Extract all span tags with their text from HTML.
    
    Args:
        html_text: Raw HTML content as string
        
    Returns:
        String with all span tags separated by newlines
    """
    spans = soup.find_all('span')
    
    return spans
