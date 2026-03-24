#!/usr/bin/env python3
"""
Test script for Wikipedia Domain Connector
Tests the new domain-based article fetching functionality
"""

from connectors.wikipedia_connector import (
    DOMAIN_KEYWORDS, 
    fetch_wikipedia_article, 
    combine_articles_content,
    fetch_domain_articles
)

def test_domains_available():
    """Test that all domains are available"""
    print("\n📚 Available Domains:")
    print("="*60)
    
    for domain in DOMAIN_KEYWORDS.keys():
        keywords = DOMAIN_KEYWORDS[domain]
        print(f"\n  ✓ {domain.upper().replace('_', ' ')}")
        print(f"    Keywords: {len(keywords)}")
        print(f"    Sample: {', '.join(keywords[:5])}")
    
    print("\n✅ All domains loaded successfully!")

def test_article_fetching():
    """Test fetching individual articles"""
    print("\n🌾 Testing Article Fetching:")
    print("="*60)
    
    test_articles = ["Agriculture", "Climate", "Artificial intelligence"]
    
    for article_title in test_articles:
        print(f"\n  Fetching: {article_title}...")
        success, content, error = fetch_wikipedia_article(article_title)
        
        if success:
            print(f"    ✅ Success")
            print(f"    📊 Size: {len(content):,} characters")
            print(f"    📄 Preview: {content[:80]}...")
        else:
            print(f"    ❌ Error: {error}")

def test_combining_articles():
    """Test combining multiple articles"""
    print("\n📊 Testing Article Combining:")
    print("="*60)
    
    # Fetch 3 agriculture articles
    agriculture_keywords = DOMAIN_KEYWORDS["agriculture"][:3]
    
    print(f"\n  Fetching {len(agriculture_keywords)} agriculture articles...")
    articles_dict = {}
    
    for keyword in agriculture_keywords:
        success, content, error = fetch_wikipedia_article(keyword)
        if success:
            articles_dict[keyword] = content
            print(f"    ✅ {keyword}")
    
    if articles_dict:
        print(f"\n  Combining {len(articles_dict)} articles...")
        combined = combine_articles_content(articles_dict)
        
        print(f"    ✅ Combined successfully")
        print(f"    📈 Total size: {len(combined):,} characters")
        print(f"    📚 Articles: {len(articles_dict)}")
        
        # Show structure
        print(f"\n  Output Structure Preview:")
        lines = combined.split('\n')[:10]
        for line in lines:
            print(f"    {line}")

def test_domain_fetch():
    """Test fetching entire domain"""
    print("\n🚀 Testing Domain Fetch:")
    print("="*60)
    
    print("\n  Fetching Agriculture domain (max 3 articles for speed)...")
    articles = fetch_domain_articles("agriculture", num_articles=3)
    
    if articles:
        print(f"    ✅ Fetched {len(articles)} articles")
        for i, title in enumerate(articles.keys(), 1):
            content = articles[title]
            print(f"    {i}. {title} ({len(content):,} chars)")
        
        combined = combine_articles_content(articles)
        print(f"\n  Combined Dataset:")
        print(f"    📈 Total size: {len(combined):,} characters")
    else:
        print("    ❌ No articles fetched")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌾 WIKIPEDIA DOMAIN CONNECTOR - TEST SUITE")
    print("="*60)
    
    try:
        test_domains_available()
    except Exception as e:
        print(f"❌ Domain test failed: {e}")
    
    try:
        test_article_fetching()
    except Exception as e:
        print(f"❌ Article fetching test failed: {e}")
    
    try:
        test_combining_articles()
    except Exception as e:
        print(f"❌ Combining articles test failed: {e}")
    
    try:
        test_domain_fetch()
    except Exception as e:
        print(f"❌ Domain fetch test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETE")
    print("="*60)
