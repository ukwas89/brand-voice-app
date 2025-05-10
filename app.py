import streamlit as st
import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import tldextract
from openai import OpenAI
from datetime import datetime
from urllib.robotparser import RobotFileParser

# Initialize session states
if 'brand_style' not in st.session_state:
    st.session_state.brand_style = {}
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}
if 'rewritten_content' not in st.session_state:
    st.session_state.rewritten_content = ""

# ------ Core Functions ------
def get_domain(url):
    """Extract main domain from URL"""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def is_valid(url, main_domain):
    """Validate URL structure and domain"""
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and get_domain(url) == main_domain

def crawl_website(start_url, max_pages=3):
    """Crawl website with error handling"""
    try:
        main_domain = get_domain(start_url)
        visited = set()
        queue = deque([start_url])
        crawled_data = {}
        
        with st.status("Analyzing website...", expanded=True) as status:
            while queue and len(crawled_data) < max_pages:
                url = queue.popleft()
                
                if url in visited:
                    continue
                
                try:
                    # Check robots.txt
                    rp = RobotFileParser()
                    rp.set_url(urljoin(url, "/robots.txt"))
                    rp.read()
                    
                    if not rp.can_fetch("*", url):
                        st.warning(f"Skipping {url} due to robots.txt restrictions")
                        continue
                        
                    response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')
                    visited.add(url)
                    
                    # Extract content structure
                    content_structure = []
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'p']):
                        content_structure.append({
                            'type': tag.name,
                            'text': tag.get_text().strip()
                        })
                    
                    crawled_data[url] = content_structure
                    
                    # Find internal links
                    for link in soup.find_all('a', href=True):
                        href = link['href'].split('#')[0]
                        absolute_url = urljoin(url, href)
                        if is_valid(absolute_url, main_domain) and absolute_url not in visited:
                            queue.append(absolute_url)
                            
                except Exception as e:
                    continue
                    
            return crawled_data
            
    except Exception as e:
        st.error(f"Crawling failed: {str(e)}")
        return {}

def analyze_brand_voice(url, api_key):
    """Analyze brand voice with proper error handling"""
    try:
        client = OpenAI(api_key=api_key)
        crawled_content = crawl_website(url, max_pages=1)
        
        if not crawled_content:
            st.error("No content found for brand analysis")
            return {}
            
        combined_text = "\n".join(
            [section['text'] for page in crawled_content.values() 
             for section in page][:2000]
        )
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{
                "role": "user",
                "content": f"""Analyze this content and return brand attributes in JSON:
                {combined_text}
                
                Output format:
                {{
                    "tone": "casual/professional",
                    "voice": "active/passive",
                    "sentence_structure": "simple/complex",
                    "content_type": "blog/commercial/technical",
                    "cta_style": "direct/indirect",
                    "keywords": ["list", "of", "keywords"]
                }}
                """
            }],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        st.error(f"Brand analysis error: {str(e)}")
        return {}

def generate_seo_assets(content, brand_style, api_key):
    """Generate SEO elements with validation"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"""Generate SEO assets for this content following {brand_style}:
                {content}
                
                Return JSON format:
                {{
                    "primary_keyword": "...",
                    "secondary_keywords": ["...", "..."],
                    "headings": ["...", "..."],
                    "content_brief": ["...", "...", "..."]
                }}
                """
            }],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate required keys
        required_keys = ['primary_keyword', 'secondary_keywords', 'headings', 'content_brief']
        if all(key in result for key in required_keys):
            return result
        else:
            st.error("Invalid SEO assets format")
            return {}
            
    except Exception as e:
        st.error(f"SEO generation failed: {str(e)}")
        return {}

def rewrite_content(content, brand_style, seo_data, api_key):
    """Rewrite content with brand alignment"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"""Rewrite this content following these guidelines:
                - Brand Style: {brand_style}
                - SEO Keywords: {seo_data.get('primary_keyword', '')}
                - Target Tone: {brand_style.get('tone', 'professional')}
                
                Original Content:
                {content}
                
                Include these headings: {seo_data.get('headings', [])}
                """
            }]
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        st.error(f"Content rewriting failed: {str(e)}")
        return content

def rewrite_cta(original_cta, brand_style, api_key):
    """Generate CTA variations safely"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"""Generate 3 CTA variations following {brand_style}:
                Original: {original_cta}
                
                Return JSON format:
                {{ "ctas": ["variation1", "variation2", "variation3"] }}
                """
            }],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('ctas', [original_cta])
        
    except Exception as e:
        st.error(f"CTA rewriting failed: {str(e)}")
        return [original_cta]

# ------ Streamlit UI ------
st.set_page_config(
    page_title="Content Optimizer Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")
    brand_url = st.text_input("Brand Reference URL", help="URL to analyze brand voice")
    
    if st.button("Analyze Brand Voice"):
        if not openai_key or not brand_url:
            st.error("Please provide API key and brand URL")
        else:
            with st.spinner("Analyzing brand voice..."):
                st.session_state.brand_style = analyze_brand_voice(brand_url, openai_key)
                
    if st.session_state.brand_style:
        st.divider()
        st.subheader("Detected Brand Style")
        st.json(st.session_state.brand_style)

# Main Interface
st.title("AI Content Optimizer Pro")
content = st.text_area("Input Content", height=200, placeholder="Paste your content here...")
cta_original = st.text_input("Original CTA", placeholder="e.g. Buy Now!")
optimize_cta = st.checkbox("Optimize CTAs", value=True)

if st.button("Generate Optimized Content"):
    if not openai_key or not content:
        st.error("Missing required fields: API key and content")
    else:
        with st.spinner("Optimizing content..."):
            # Generate SEO assets
            seo_data = generate_seo_assets(content, st.session_state.brand_style, openai_key)
            st.session_state.analysis_data = seo_data
            
            # Rewrite main content
            rewritten = rewrite_content(content, st.session_state.brand_style, seo_data, openai_key)
            st.session_state.rewritten_content = rewritten
            
            # Generate CTA variations
            if optimize_cta and cta_original:
                st.session_state.cta_variations = rewrite_cta(cta_original, st.session_state.brand_style, openai_key)

# Display Results
if st.session_state.rewritten_content:
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("SEO Assets")
        with st.container(border=True):
            if 'primary_keyword' in st.session_state.analysis_data:
                st.metric("Primary Keyword", st.session_state.analysis_data['primary_keyword'])
            if 'secondary_keywords' in st.session_state.analysis_data:
                st.write("**Secondary Keywords:**")
                st.write(", ".join(st.session_state.analysis_data['secondary_keywords']))
                
            st.divider()
            if 'headings' in st.session_state.analysis_data:
                st.write("**Recommended Structure:**")
                for heading in st.session_state.analysis_data['headings']:
                    st.write(f"- {heading}")
                    
            st.download_button(
                "Download Content Brief",
                "\n".join(st.session_state.analysis_data.get('content_brief', [])),
                file_name="content_brief.md"
            )
    
    with col2:
        st.subheader("Optimized Content")
        with st.container(border=True):
            st.markdown(st.session_state.rewritten_content)
            
            if optimize_cta and cta_original and 'cta_variations' in st.session_state:
                st.divider()
                st.subheader("CTA Variations")
                for idx, cta in enumerate(st.session_state.cta_variations, 1):
                    st.write(f"{idx}. {cta}")
            
            st.download_button(
                "Download Full Content",
                st.session_state.rewritten_content,
                file_name="optimized_content.md"
            )

st.markdown("---")
st.write("**Features:** Brand Voice Analysis | SEO Optimization | CTA Generation | Style Adaptation")
