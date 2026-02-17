HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Patent Changes Report - {author}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            background: #ffffff;
            padding: 20px;
            line-height: 1.6;
            color: #000000;
        }}
        
        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .report-header {{
            border-bottom: 2px solid #000000;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        
        .report-header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        
        .report-header .meta {{
            font-size: 14px;
            color: #333333;
        }}
        
        .patent-section {{
            border: 1px solid #000000;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}
        
        .patent-section.no-changes {{
            border-color: #cccccc;
            background: #f9f9f9;
        }}
        
        .header {{
            background: #f0f0f0;
            padding: 15px;
            border-bottom: 1px solid #000000;
            cursor: pointer;
            user-select: none;
        }}
        
        .header.no-changes {{
            background: #fafafa;
        }}
        
        .header h2 {{
            font-size: 16px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .arrow {{
            font-size: 12px;
            transition: transform 0.3s;
            display: inline-block;
        }}
        
        .header.active .arrow {{
            transform: rotate(90deg);
        }}
        
        .content {{
            padding: 20px;
        }}
        
        .header-info {{
            background: #fafafa;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #cccccc;
        }}
        
        .header-info h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: bold;
            border-bottom: 1px solid #000000;
            padding-bottom: 5px;
        }}
        
        .header-info p {{
            margin: 5px 0;
            font-size: 13px;
        }}
        
        .header-info strong {{
            font-weight: bold;
            display: inline-block;
            min-width: 180px;
        }}
        
        .links {{
            margin: 15px 0;
            padding: 10px;
            background: #f5f5f5;
            border: 1px solid #cccccc;
        }}
        
        .links a {{
            display: inline-block;
            color: #000000;
            text-decoration: underline;
            margin-right: 20px;
            font-size: 13px;
        }}
        
        .links a:hover {{
            text-decoration: none;
        }}
        
        .section-header {{
            font-weight: bold;
            margin: 20px 0 10px 0;
            font-size: 14px;
            border-bottom: 1px solid #000000;
            padding-bottom: 5px;
        }}
        
        .sub-header {{
            font-weight: bold;
            margin: 15px 0 8px 0;
            font-size: 13px;
        }}
        
        .change-group {{
            margin: 15px 0;
            padding: 15px;
            border: 1px solid #cccccc;
            background: #fafafa;
        }}
        
        .content-paragraph {{
            margin: 8px 0;
            padding: 5px 0;
            line-height: 1.8;
            font-size: 13px;
        }}
        
        .change-arrow {{
            display: inline-block;
            margin: 0 8px;
            font-weight: bold;
            color: #000000;
            font-size: 16px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            border: 1px solid #000000;
        }}
        
        table th, table td {{
            border: 1px solid #000000;
            padding: 8px;
            text-align: left;
            vertical-align: top;
            font-size: 13px;
        }}
        
        table th {{
            background: #e0e0e0;
            font-weight: bold;
        }}
        
        table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .no-content-message {{
            text-align: center;
            padding: 20px;
            color: #666666;
            font-style: italic;
            background: #f5f5f5;
            border: 1px dashed #cccccc;
            margin: 10px 0;
        }}
        
        @media print {{
            .patent-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="report-header">
            <h1>Patent Changes Report - {author}</h1>
            <div class="meta">Generated on {date} | {patent_count} total patents ({changes_count} with changes, {no_changes_count} without changes)</div>
        </div>
        {patent_sections}
    </div>
</body>
</html>"""
