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
    """Generate two relevant H3 sections with content"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Given this H2 heading: '{h2_text}'
    And context: '{context[:500]}'
    
    Create:
    1. Two specific H3 subheadings (different from original content)
    2. For each H3, a 50-70 word explanation using simple terms
    3. Ensure completely original content
    
    Format as:
    H3: [subheading 1]
    Content: [text]
    
    H3: [subheading 2]
    Content: [text]"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"H3 generation failed: {str(e)}"

def process_page_content(page_content, api_key):
    """Process content with enhanced restructuring"""
    rewritten = []
    current_context = ""
    
    for i, section in enumerate(page_content):
        if section['type'] == 'heading':
            if section['level'] == 2:
                # Add original H2
                rewritten.append(section)
                current_context = section['text']
                
                # Generate 2 new H3 sections
                next_content = page_content[i+1]['text'] if i+1 < len(page_content) else ""
                h3_content = generate_h3_sections(section['text'], next_content, api_key)
                
                # Parse generated H3s
                h3_blocks = re.split(r'H3: ', h3_content)
                for block in h3_blocks[1:]:  # Skip first empty split
                    if 'Content:' in block:
                        h3_text, content = block.split('Content:', 1)
                        rewritten.append({
                            'type': 'heading',
                            'level': 3,
                            'text': h3_text.strip()
                        })
                        rewritten.append({
                            'type': 'paragraph',
                            'text': content.strip()
                        })
                        
            else:
                rewritten.append(section)
        else:
            # Enhanced rewriting with originality checks
            original_words = len(re.findall(r'\w+', section['text']))
            rewritten_text = rewrite_content_section(section['text'], original_words, api_key)
            
            # Ensure originality
            if any(word in rewritten_text for word in section['text'].split()[:5]):
                rewritten_text = "Original content unavailable" # Fallback
                
            rewritten.append({
                'type': 'paragraph',
                'text': rewritten_text
            })
    
    return rewritten

def rewrite_content_section(text, original_word_count, api_key):
    """Advanced rewriting with anti-plagiarism measures"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Completely rewrite this text with:
    - 0% plagiarism
    - Simplified language (8-year-old level)
    - 2-3 short sentences per paragraph
    - {original_word_count} words exactly
    - Add practical examples
    
    Original text: {text}
    
    Output must:
    - Use different sentence structures
    - Avoid original terminology
    - Include 1 analogy/metaphor
    - Add a rhetorical question"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            presence_penalty=0.7  # Discourage original phrases
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Rewriting failed: {str(e)}"

# (Keep previous UI and crawling functions, update process_page_content call)

# In your results display section:
if st.session_state.rewritten_content:
    st.divider()
    st.subheader("Enhanced Content Output")
    
    tab_labels = [f"Page {i+1}" for i in range(len(st.session_state.rewritten_content))]
    tabs = st.tabs(tab_labels)
    
    for idx, (url, content) in enumerate(st.session_state.rewritten_content.items()):
        with tabs[idx]:
            with st.container(border=True):
                st.markdown(f"**Source URL:** `{url}`")
                st.caption("New H3 sections highlighted in blue")
                
                export_content = []
                for section in content:
                    if section['type'] == 'heading':
                        if section['level'] == 3:
                            st.markdown(f"<h4 style='color: #1e88e5;'>{section['text']}</h4>", 
                                      unsafe_allow_html=True)
                            export_content.append(f"### {section['text']}")
                        else:
                            st.markdown(f"### {section['text']}")
                            export_content.append(f"## {section['text']}")
                    else:
                        st.markdown(section['text'])
                        export_content.append(section['text'])
                
                sanitized_url = re.sub(r'\W+', '', url)[:30]
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                st.download_button(
                    label="Export Enhanced Content",
                    data="\n\n".join(export_content),
                    file_name=f"enhanced_{sanitized_url}_{timestamp}.md",
                    key=f"export_{idx}",
                    use_container_width=True
                )
