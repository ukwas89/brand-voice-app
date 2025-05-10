import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import tldextract
from openai import OpenAI

# Initialize session state
if 'style_guide' not in st.session_state:
    st.session_state.style_guide = None
if 'crawled_urls' not in st.session_state:
    st.session_state.crawled_urls = []

def get_domain(url):
    """Extract main domain from URL"""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def is_valid(url, main_domain):
    """Check if URL belongs to same domain and is valid"""
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and get_domain(url) == main_domain

def crawl_website(start_url, max_pages=10):
    """Crawl website starting from given URL"""
    try:
        main_domain = get_domain(start_url)
        visited = set()
        queue = deque([start_url])
        crawled_urls = []
        
        while queue and len(crawled_urls) < max_pages:
            url = queue.popleft()
            
            if url in visited:
                continue
                
            try:
                response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                crawled_urls.append(url)
                visited.add(url)
                
                # Find all links on page
                for link in soup.find_all('a', href=True):
                    href = link['href'].split('#')[0]  # Remove fragments
                    absolute_url = urljoin(url, href)
                    if is_valid(absolute_url, main_domain) and absolute_url not in visited:
                        queue.append(absolute_url)
                        
            except Exception as e:
                continue
                
        return crawled_urls
    
    except Exception as e:
        st.error(f"Crawling error: {str(e)}")
        return []

def clean_content(html):
    """Clean HTML content for analysis"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'form', 'iframe']):
        element.decompose()
        
    # Get main content or fallback to body
    main_content = soup.find('main') or soup.find('article') or soup.body
    
    # Clean text
    text = main_content.get_text(separator='\n', strip=True)
    return ' '.join(text.split()[:1500])  # Limit to 1500 words

def analyze_brand_voice(urls, api_key):
    """Analyze website content to create brand voice profile"""
    client = OpenAI(api_key=api_key)
    content_samples = []
    
    for url in urls:
        try:
            response = requests.get(url, timeout=15)
            cleaned_text = clean_content(response.text)
            content_samples.append(f"URL: {url}\nCONTENT: {cleaned_text}\n")
        except Exception as e:
            st.warning(f"Couldn't process {url}: {str(e)}")
    
    if not content_samples:
        return None
        
    analysis_prompt = f"""Analyze the following website content to create detailed brand guidelines:

{''.join(content_samples)}

Create a comprehensive brand voice profile covering:
1. Tone (formal/informal, serious/playful)
2. Style (technical/conversational)
3. Vocabulary (simple/complex, industry jargon)
4. Sentence structure (short/long sentences)
5. Content organization (section patterns)
6. Target audience perception
7. Frequently used phrases/words

Present the analysis in clear markdown format with section headers."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None

def generate_content(topic, api_key):
    """Generate content using brand voice"""
    client = OpenAI(api_key=api_key)
    if not st.session_state.style_guide:
        return "No brand voice profile available"
        
    prompt = f"""Write content about: {topic}

Strictly follow these brand guidelines:
{st.session_state.style_guide}

Include:
- SEO-optimized title
- Engaging introduction
- 3-5 subheadings with detailed content
- Bullet points where appropriate
- Real-world examples
- Natural keyword integration
- Conclusion with key takeaways"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Generation failed: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="Brand Voice Trainer", layout="wide")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")
    max_pages = st.slider("Max Pages to Crawl", 3, 15, 5)

# Main Interface
st.title("🚀 Website Brand Voice Trainer")
st.markdown("Analyze any website's content style and generate on-brand content")

# Training Section
website_url = st.text_input(
    "Enter Website URL", 
    placeholder="https://example.com",
    help="Start with homepage URL"
)

if st.button("Analyze Brand Voice"):
    if not website_url.startswith('http'):
        st.error("Please enter valid URL (http:// or https://)")
    elif not openai_key:
        st.error("OpenAI API key required")
    else:        
        with st.spinner(f"🕸️ Crawling website (max {max_pages} pages)..."):
            crawled_urls = crawl_website(website_url, max_pages)
            st.session_state.crawled_urls = crawled_urls
            
            if crawled_urls:
                st.info(f"Successfully crawled {len(crawled_urls)} pages")
                with st.expander("Show Crawled URLs"):
                    st.write(crawled_urls)
                
                with st.spinner("🔍 Analyzing content style..."):
                    st.session_state.style_guide = analyze_brand_voice(crawled_urls, openai_key)
                    if st.session_state.style_guide:
                        st.success("Brand voice profile created!")
                        st.expander("View Brand Guidelines").markdown(st.session_state.style_guide)

# Content Generation
if st.session_state.style_guide:
    st.markdown("---")
    st.subheader("Content Generator")
    
    topic = st.text_input("Enter content topic", 
                        placeholder="How to create effective content strategies")
    
    if st.button("Generate Content"):
        with st.spinner("✍️ Writing in brand voice..."):
            content = generate_content(topic, openai_key)
            st.markdown("---")
            st.subheader("Generated Content")
            st.markdown(content)
            st.download_button("Download Content", content, 
                             file_name="generated_content.md",
                             help="Download in Markdown format")

st.markdown("---")
st.info("💡 Tip: For best results, use websites with substantial text content (blogs, documentation, marketing sites)")
