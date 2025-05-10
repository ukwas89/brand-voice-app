import streamlit as st
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import openai
from collections import deque
import tldextract

# Initialize session state
if 'style_guide' not in st.session_state:
    st.session_state.style_guide = None
if 'crawled_urls' not in st.session_state:
    st.session_state.crawled_urls = []

def crawl_website(base_url, max_pages=10):
    """Crawl website starting from base URL"""
    try:
        domain = tldextract.extract(base_url).registered_domain
        visited = set()
        queue = deque([base_url])
        pages_crawled = 0
        urls = []

        while queue and pages_crawled < max_pages:
            url = queue.popleft()
            
            if url in visited:
                continue
                
            try:
                response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Add to crawled URLs
                urls.append(url)
                pages_crawled += 1
                visited.add(url)
                
                # Extract all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    if tldextract.extract(full_url).registered_domain == domain:
                        if full_url not in visited:
                            queue.append(full_url)
                            
            except Exception as e:
                continue
                
        return urls

    except Exception as e:
        st.error(f"Crawling failed: {str(e)}")
        return []

def analyze_content(urls):
    """Analyze website content and create style guide"""
    all_content = []
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
                
            main_content = soup.find('main') or soup.body
            text = main_content.get_text(separator=' ', strip=True)[:2000]  # Limit text length
            all_content.append(f"URL: {url}\nCONTENT: {text}")
        except Exception as e:
            st.warning(f"Couldn't process {url}: {str(e)}")
    
    if not all_content:
        return None
        
    prompt = f"""Analyze this website content and create detailed brand guidelines covering these aspects:
    1. Brand Voice (casual/formal, humorous/serious, emotional/rational)
    2. Tone Preferences (authoritative, conversational, technical)
    3. Sentence Structure (short vs long sentences, active/passive voice)
    4. Vocabulary (industry-specific terms, simple/complex words)
    5. Content Organization (section patterns, heading styles)
    6. Frequently Addressed Topics
    
    Content samples:
    {" ".join(all_content)}
    
    Format the output in clear markdown sections with bullet points."""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=st.secrets.get("OPENAI_API_KEY", openai.api_key)
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None

def generate_content(topic):
    """Generate content using brand voice"""
    if not st.session_state.style_guide:
        return "No style guide available"
        
    prompt = f"""Write a comprehensive article about: {topic}
    
    Strictly follow these brand guidelines:
    {st.session_state.style_guide}
    
    Structure requirements:
    - SEO-friendly title
    - Introduction with hook
    - 3-5 sections with H2 headings
    - Bullet points where appropriate
    - Real-world examples
    - Actionable conclusion
    - Natural keyword integration"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=st.secrets.get("OPENAI_API_KEY", openai.api_key)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Generation failed: {str(e)}"

# Streamlit UI Configuration
st.set_page_config(page_title="Brand Voice Trainer", layout="wide")

# Sidebar for API Configuration
with st.sidebar:
    st.header("🔑 API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")

# Main Interface
st.title("🎯 Website Brand Voice Trainer")
st.markdown("Enter your website URL to analyze its content style and generate on-brand content")

# Training Section
st.subheader("1. Train on Website Content")
website_url = st.text_input(
    "Enter Website URL", 
    placeholder="https://example.com",
    help="Homepage URL of the website to analyze"
)

if st.button("Analyze Brand Voice"):
    if not website_url.startswith('http'):
        st.error("Please enter a valid URL starting with http:// or https://")
    elif not openai_key:
        st.error("OpenAI API key required")
    else:
        openai.api_key = openai_key
        with st.spinner("🕷️ Crawling website (this may take a minute)..."):
            urls = crawl_website(website_url)
            if urls:
                st.session_state.crawled_urls = urls
                st.info(f"Crawled {len(urls)} pages: {', '.join(urls[:3])}...")
                
                with st.spinner("🧠 Analyzing content style..."):
                    st.session_state.style_guide = analyze_content(urls)
                    if st.session_state.style_guide:
                        st.success("Brand voice analysis complete!")
                        st.expander("View Style Guide").write(st.session_state.style_guide)

# Content Generation Section
if st.session_state.style_guide:
    st.subheader("2. Generate On-Brand Content")
    topic = st.text_input("Content Topic", placeholder="How to create effective content strategies")
    
    if st.button("Generate Content"):
        with st.spinner("✍️ Writing in brand voice..."):
            content = generate_content(topic)
            st.subheader("Generated Content")
            st.markdown(content)
            st.download_button("Download Content", content, file_name="brand_content.md")

st.markdown("---")
st.info("Note: This version crawls up to 10 pages from the website homepage. For better results, ensure your website has substantial text content.")
