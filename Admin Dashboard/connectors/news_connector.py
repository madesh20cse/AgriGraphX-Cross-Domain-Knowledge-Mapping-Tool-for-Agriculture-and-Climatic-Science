"""
news_connector.py — News Data Connector (Mock)

Provides mock news data for knowledge graph building.
In production, this would integrate with news APIs like NewsAPI, Newsdata.io, etc.
Used by: Dataset selection UI as a news data source.
"""

import streamlit as st
import os
from datetime import datetime
from typing import Tuple, Optional, List
import json
from .file_uploader import save_dataset_file


# Mock news dataset
MOCK_NEWS_DATA = {
    "agriculture": [
        {
            "title": "Climate Change Impact on Global Crop Yields",
            "content": "Climate change continues to affect agricultural productivity worldwide. Rising temperatures and irregular precipitation patterns are challenging farmers in maintaining consistent crop yields. Research shows a 5-10% decrease in major crops over the past decade due to climatic factors.",
            "source": "Agricultural Today",
            "date": "2024-03-15"
        },
        {
            "title": "Precision Farming Technologies Revolutionize Agriculture",
            "content": "Modern precision farming techniques using IoT sensors and AI are transforming agricultural practices. Farmers can now optimize irrigation, fertilizer application, and pest management with unprecedented accuracy. Studies show a 20-30% increase in crop efficiency with these technologies.",
            "source": "Tech in Agriculture",
            "date": "2024-03-10"
        },
        {
            "title": "Sustainable Farming Practices Gain Momentum",
            "content": "Organic and sustainable farming methods are becoming increasingly popular among farmers. Crop rotation, composting, and integrated pest management reduce environmental impact while maintaining soil health. Global organic farming market is expected to grow by 15% annually.",
            "source": "Green Futures",
            "date": "2024-03-08"
        },
    ],
    "climate": [
        {
            "title": "Global Temperature Records Break Again in 2024",
            "content": "2024 marks another year of record-breaking global temperatures. Climate scientists warn of accelerating climate change impacts on weather patterns, sea levels, and ecosystems. International efforts to reduce carbon emissions remain critical.",
            "source": "Climate Science Today",
            "date": "2024-03-14"
        },
        {
            "title": "Renewable Energy Adoption Accelerates Worldwide",
            "content": "Renewable energy sources now account for 30% of global electricity generation. Solar and wind power technologies continue to improve while costs decrease. Countries worldwide are committing to net-zero emissions targets.",
            "source": "Energy Weekly",
            "date": "2024-03-12"
        },
    ],
    "ai_technology": [
        {
            "title": "Large Language Models Transform NLP Applications",
            "content": "Advanced language models are revolutionizing natural language processing. Applications range from content generation to complex reasoning tasks. Ethical considerations and fine-tuning approaches remain active areas of research.",
            "source": "AI Research Hub",
            "date": "2024-03-16"
        },
        {
            "title": "Machine Learning Models Show Breakthrough Results",
            "content": "Recent machine learning innovations achieve state-of-the-art performance across multiple domains. Computer vision, speech recognition, and predictive analytics benefit from advanced model architectures. Practical deployment challenges require ongoing attention.",
            "source": "ML Weekly",
            "date": "2024-03-13"
        },
    ]
}


def get_available_categories() -> List[str]:
    """Get available news categories."""
    return list(MOCK_NEWS_DATA.keys())


def fetch_news_articles(category: str) -> Tuple[bool, List[dict]]:
    """
    Fetch mock news articles for a category.
    
    Args:
        category: News category (agriculture, climate, ai_technology, etc.)
        
    Returns:
        Tuple of (success: bool, articles: list of dict)
    """
    category = category.lower().replace(" ", "_")
    
    if category in MOCK_NEWS_DATA:
        return True, MOCK_NEWS_DATA[category]
    else:
        return False, []


def format_news_content(articles: List[dict]) -> str:
    """
    Format multiple news articles into unified text format.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Formatted text content combining all articles
    """
    content = ""
    
    for i, article in enumerate(articles, 1):
        content += f"{'='*80}\n"
        content += f"Article {i}: {article['title']}\n"
        content += f"Source: {article['source']} | Date: {article['date']}\n"
        content += f"{'─'*80}\n"
        content += f"{article['content']}\n\n"
    
    return content


def render_news_connector():
    """
    Render Streamlit UI for news connector.
    
    Returns:
        Tuple of (success: bool, content: str or None)
    """
    st.markdown("### 📰 News Data Source")
    st.markdown("🔍 Browse curated news articles on agriculture, climate, and AI technologies.")
    
    categories = get_available_categories()
    selected_category = st.selectbox(
        "📂 Select News Category",
        categories,
        format_func=lambda x: x.replace("_", " ").title(),
        help="Choose a news category to view articles"
    )
    
    if selected_category:
        success, articles = fetch_news_articles(selected_category)
        
        if success and articles:
            st.markdown(f"**✅ Found {len(articles)} articles in '{selected_category.replace('_', ' ').title()}' category**")
            
            # Display articles
            for i, article in enumerate(articles):
                with st.expander(f"📄 {article['title']}", expanded=(i==0)):
                    st.markdown(f"📰 **Source:** {article['source']}")
                    st.markdown(f"📅 **Date:** {article['date']}")
                    st.markdown(f"📝 **Content:**\n{article['content']}")
            
            # Option to use all articles
            if st.button("📥 Use All Articles from This Category", type="primary"):
                content = format_news_content(articles)
                
                # Save dataset file
                dataset_name = f"News_{selected_category.replace('_', ' ').title()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                success_save, file_path, error = save_dataset_file(
                    content, 
                    dataset_name, 
                    "News",
                    metadata={"category": selected_category, "articles_count": len(articles)}
                )
                
                st.success("✅ Articles selected successfully!")
                
                # Show file link if saved successfully
                if success_save:
                    st.info(f"✅ Dataset saved to: `data/datasets/{os.path.basename(file_path)}`")
                    with st.expander("📁 View File Information"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**File:** {os.path.basename(file_path)}")
                            st.write(f"**Size:** {len(content.encode('utf-8')) / 1024:.2f} KB")
                        with col2:
                            st.write(f"**Metadata:** {os.path.basename(file_path.replace('.txt', '_meta.json'))}")
                else:
                    st.warning(f"⚠️ Could not save file: {error}")
                
                return True, content
        else:
            st.warning("No articles found for this category.")
    
    return False, None


def get_random_news_article() -> Optional[dict]:
    """
    Get a random news article from the mock dataset.
    
    Returns:
        Random article dictionary or None
    """
    import random
    
    all_articles = []
    for articles in MOCK_NEWS_DATA.values():
        all_articles.extend(articles)
    
    if all_articles:
        return random.choice(all_articles)
    
    return None


def search_news(query: str) -> List[dict]:
    """
    Search for news articles by keyword.
    
    Args:
        query: Search keyword
        
    Returns:
        List of matching articles
    """
    query = query.lower()
    results = []
    
    for articles in MOCK_NEWS_DATA.values():
        for article in articles:
            if (query in article['title'].lower() or 
                query in article['content'].lower()):
                results.append(article)
    
    return results
