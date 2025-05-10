import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import tldextract
from openai import OpenAI
from datetime import datetime

# Initialize session state
if 'original_content' not in st.session_state:
    st.session_state.original_content = {}
if 'rewritten_content' not in st.session_state:
    st.session_state.rewritten_content = {}

def generate_h3_sections(h2_text, context, api_key):
    """Generate two professional H3 sections with enhanced content"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Given this H2 heading: '{h2_text}'
    Context: '{context[:500]}'
    
    Create two professional H3 subheadings with content that:
    1. Expand on the H2 topic with specific insights
    2. Include industry-relevant terminology
    3. Maintain formal business tone
    4. Add strategic value to the section
    
    Format as markdown with H3 headings and paragraphs"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Section enhancement failed: {str(e)}"

def rewrite_content_section(text, original_word_count, api_key):
    """Professional content optimization with value addition"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Enhance this professional content while:
    1. Maintaining formal business tone
    2. Preserving technical accuracy
    3. Adding strategic insights
    4. Using industry-specific terminology
    5. Keeping {original_word_count} words exactly
    
    Original text: {text}
    
    Improvements should include:
    - Data-driven recommendations
    - Best practice integration
    - Actionable insights
    - Professional formatting
    - Complete originality"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            presence_penalty=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Content enhancement failed: {str(e)}"

def process_page_content(page_content, api_key):
    """Process content with professional enhancements"""
    rewritten = []
    
    for i, section in enumerate(page_content):
        if section['type'] == 'heading':
            if section['level'] == 2:
                # Preserve original H2
                rewritten.append(section)
                
                # Generate strategic H3 expansions
                context = page_content[i+1]['text'] if i+1 < len(page_content) else ""
                h3_content = generate_h3_sections(section['text'], context, api_key)
                
                # Parse generated H3 content
                current_h3 = None
                for line in h3_content.split('\n'):
                    if line.startswith('### '):
                        if current_h3:
                            rewritten.append(current_h3)
                        current_h3 = {
                            'type': 'heading',
                            'level': 3,
                            'text': line[4:].strip()
                        }
                    elif line.strip() and current_h3:
                        rewritten.append(current_h3)
                        rewritten.append({
                            'type': 'paragraph',
                            'text': line.strip()
                        })
                        current_h3 = None
                
            else:
                rewritten.append(section)
        else:
            original_words = len(re.findall(r'\w+', section['text']))
            rewritten_text = rewrite_content_section(section['text'], original_words, api_key)
            
            # Quality assurance check
            if len(re.findall(r'\w+', rewritten_text)) < original_words * 0.9:
                rewritten_text = section['text']  # Preserve original if word count mismatch
                
            rewritten.append({
                'type': 'paragraph',
                'text': rewritten_text
            })
    
    return rewritten

# Streamlit UI Configuration
st.set_page_config(
    page_title="Professional Content Enhancer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# [Keep existing crawl_website function]
# [Maintain previous UI structure with professional terminology updates]

# Results Display
if st.session_state.rewritten_content:
    st.divider()
    st.subheader("Enhanced Professional Content")
    
    for idx, (url, content) in enumerate(st.session_state.rewritten_content.items()):
        with st.expander(f"Enhanced Content: {url}"):
            st.markdown(f"**Original Source:** [{url}]({url})")
            
            export_content = []
            for section in content:
                if section['type'] == 'heading':
                    if section['level'] == 3:
                        st.markdown(f"#### {section['text']}")
                        export_content.append(f"### {section['text']}")
                    else:
                        st.markdown(f"### {section['text']}")
                        export_content.append(f"## {section['text']}")
                else:
                    st.markdown(section['text'])
                    export_content.append(section['text'])
            
            # Professional export options
            sanitized_url = re.sub(r'\W+', '', url)[:30]
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            st.download_button(
                label="Download Enhanced Version",
                data="\n\n".join(export_content),
                file_name=f"professional_{sanitized_url}_{timestamp}.md",
                key=f"export_{idx}",
                help="Formatted markdown with professional enhancements"
            )
