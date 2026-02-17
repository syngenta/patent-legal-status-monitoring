from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import PydanticOutputParser
from .prompt_config import model

class TableParser(BaseModel): 
    table_headers: list[list[str]] = Field(description="Column or Attributes name of the table")
    table_tbody: list[list[str]] = Field(description="list of the row/rows contain span tag of either red strikeout or underline, while returning the rows, the red spans tags(either strikeout or underline) should be preserved.")


class RedSpanParser(BaseModel):
    header: str = Field(description="Header of the content where red strikeout or red underline is present")
    sub_header: str = Field(description="Sub header of the content where red strikeout or red underline is present")
    table_content: TableParser = Field(description="Content related table tags")
    content: list[str] = Field(description="Content (extract from p, div, pre or any other similar tags) containing span tag either red strikeout or red underline. Return complete sentences or thoughts that include the span tag (either red-strikeout or red-underline). Exclude tables or table tags, include only sentence content and the red spans tags(either strikeout or underline) should be preserved.")


class RedSpanScrapper(BaseModel):
    red_span_parsers: list[RedSpanParser] = Field(description="List of all content sections containing red span elements from the HTML")


output_parser = PydanticOutputParser(pydantic_object=RedSpanScrapper)

prompt_template = """
You are an expert making web scrapping and analyzing HTML raw code.
If there is no explicit information don't make any assumption.
Extract all objects that matched the instructions from the following html
{html_text}
Provide them in a list.
Please following the instructions
    - {format_instructions}
    - While return each section, preserve order. 
    - Remove unnecessary space, tabs, and newlines.  
    - Omit any introductory statements or XML tags.
"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["html_text"],
    partial_variables={"format_instructions": output_parser.get_format_instructions}
)

chain = prompt | model | output_parser