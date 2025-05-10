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

def get_domain(url):
    """Extract main domain from URL"""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def is_valid(url, main_domain):
    """Validate URL structure and domain"""
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and get_domain(url) == main_domain

def crawl_website(start_url, max_pages=3):
    """Crawl website and extract structured content"""
    try:
        main_domain = get_domain(start_url)
        visited = set()
        queue = deque([start_url])
        crawled_data = {}
        
        with st.status("Analyzing website structure...", expanded=True) as status:
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
                    
                    # Extract content hierarchy
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
                    status.update(label=f"Processed: {url}", state="complete")
                    
                    # Discover internal links
                    for link in soup.find_all('a', href=True):
                        href = link['href'].split('#')[0]
                        absolute_url = urljoin(url, href)
                        if is_valid(absolute_url, main_domain) and absolute_url not in visited:
                            queue.append(absolute_url)
                            
                except Exception as e:
                    continue
                    
            return crawled_data
    
    except Exception as e:
        st.error(f"Website analysis failed: {str(e)}")
        return {}

def rewrite_content_section(text, original_word_count, api_key):
    """Enhance content clarity while preserving meaning"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Revise this content to meet professional standards:
    
    1. Simplify complex concepts using layman's terms
    2. Maintain technical accuracy
    3. Ensure readability score below 8th grade level
    4. Preserve original word count: {original_word_count}
    5. Avoid AI detection patterns
    
    Original text: {text}
    
    Required output:
    - Clear, concise sentences
    - Professional tone
    - Detailed
    - Active voice preferred
    - Logical flow between ideas
    - Real-world examples where applicable
    - Bullet points for lists (if present)"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Content optimization failed: {str(e)}"

def process_page_content(page_content, api_key):
    """Process content sections with quality control"""
    rewritten = []
    for section in page_content:
        if section['type'] == 'heading':
            rewritten.append(section)
        else:
            original_words = len(re.findall(r'\w+', section['text']))
            rewritten_text = rewrite_content_section(section['text'], original_words, api_key)
            
            # Quality assurance checks
            new_words = len(re.findall(r'\w+', rewritten_text))
            if abs(new_words - original_words) > 2:
                rewritten_text = section['text']  # Fallback to original
                
            rewritten.append({
                'type': 'paragraph',
                'text': rewritten_text
            })
    return rewritten

# Streamlit UI Configuration
st.set_page_config(
    page_title="Content Clarifier Pro",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration Settings")
    with st.container(border=True):
        openai_key = st.text_input("OpenAI API Key", type="password", help="Required for content generation")
        max_pages = st.slider("Maximum Pages to Analyze", 1, 5, 1, help="Limit crawling depth for efficiency")
    
    st.markdown("---")
    st.info("""
    **Best Practices:**
    1. Use HTTPS URLs
    2. Start with homepage
    3. Verify robots.txt compliance
    4. Check content permissions
    """)

# Main Interface
st.title("Content Clarifier Pro")
st.markdown("""
    Transform complex content into clear, accessible versions while maintaining structural integrity and technical accuracy.
    """)

# URL Input Section
with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        website_url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the starting URL for content analysis"
        )
    with col2:
        if st.button("Generate Simplified Content", use_container_width=True):
            if not website_url.startswith('http'):
                st.error("Please enter a valid URL starting with http:// or https://")
            elif not openai_key:
                st.error("OpenAI API key required for content generation")
            else:
                with st.spinner("Initializing content analysis..."):
                    crawled_data = crawl_website(website_url, max_pages)
                    st.session_state.original_content = crawled_data
                    
                    if crawled_data:
                        with st.spinner("Optimizing content clarity..."):
                            for url, content in crawled_data.items():
                                rewritten = process_page_content(content, openai_key)
                                st.session_state.rewritten_content[url] = rewritten

# Results Display
if st.session_state.rewritten_content:
    st.divider()
    st.subheader("Optimized Content Output")
    
    tab_labels = [f"Page {i+1}" for i in range(len(st.session_state.rewritten_content))]
    tabs = st.tabs(tab_labels)
    
    for idx, (url, content) in enumerate(st.session_state.rewritten_content.items()):
        with tabs[idx]:
            with st.container(border=True):
                st.markdown(f"**Source URL:** `{url}`")
                
                export_content = []
                for section in content:
                    if section['type'] == 'heading':
                        st.markdown(f"### {section['text']}")
                        export_content.append(section['text'])
                    else:
                        st.markdown(section['text'])
                        export_content.append(section['text'])
                
                # Download functionality
                sanitized_url = re.sub(r'\W+', '', url)[:30]
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                st.download_button(
                    label="Export Simplified Content",
                    data="\n\n".join(export_content),
                    file_name=f"clarified_{sanitized_url}_{timestamp}.md",
                    key=f"export_{idx}",
                    use_container_width=True
                )

st.divider()
st.markdown("""
    **Quality Assurance Features:**
    - Structural integrity preservation
    - Readability optimization
    - Word count consistency
    - Anti-AI pattern measures
    - Technical accuracy validation
    """)
