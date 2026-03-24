# Wikipedia Domain Article Fetching - Quick Reference Card

## 🌱 What's New?

The Wikipedia connector now fetches **multiple related articles** organized by domain instead of single articles.

---

## 🎯 Quick Start

### In Streamlit App:
```
1. Login → go to main app
2. Click "📂 Dataset Selection" 
3. Select "Wikipedia" tab
4. Choose "📚 Domain Articles" tab
5. Select domain (Agriculture/Climate/AI/DataScience)
6. Adjust slider: 2-15 articles
7. Click "🚀 Fetch Domain Articles"
8. Done! Dataset ready
```

---

## 📚 Available Domains

| Domain | Keywords | Use For |
|--------|----------|---------|
| 🌾 Agriculture | 15 items | Farming, crops, soil, etc. |
| 🌍 Climate | 15 items | Weather, climate change, etc. |
| 🤖 AI Technology | 14 items | Machine learning, AI algorithms |
| 📊 Data Science | 15 items | Statistics, data analysis |

---

## 🚀 Key Features

### Feature 1: Domain-Based Fetching
Select domain → System fetches related articles automatically

### Feature 2: Multi-Select Search
Search any topic → Select multiple articles → Combine them

### Feature 3: Unified Output
All articles merged into single formatted text dataset

### Feature 4: Smart Statistics
Shows: # Articles, Total chars, Estimated words, List of included articles

---

## 💻 Programmatic Usage

```python
from connectors.wikipedia_connector import (
    fetch_domain_articles,
    combine_articles_content
)

# Fetch domain articles
articles = fetch_domain_articles("agriculture", num_articles=5)

# Combine
dataset = combine_articles_content(articles)

# Use
from knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
kg.process_text(dataset)
```

---

## 📊 Expected Output

```
20,000+ chars per article
→ 5 articles = 100,000+ chars
→ 10 articles = 200,000+ chars

All articles combined with clear boundaries
Well-organized for NLP processing
Ready for knowledge graph building
```

---

## ✅ Test It

```bash
# Verify it works
python test_wikipedia_connector.py

# Should show:
# ✓ All domains loaded
# ✓ Article fetching works
# ✓ Combining works
# ✓ Domain fetch works
```

---

## 🎯 Use Cases

1. **Agriculture Dataset** → 8 farming articles
2. **Climate Dataset** → 10 climate change articles
3. **AI Dataset** → 10 ML/AI articles
4. **Custom** → Search and multi-select any topic

---

## 📚 Documentation

- `WIKIPEDIA_DOMAIN_GUIDE.md` - Complete guide (you are here)
- `WIKIPEDIA_DOMAIN_FEATURES.md` - Feature details
- `WIKIPEDIA_ENHANCEMENT_SUMMARY.md` - Implementation summary
- `test_wikipedia_connector.py` - Test suite

---

## 🔗 Integration

```
Wikipedia Connector
        ↓
Fetch domain articles
        ↓
Combine into unified text
        ↓
Store in session_state
        ↓
Pass to Knowledge Graph
        ↓
Process → Build graph
```

---

## ⚡ Performance

- Single article: 2-5 seconds
- Combine 5 articles: <100ms
- Full domain (10 articles): 30-60 seconds
- Session storage: Instant

---

## ✨ What Changed

### Before:
```
❌ One article at a time
❌ No multi-select
❌ Limited to search results
```

### After:
```
✅ Multiple articles at once
✅ Multi-select capability
✅ Pre-curated domains
✅ Automatic combining
✅ Statistics display
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Slow fetching | Wikipedia API is throttled, wait or reduce articles |
| Some articles missing | Some keywords might not have Wikipedia pages |
| Large dataset | Reduce number of articles to 5-10 |
| Session cleared | Re-select dataset (state is lost on page refresh) |

---

## 🎓 Learning Path

1. **Beginner**: Use Domain Articles (simplest)
2. **Intermediate**: Use Search + Multi-select
3. **Advanced**: Use programmatic API
4. **Expert**: Add custom domains

---

## 📊 Dataset Size Reference

| Selection | Size | Characters |
|-----------|------|-----------|
| 1 article | Small | 20K-90K |
| 3 articles | Medium | 100K-200K |
| 5 articles | Large | 150K-300K |
| 10+ articles | XL | 300K-500K+ |

---

**Version**: 1.0
**Status**: ✅ Production Ready
**Last Updated**: March 18, 2026
