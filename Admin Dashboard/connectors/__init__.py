"""
connectors — Data Source Connectors Package

Provides various data sources for dataset selection:
  - wikipedia_connector.py: Wikipedia article fetcher
  - news_connector.py: Mock news data provider
  - file_uploader.py: File upload handler (CSV, TXT, JSON)
"""

from .wikipedia_connector import (
    fetch_wikipedia_article,
    search_wikipedia,
    render_wikipedia_connector,
    get_wikipedia_metadata,
)

from .news_connector import (
    get_available_categories,
    fetch_news_articles,
    format_news_content,
    render_news_connector,
    get_random_news_article,
    search_news,
)

from .arxiv_connector import (
    fetch_arxiv_papers,
    render_arxiv_connector,
)

from .file_uploader import (
    validate_file,
    read_text_file,
    read_csv_file,
    read_json_file,
    process_uploaded_file,
    render_file_uploader,
    export_dataset,
    save_dataset_file,
)

__all__ = [
    # Wikipedia
    "fetch_wikipedia_article",
    "search_wikipedia",
    "render_wikipedia_connector",
    "get_wikipedia_metadata",
    
    # News
    "get_available_categories",
    "fetch_news_articles",
    "format_news_content",
    "render_news_connector",
    "get_random_news_article",
    "search_news",

    # ArXiv
    "fetch_arxiv_papers",
    "render_arxiv_connector",
    
    # File Uploader
    "validate_file",
    "read_text_file",
    "read_csv_file",
    "read_json_file",
    "process_uploaded_file",
    "render_file_uploader",
    "export_dataset",
    "save_dataset_file",
]
