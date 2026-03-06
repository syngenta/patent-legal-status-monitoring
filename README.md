# Patent Legal Status Monitoring

Application is detection system featuring automated HTML report ingestion, author-based document segmentation, difference highlighting, and structured data export. Implements configurable thread-pool batch processing for high-throughput patent monitoring workflows.

---

## 📋 About

It ingests patent data from external sources and provides actionable insights into patent changes tracked by individual authors.

### Key Features

- **Automated Patent Report Processing**: Ingests consolidated HTML reports from external patent sources
- **Author-based Report Splitting**: Breaks down consolidated reports into individual author sections
- **Change Highlighting**: Identifies and highlights modifications in patent data
- **Batch Processing**: Optimized processing with configurable worker threads and retry logic
- **Structured Output**: Generates organized reports with detailed change tracking

---

## 📁 Project Structure

```
open-source/
├── backend/
│   ├── process/              # Core processing logic
│   │   └── weekly_report_core.py
│   ├── prompt/               # Prompt templates and configurations
│   │   ├── models.yml
│   │   ├── prompt_config.py
│   │   └── prompt.py
│   ├── report/               # Report generation
│   │   ├── create_report.py
│   │   ├── templates.py
│   │   └── weekly_report.py
│   ├── src/                  # Entry point
│   │   └── index.py
│   └── utils/                # Utility functions
│       └── utils.py
├── frontend/
│   └── app.py               # Frontend interface
├── main.py                  # Main entry point
├── pyproject.toml           # Project configuration
├── .env                     # Environment variables
├── .python-version          # Python version specification
└── README.md                # This file
```

---

## 🔧 Installation & Setup

### 1.1 Prerequisites

- **Python 3.13+** (as specified in `pyproject.toml`)
- **UV** - A fast Python package manager (recommended)
  - Install UV: `pip install uv` or follow [UV documentation](https://docs.astral.sh/uv/)
- Git for cloning the repository

### 1.2 Install Dependencies Using UV

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone <repository-url>
cd open-source

# Install dependencies using UV (recommended)
uv sync

# OR install with pip
pip install -e .
```

**Note**: The project uses `uv.lock` for reproducible dependency installation. See [UV Lock File](#15-uv-lock-file) section for details.

### 1.3 Environment Configuration

Create a `.env` file in the project root with required configurations:

```env
# LLM API Keys (choose at least one)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Application Settings
PATENT_SOURCE_URL=https://example.com/patents
VALID_AUTHOR=author1,author2,author3
```

### 1.4 Project Dependencies

Core dependencies (from `pyproject.toml`):

| Package | Version | Purpose |
|---------|---------|---------|
| `beautifulsoup4` | >=4.14.3 | HTML parsing and processing |
| `langchain` | >=1.2.10 | LLM framework and orchestration |
| `langchain-openai` | >=0.2.0 | OpenAI API integration |
| `langchain-anthropic` | >=0.1.0 | Anthropic Claude integration |
| `langchain-google-genai` | >=1.0.0 | Google Gemini integration |
| `langchain-aws` | >=1.2.4 | AWS Bedrock integration |
| `python-dotenv` | >=1.2.1 | Environment variable management |
| `pyyaml` | >=6.0.0 | YAML configuration parsing |
| `streamlit` | >=1.28.0 | Web UI framework |

**See `pyproject.toml` and `uv.lock` for complete dependency tree and pinned versions.**

### 1.5 UV Lock File

The `uv.lock` file maintains exact versions of all dependencies for reproducible installations across environments:

```bash
# Install with exact versions from uv.lock
uv sync

# Update dependencies (generates new lock file)
uv lock
```

This ensures consistent builds and prevents version conflicts across development, testing, and production environments.

---

## 📖 Usage Guide

### 2.1 Quick Start

Run the main application with a patent report file:

```bash
streamlit run frontend/app.py
```

Or use the backend processing directly:

```python
from backend.src import index

# Process a patent report
file, dir = index.main(r"path/to/patent_report.html")
print(f"Report saved to: {file}")
print(f"Output directory: {dir}")
```

---

## 🔄 Workflow

### Step 1: Patent Report Ingestion

The application accepts consolidated HTML (.html or .htm) reports from external patent sources containing patent information and metadata.

```bash
# Input file format:
# 20251102_information_patent_example.htm
```

### Step 2: HTML Parsing & Section Splitting

The `weekly_report.HTMLParser` class breaks down the consolidated report into individual author sections:

```python
from backend.report import weekly_report

parser = weekly_report.HTMLParser(file_path)
author_sections = parser.split_file_as_individual_author_sections()
```

### Step 3: Optimized HTML Processing

The core processing engine analyzes patent data with optimized threading:

```python
from backend.process import weekly_report_core

# Process with 4 worker threads and up to 8 retries
result = weekly_report_core.html_parser_optimized(
    author_sections, 
    max_workers=4, 
    max_retries=8
)
```

**Processing Configuration:**
- `max_workers`: Number of concurrent worker threads (default: 4)
- `max_retries`: Maximum retry attempts for failed processing (default: 8)

### Step 4: Report Generation

Generate formatted reports with change highlighting:

```python
from backend.report import create_report

file, dir = create_report.main(result)
```

### Step 5: Output & Delivery

Reports are generated in the configured output directory with the following structure:

```
output/
├── author_1_report.html
├── author_2_report.html
├── author_3_report.html
└── summary_report.html
```

---

## ⚙️ Configuration

### 3.1 Prompt Configuration

Configure AI/LLM prompts for patent analysis in `backend/prompt/prompt_config.py`:

```yaml
# backend/prompt/models.yml
model:
  type: "openai"
  version: "gpt-3.5-turbo"
  temperature: 0.7

prompts:
  patent_analysis: "Analyze the following patent..."
  change_detection: "Identify changes in..."
```

### 3.2 Processing Parameters

Modify processing behavior in `backend/process/weekly_report_core.py`:

```python
# Adjustable parameters
MAX_WORKERS = 4          # Parallel processing threads
MAX_RETRIES = 8          # Retry attempts for failures
TIMEOUT_SECONDS = 300    # Processing timeout
```

### 3.3 Report Templates

Customize report output format in `backend/report/templates.py`:

```python
# Template configuration for HTML report generation
# Modify styling, layout, and content organization
```

---

## 📊 Advanced Usage

### 4.1 Batch Processing

Process multiple patent reports:

```python
from backend.src import index
import os

patent_files = [f for f in os.listdir("patents/") if f.endswith(".html")]

for patent_file in patent_files:
    file, dir = index.main(os.path.join("patents/", patent_file))
    print(f"Processed: {file}")
```

### 4.2 Error Handling & Retries

The system automatically retries failed processing tasks:

```python
result = weekly_report_core.html_parser_optimized(
    author_sections,
    max_workers=4,
    max_retries=8  # Automatically retry up to 8 times
)
```

### 4.3 Custom Output Paths

Specify custom output directory:

```python
from backend.report import create_report

file, dir = create_report.main(result, output_dir="/custom/path")
```

---

## 🖥️ Frontend Usage

The frontend application provides a user-friendly interface:

```bash
streamlit run frontend/app.py
```

This launches an interactive interface for:
- Uploading patent reports
- Monitoring processing progress
- Viewing generated reports
- Downloading results

---

## 📋 System Requirements

- **OS**: Windows, macOS, Linux
- **Python**: 3.13+
- **Memory**: Minimum 2GB RAM (4GB+ recommended for large batches)
- **Storage**: Sufficient space for input HTML files and generated reports
- **Dependencies**: See `pyproject.toml` for complete list

---
## 👥 Credits

### Created By

- **Paresh Pandya**

### Special Thanks

- **Nicolas Lalyre**
- **Patrice Guerne**
- **Jay Sangaraju**
- **Shital Deshpande**
- **Evangelos Ninnis**
- **Moupiya Chatterjee**

---
## License

This project is provided under the MIT License. See `LICENSE` file for details.

---
## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
## 📫 Contact

For issues, questions, or collaboration inquiries, please contact:

| Name             | Email                        |
|------------------|------------------------------|
| Paresh Pandya    | pareshpandya026@gmail.com    |
| Shital Deshpande | shitaldeshpande21@gmail.com  |

---
**Last Updated**: February 2026  
**Version**: 1.0.0

