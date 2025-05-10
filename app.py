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
    
    Format as markdown with H3 headings and paragraphs"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"H3 generation failed: {str(e)}"

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
            presence_penalty=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Rewriting failed: {str(e)}"

def process_page_content(page_content, api_key):
    """Process content with enhanced restructuring"""
    rewritten = []
    
    for i, section in enumerate(page_content):
        if section['type'] == 'heading':
            if section['level'] == 2:
                # Add original H2
                rewritten.append(section)
                
                # Generate 2 new H3 sections
                context = page_content[i+1]['text'] if i+1 < len(page_content) else ""
                h3_content = generate_h3_sections(section['text'], context, api_key)
                
                # Parse generated H3s
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
            
            # Ensure originality
            if any(word in rewritten_text for word in section['text'].split()[:5]):
                rewritten_text = "Original content unavailable - please check API key" 
                
            rewritten.append({
                'type': 'paragraph',
                'text': rewritten_text
            })
    
    return rewritten

# Rest of the code (crawling and UI functions) remains the same as previous working version
# Make sure to update the process_page_content call in the main logic

# [Keep the existing crawl_website function]
# [Keep the existing Streamlit UI code]
# [Keep the existing results display code]
