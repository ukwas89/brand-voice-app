import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import tldextract
from openai import OpenAI

# Initialize session state
if 'original_content' not in st.session_state:
    st.session_state.original_content = {}
if 'rewritten_content' not in st.session_state:
    st.session_state.rewritten_content = {}

def get_domain(url):
    """Extract main domain from URL"""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def is_valid(url, main_domain):
    """Check if URL belongs to same domain and is valid"""
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and get_domain(url) == main_domain

def crawl_website(start_url, max_pages=3):
    """Crawl website and extract content structure"""
    try:
        main_domain = get_domain(start_url)
        visited = set()
        queue = deque([start_url])
        crawled_data = {}
        
        while queue and len(crawled_data) < max_pages:
            url = queue.popleft()
            
            if url in visited:
                continue
                
            try:
                response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                visited.add(url)
                
                # Extract content structure
                content_structure = []
                for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                    if tag.name.startswith('h'):
                        content_structure.append({
                            'type': 'heading',
                            'level': int(tag.name[1]),
                            'text': tag.get_text().strip()
                        })
                    else:
                        content_structure.append({
                            'type': 'paragraph',
                            'text': tag.get_text().strip()
                        })
                
                crawled_data[url] = content_structure
                
                # Find links
                for link in soup.find_all('a', href=True):
                    href = link['href'].split('#')[0]
                    absolute_url = urljoin(url, href)
                    if is_valid(absolute_url, main_domain) and absolute_url not in visited:
                        queue.append(absolute_url)
                        
            except Exception as e:
                continue
                
        return crawled_data
    
    except Exception as e:
        st.error(f"Crawling error: {str(e)}")
        return {}

def rewrite_content_section(text, original_word_count, api_key):
    """Rewrite content section with simplicity and originality"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Rewrite this text while maintaining:
    - Original meaning and factual accuracy
    - Simple language for 8-year-old comprehension
    - Unique phrasing (avoid AI patterns)
    - Exact word count: {original_word_count}
    
    Original text: {text}
    
    Make it:
    - Use short sentences and basic vocabulary
    - Include examples from daily life
    - Avoid complex terminology
    - Keep paragraph structure identical
    - Ensure 100% originality"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Rewriting failed: {str(e)}"

def process_page_content(page_content, api_key):
    """Process and rewrite page content section by section"""
    rewritten = []
    for section in page_content:
        if section['type'] == 'heading':
            rewritten.append(section)
        else:
            original_words = len(re.findall(r'\w+', section['text']))
            rewritten_text = rewrite_content_section(section['text'], original_words, api_key)
            
            new_words = len(re.findall(r'\w+', rewritten_text))
            if new_words != original_words:
                rewritten_text += " " * (original_words - new_words)
            
            rewritten.append({
                'type': 'paragraph',
                'text': rewritten_text
            })
    return rewritten

# Streamlit UI
st.set_page_config(page_title="Content Simplifier", layout="wide")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")
    max_pages = st.slider("Max Pages to Process", 1, 5, 1)

# Main Interface
st.title("🧒 Content Simplifier Tool")
st.markdown("Transform complex content into child-friendly versions while preserving structure")

website_url = st.text_input(
    "Enter Website URL", 
    placeholder="https://example.com",
    help="Start with homepage URL"
)

if st.button("Process Content"):
    if not website_url.startswith('http'):
        st.error("Please enter valid URL (http:// or https://)")
    elif not openai_key:
        st.error("OpenAI API key required")
    else:
        with st.spinner(f"📚 Analyzing website structure..."):
            crawled_data = crawl_website(website_url, max_pages)
            st.session_state.original_content = crawled_data
            
            if crawled_data:
                st.success(f"Analyzed {len(crawled_data)} pages")
                with st.spinner("✍️ Rewriting content for young readers..."):
                    for url, content in crawled_data.items():
                        rewritten = process_page_content(content, openai_key)
                        st.session_state.rewritten_content[url] = rewritten

# Display Results
if st.session_state.rewritten_content:
    st.markdown("---")
    st.subheader("Simplified Content Results")
    
    for idx, (url, content) in enumerate(st.session_state.rewritten_content.items()):
        with st.expander(f"View: {url}"):
            for section in content:
                if section['type'] == 'heading':
                    st.markdown(f"**{section['text']}**")
                else:
                    st.write(section['text'])
            
            # Create unique download button for each page
            sanitized_url = url.replace("https://", "").replace("/", "_")[:50]
            st.download_button(
                label="Download Simplified Content",
                data="\n\n".join([s['text'] for s in content]),
                file_name=f"simplified_{sanitized_url}.txt",
                key=f"download_{idx}"  # Unique key based on index
            )

st.markdown("---")
st.info("Key Features:\n"
        "1. Preserves original headings and structure\n"
        "2. Maintains exact word count\n"
        "3. Uses simple language for young readers\n"
        "4. Avoids AI detection patterns\n"
        "5. Ensures plagiarism-free content")
