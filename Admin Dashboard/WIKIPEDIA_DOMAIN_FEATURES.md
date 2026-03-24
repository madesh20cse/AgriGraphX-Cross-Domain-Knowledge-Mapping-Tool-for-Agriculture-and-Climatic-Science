# Wikipedia Connector - Domain Article Fetching Feature

## Overview

The Wikipedia connector has been enhanced to fetch **multiple related articles based on domain** instead of just single articles. This creates rich, domain-specific datasets by combining content from multiple Wikipedia articles.

## New Features

### 1. **Domain-Based Article Fetching**
Automatically fetch multiple articles related to specific domains:

- 🌾 **Agriculture** (15 related topics)
  - Agriculture, Farming, Crop, Soil, Irrigation, Pesticide, Fertilizer, Corn, Wheat, Rice, Livestock, Aquaculture, etc.

- 🌍 **Climate** (15 related topics)
  - Climate, Global Warming, Weather, Atmosphere, Greenhouse Gas, Carbon Cycle, Drought, Flood, Temperature, etc.

- 🤖 **AI Technology** (14 related topics)
  - Artificial Intelligence, Machine Learning, Deep Learning, Neural Networks, NLP, Computer Vision, Data Science, etc.

- 📊 **Data Science** (15 related topics)
  - Data Science, Statistics, Data Analysis, Big Data, Machine Learning, Regression, Classification, etc.

### 2. **Multiple Article Selection**
Users can now:
- Search for specific topics
- **Multi-select multiple articles** from search results
- Combine them into a single unified dataset

### 3. **Combined Dataset Output**
All selected/fetched articles are automatically merged into a unified text format with:
- Clear article boundaries
- Organized structure
- Metadata headers
- Cross-domain knowledge

## User Interface

### Tab 1: Search Articles
```
┌─────────────────────────────────────┐
│ Wikipedia Data Source - Domain Articles
├─────────────────────────────────────┤
│
│  🔍 Search Articles | 📚 Domain Articles
│
│  Search for Specific Articles
│  ────────────────────────────
│  Search Query: [___________________]
│  Max Results: [5]
│
│  Found 5 results:
│  ☑ Article 1
│  ☑ Article 2
│  ☑ Article 3
│
│  [📥 Fetch Selected Articles] [ℹ️ Show Metadata]
│
│  Preview Combined Content >
└─────────────────────────────────────┘
```

### Tab 2: Domain Articles
```
┌─────────────────────────────────────┐
│  📚 Domain Articles
│  ────────────────────────────
│  Select Domain: [Agriculture  ▼]
│
│  Number of Articles: [5  ▤▤▤▤▤]
│
│  Keywords for 'Agriculture' >
│
│  [🚀 Fetch Domain Articles]
│
│  ✅ Successfully fetched 5 article(s)
│
│  Articles Combined: 5
│  Total Characters: 45,230
│  Estimated Words: 8,450
│
│  Preview Combined Content >
│  📄 Articles Included >
│
└─────────────────────────────────────┘
```

## How It Works

### Feature 1: Domain Article Fetching
```python
# Fetch articles for a domain
articles = fetch_domain_articles("agriculture", num_articles=5)
# Returns: {"Farming": content, "Crop": content, "Soil": content, ...}

# Combine into unified dataset
combined = combine_articles_content(articles)
# Returns: Formatted multi-article dataset
```

### Feature 2: Custom Multi-Select
```python
# User can search and select multiple articles
search_results = search_wikipedia("Agriculture", results=10)
# User selects: ["Farming", "Crop", "Irrigation", "Soil"]

# Fetch all selected articles
articles = {}
for article in selected:
    articles[article] = fetch_wikipedia_article(article)

# Combine
combined = combine_articles_content(articles)
```

## Usage Workflow

### Method 1: Domain-Based (Recommended for Datasets)
1. Open **Dataset Selection** → **Wikipedia** tab
2. Click **📚 Domain Articles** tab
3. Select domain: `Agriculture` / `Climate` / `AI Technology` / `Data Science`
4. Adjust "Number of Articles" slider (2-15)
5. Click **🚀 Fetch Domain Articles**
6. System automatically fetches related articles
7. Preview combined content
8. Content ready for knowledge graph processing

### Method 2: Custom Search
1. Open **Dataset Selection** → **Wikipedia** tab
2. Click **🔍 Search Articles** tab
3. Enter search query: e.g., "Renewable Energy"
4. Set Max Results: 5
5. **Select multiple articles** from the list
6. Click **📥 Fetch Selected Articles**
7. Preview combined content
8. Content ready for processing

## Output Format

**Combined Dataset Structure:**
```
================================================================================
DOMAIN DATASET - 5 ARTICLES COMBINED
================================================================================

────────────────────────────────────────────────────────────────────────────────
ARTICLE 1/5: Agriculture
────────────────────────────────────────────────────────────────────────────────
Title: Agriculture

Summary:
[Article summary text...]

Content:
[Full article content...]


────────────────────────────────────────────────────────────────────────────────
ARTICLE 2/5: Farming
────────────────────────────────────────────────────────────────────────────────
Title: Farming
[Content...]

... (Articles 3-5 follow same format)
```

## New Functions

### `fetch_domain_articles(domain, num_articles=5)`
Fetches multiple related articles for a domain.
```python
from connectors.wikipedia_connector import fetch_domain_articles

articles = fetch_domain_articles("agriculture", num_articles=5)
# Returns: Dict[str, str] with article titles and content
```

### `combine_articles_content(articles_dict)`
Merges multiple articles into unified format.
```python
from connectors.wikipedia_connector import combine_articles_content

combined = combine_articles_content(articles)
# Returns: Formatted combined content as string
```

### `DOMAIN_KEYWORDS` Dictionary
Available domains and their keywords:
```python
from connectors.wikipedia_connector import DOMAIN_KEYWORDS

# See all domains
print(DOMAIN_KEYWORDS.keys())  # agriculture, climate, ai_technology, data_science

# Access keywords for a domain
keywords = DOMAIN_KEYWORDS["agriculture"]
# Returns: ["Agriculture", "Farming", "Crop", "Soil", ...]
```

## Advanced Usage

### Programmatic Dataset Creation
```python
from connectors.wikipedia_connector import fetch_domain_articles, combine_articles_content

# Fetch agriculture dataset
articles = fetch_domain_articles("agriculture", num_articles=10)

if articles:
    # Combine into unified dataset
    dataset = combine_articles_content(articles)
    
    # Save to file
    with open("agriculture_dataset.txt", "w") as f:
        f.write(dataset)
    
    # Use in knowledge graph
    from knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    kg.process_text(dataset)
```

### Custom Domain Addition
To add a new domain, edit `DOMAIN_KEYWORDS`:
```python
DOMAIN_KEYWORDS = {
    ...existing domains...
    "renewable_energy": [
        "Renewable energy", "Solar power", "Wind power", 
        "Hydropower", "Biomass", "Geothermal energy",
        "Photovoltaic", "Sustainability"
    ]
}
```

## Features Comparison

| Feature | Before | After |
|---------|--------|-------|
| Single Article | ✅ | ✅ |
| Multiple Articles | ❌ | ✅ |
| Domain Mapping | ❌ | ✅ 4 domains |
| Multi-Select | ❌ | ✅ |
| Combined Output | ❌ | ✅ |
| Metadata Display | ✅ Limited | ✅ Enhanced |
| Statistics | ❌ | ✅ Article count, chars, words |
| Progress Tracking | ❌ | ✅ Progress bar |
| Article List | ❌ | ✅ Expandable list |

## Performance

- **Single article fetch**: ~2-5 seconds per article
- **Domain fetch (5 articles)**: ~10-25 seconds (depends on Wikipedia API)
- **Combining articles**: <100ms
- **Total dataset size**: 10,000-50,000+ characters depending on articles

## Error Handling

✅ Handles Wikipedia API errors gracefully
✅ Skips articles that fail to load
✅ Shows partial results if some articles fail
✅ User-friendly error messages
✅ Retry capability

## Storage & Integration

Selected datasets are stored in `st.session_state`:
```python
st.session_state.dataset_content  # Combined article text
st.session_state.dataset_source   # "Wikipedia"
```

Integration with existing modules:
- Flows into NLP pipeline automatically
- Compatible with knowledge_graph.py
- Works with semantic_search.py
- Ready for refinement_tools.py

## Testing

### Test Case 1: Fetch Agriculture Domain
1. Domain: Agriculture
2. Articles: 5
3. Expected: 5 farming/agriculture related articles combined
4. Output: 30,000+ characters

### Test Case 2: Custom Search - AI
1. Search: "Artificial Intelligence"
2. Select: ["AI", "Machine Learning", "Neural Network", "Deep Learning"]
3. Expected: 4 articles combined
4. Output: 25,000+ characters

### Test Case 3: Climate Domain
1. Domain: Climate
2. Articles: 10
3. Expected: 10 climate-related articles
4. Output: 60,000+ characters

## FAQ

**Q: Can I select articles from different searches?**
A: No, each search session is independent. Use Domain Articles for pre-curated multi-article sets.

**Q: What if some articles fail to fetch?**
A: The system shows partial results with successful articles only.

**Q: How are keywords chosen for each domain?**
A: Keywords are manually curated for relevance and cross-domain connectivity.

**Q: Can I add custom domains?**
A: Yes, edit `DOMAIN_KEYWORDS` dictionary in wikipedia_connector.py

**Q: What's the maximum articles I can combine?**
A: Technically unlimited, but 10-15 is recommended for balanced datasets.

---

**Feature Release Date**: March 18, 2026
**Status**: ✅ Production Ready
**Testing**: ✅ Complete
