"""
file_uploader.py — File Upload Data Connector

Handles file uploads (CSV, TXT, JSON) and converts them to unified text format.
Includes dataset preprocessing and categorization.
Used by: Dataset selection UI for file-based data sources.
"""

import streamlit as st
import pandas as pd
import json
import os
from typing import Tuple, Optional
from dataset_preprocessor import DatasetPreprocessor, categorize_dataset, get_category_info


ALLOWED_EXTENSIONS = {'.txt', '.csv', '.json', '.jsonl'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate uploaded file.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (valid: bool, message: str)
    """
    if uploaded_file is None:
        return False, "No file selected."
    
    # Check file extension
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: 50MB. Your file: {uploaded_file.size / 1024 / 1024:.2f}MB"
    
    return True, "File is valid."


def read_text_file(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Read a TXT file.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, content: str, error: str or None)
    """
    try:
        content = uploaded_file.read().decode('utf-8')
        return True, content, None
    except UnicodeDecodeError:
        return False, "", "Error: File must be UTF-8 encoded text."
    except Exception as e:
        return False, "", f"Error reading file: {str(e)}"


def read_csv_file(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Read a CSV file and convert to text format.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, content: str, error: str or None)
    """
    try:
        df = pd.read_csv(uploaded_file)
        
        # Validate data
        if df.empty:
            return False, "", "CSV file is empty."
        
        # Convert to text format
        content = f"CSV Data from {uploaded_file.name}\n"
        content += f"{'='*80}\n"
        content += f"Rows: {len(df)} | Columns: {len(df.columns)}\n"
        content += f"Columns: {', '.join(df.columns)}\n"
        content += f"{'─'*80}\n\n"
        
        # Add data
        for idx, row in df.iterrows():
            content += f"Record {idx + 1}:\n"
            for col, val in row.items():
                content += f"  {col}: {val}\n"
            content += "\n"
        
        return True, content, None
        
    except Exception as e:
        return False, "", f"Error reading CSV: {str(e)}"


def read_json_file(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Read a JSON file and convert to text format.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, content: str, error: str or None)
    """
    try:
        data = json.load(uploaded_file)
        
        # Convert to text format
        content = f"JSON Data from {uploaded_file.name}\n"
        content += f"{'='*80}\n"
        content += json.dumps(data, indent=2)
        
        return True, content, None
        
    except json.JSONDecodeError:
        return False, "", "Error: Invalid JSON format."
    except Exception as e:
        return False, "", f"Error reading JSON: {str(e)}"


def read_jsonl_file(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Read a JSONL (JSON Lines) file and convert to text format.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, content: str, error: str or None)
    """
    try:
        lines = uploaded_file.read().decode('utf-8').strip().split('\n')
        
        content = f"JSONL Data from {uploaded_file.name}\n"
        content += f"{'='*80}\n"
        content += f"Total Records: {len(lines)}\n"
        content += f"{'─'*80}\n\n"
        
        for i, line in enumerate(lines):
            if line.strip():
                try:
                    obj = json.loads(line)
                    content += f"Record {i + 1}:\n"
                    content += json.dumps(obj, indent=2) + "\n\n"
                except json.JSONDecodeError:
                    continue
        
        return True, content, None
        
    except Exception as e:
        return False, "", f"Error reading JSONL: {str(e)}"


def process_uploaded_file(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Process uploaded file based on its type.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success: bool, content: str, error: str or None)
    """
    # Validate file
    valid, message = validate_file(uploaded_file)
    if not valid:
        return False, "", message
    
    # Get file extension
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    # Process based on type
    if file_ext == '.txt':
        return read_text_file(uploaded_file)
    elif file_ext == '.csv':
        return read_csv_file(uploaded_file)
    elif file_ext in {'.json', '.jsonl'}:
        if file_ext == '.json':
            return read_json_file(uploaded_file)
        else:
            return read_jsonl_file(uploaded_file)
    else:
        return False, "", "Unsupported file format."


def render_file_uploader():
    """
    Render Streamlit UI for file upload with preprocessing options.
    
    Returns:
        Tuple of (success: bool, content: str or None)
    """
    st.markdown("### 📂 Upload Dataset File")
    st.markdown("📄 Upload agriculture, climate, or data science datasets (CSV, TXT, JSON)")
    st.markdown("**✨ Supported formats:** CSV, TXT, JSON, JSONL | **📏 Max size:** 50MB")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['txt', 'csv', 'json'],
        help=f"Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"📄 **File:** {uploaded_file.name}")
            st.markdown(f"📏 **Size:** {uploaded_file.size / 1024:.2f} KB")
        
        # Preprocessing options
        st.markdown("#### ⚙️ Preprocessing Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            remove_urls = st.checkbox("🌐 Remove URLs", value=True, help="Remove web links")
        
        with col2:
            remove_emails = st.checkbox("📧 Remove Emails", value=True, help="Remove email addresses")
        
        with col3:
            normalize_text = st.checkbox("🔀 Normalize", value=True, help="Remove accents & special unicode")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            remove_special = st.checkbox("🔧 Remove Special Chars", value=True, help="Clean special characters")
        
        with col2:
            lowercase = st.checkbox("🎧 Lowercase", value=True, help="Convert to lowercase")
        
        with col3:
            auto_categorize = st.checkbox("🤖 Auto-Categorize", value=True, help="Detect dataset domain")
        
        # Process button
        if st.button("📥 Upload & Preprocess", type="primary"):
            with st.spinner("Processing file..."):
                success, content, error = process_uploaded_file(uploaded_file)
            
            if success:
                # Apply preprocessing
                preprocessor = DatasetPreprocessor()
                
                original_content = content
                processed_content = preprocessor.preprocess_full(
                    content,
                    lowercase=lowercase,
                    remove_urls=remove_urls,
                    remove_emails=remove_emails,
                    remove_special=remove_special,
                    normalize=normalize_text
                )
                
                # Categorize dataset
                category = "general"
                if auto_categorize:
                    category = categorize_dataset(uploaded_file.name, content[:500])
                
                category_info = get_category_info(category)
                
                # Generate report
                report = preprocessor.generate_report(original_content, processed_content)
                
                st.success("✅ File uploaded and preprocessed successfully!")
                
                # Display category
                st.markdown(f"### {category_info['emoji']} Dataset Category: **{category_info['name']}**")
                st.caption(f"🏇 {category_info['description']}")
                
                # Display statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📂 Original Size", f"{report['original_characters']:,} chars")
                
                with col2:
                    st.metric("✍️ Processed Size", f"{report['processed_characters']:,} chars")
                
                with col3:
                    st.metric("📄 Reduction", report['percentage_reduction'])
                
                with col4:
                    st.metric("📚 Words", f"{report['processed_words']:,}")
                
                # Show before/after preview
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.expander("📁 Original Content Preview"):
                        preview = original_content[:1000] + ("..." if len(original_content) > 1000 else "")
                        st.code(preview, language="markdown")
                
                with col2:
                    with st.expander("✨ Processed Content Preview"):
                        preview = processed_content[:1000] + ("..." if len(processed_content) > 1000 else "")
                        st.code(preview, language="markdown")
                
                # Detailed report
                with st.expander("📊 Detailed Preprocessing Report"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📝 Text Statistics:**")
                        st.write(f"📄 Original Characters: {report['original_characters']:,}")
                        st.write(f"✨ Processed Characters: {report['processed_characters']:,}")
                        st.write(f"🗑️ Characters Removed: {report['characters_removed']:,}")
                    
                    with col2:
                        st.write("**📚 Word & Sentence Statistics:**")
                        st.write(f"📖 Original Words: {report['original_words']:,}")
                        st.write(f"✂️ Processed Words: {report['processed_words']:,}")
                        st.write(f"💬 Original Sentences: {report['original_sentences']}")
                        st.write(f"📋 Processed Sentences: {report['processed_sentences']}")
                
                return True, processed_content
            else:
                st.error(f"❌ {error}")
    
    return False, None


def save_dataset_file(content: str, dataset_name: str, source: str, metadata: dict = None) -> Tuple[bool, str, str]:
    """
    Save dataset content to files in data/datasets directory with metadata.
    Creates both .txt (content) and _meta.json (metadata) files.
    
    Args:
        content: Dataset content as string
        dataset_name: Name of the dataset (without extension)
        source: Source of the dataset (Wikipedia, News, etc.)
        metadata: Optional metadata dictionary
        
    Returns:
        Tuple of (success: bool, file_path: str, error_message: str)
    """
    try:
        # Get the Admin Dashboard directory (parent of connectors)
        admin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        datasets_dir = os.path.join(admin_dir, "data", "datasets")
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in dataset_name if c.isalnum() or c in (' ', '_', '-')).replace(' ', '_').lower()
        
        # Save content file
        content_file = os.path.join(datasets_dir, f"{safe_name}.txt")
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create metadata
        if metadata is None:
            metadata = {}
        
        from datetime import datetime
        meta = {
            "name": dataset_name,
            "filename": f"{safe_name}.txt",
            "source": source,
            "created_at": metadata.get("created_at", datetime.now().isoformat()),
            "size_bytes": len(content.encode('utf-8')),
            "size_chars": len(content),
            "size_words": len(content.split()),
            **metadata
        }
        
        # Save metadata file
        meta_file = os.path.join(datasets_dir, f"{safe_name}_meta.json")
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        return True, content_file, ""
    
    except Exception as e:
        return False, "", str(e)


def export_dataset(content: str, filename: str = "dataset.txt"):
    """
    Create download button for processed dataset.
    
    Args:
        content: Dataset content as string
        filename: Output filename
    """
    st.download_button(
        label="📥 Download Dataset",
        data=content,
        file_name=filename,
        mime="text/plain"
    )
