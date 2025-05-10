import streamlit as st
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import openai
import serpapi
from io import BytesIO

# Initialize session state
if 'style_guide' not in st.session_state:
    st.session_state.style_guide = None
if 'cached_urls' not in st.session_state:
    st.session_state.cached_urls = []

def process_sitemap(sitemap_url):
    """Extract URLs from sitemap.xml with enhanced error handling"""
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        # Validate content type
        if 'xml' not in response.headers.get('Content-Type', '').lower():
            st.error("URL doesn't return XML content. Are you sure this is a sitemap?")
            return []

        # Handle encoding
        response.encoding = 'utf-8'
        content = response.text
        
        # Register namespaces
        namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }
        
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            # Try parsing with lxml for malformed XML
            from lxml import etree
            parser = etree.XMLParser(recover=True)
            root = etree.parse(BytesIO(response.content), parser)

        urls = []
        
        # Check if sitemap index
        if 'sitemapindex' in root.tag:
            for sitemap in root.findall('ns:sitemap', namespaces):
                loc = sitemap.find('ns:loc', namespaces)
                if loc is not None and loc.text:
                    urls += process_sitemap(loc.text)
        else:
            for url in root.findall('ns:url', namespaces):
                loc = url.find('ns:loc', namespaces)
                if loc is not None and loc.text:
                    urls.append(loc.text)

        return list(set(urls))  # Remove duplicates

    except Exception as e:
        st.error(f"Error processing sitemap: {str(e)}")
        if 'response' in locals():
            st.markdown(f"**First 200 characters received:**\n`{content[:200]}...`")
        return []

def analyze_content(urls):
    """Analyze website content and create style guide"""
    all_content = []
    max_pages = 5  # Limit for demo purposes
    
    for url in urls[:max_pages]:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
                
            main_content = soup.find('main') or soup.body
            text = main_content.get_text(separator=' ', strip=True)[:2000]  # Limit text length
            all_content.append(f"URL: {url}\nCONTENT: {text}")
        except Exception as e:
            st.warning(f"Couldn't process {url}: {str(e)}")
    
    if not all_content:
        return None
        
    prompt = f"""Analyze this content and create detailed style guidelines covering:
    - Brand voice characteristics (casual/formal, humorous/serious)
    - Tone preferences (authoritative, conversational, technical)
    - Sentence structure preferences
    - Frequently used vocabulary
    - Content organization patterns
    
    Content samples:
    {" ".join(all_content)}"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=st.secrets.get("OPENAI_API_KEY", openai.api_key)
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API error: {str(e)}")
        return None

def generate_content(topic, serp_analysis=None):
    """Generate content using brand voice"""
    if not st.session_state.style_guide:
        return "No style guide available"
        
    prompt = f"""Write a comprehensive article about: {topic}
    
    Style Guidelines:
    {st.session_state.style_guide}
    
    {f"SERP Analysis Insights: {serp_analysis}" if serp_analysis else ""}
    
    Structure the content with:
    - Engaging introduction
    - 3-5 main sections with subheadings (##)
    - Bullet points where appropriate
    - Real-world examples
    - Actionable conclusion"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=st.secrets.get("OPENAI_API_KEY", openai.api_key)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Content generation failed: {str(e)}"

def analyze_serp(keyword):
    """Analyze search results intent"""
    try:
        client = serpapi.Client(api_key=st.secrets.get("SERPAPI_KEY", serpapi.api_key))
        results = client.search({
            'q': keyword,
            'engine': 'google',
            'num': 5  # Limit to 5 results for demo
        })
        
        analysis_prompt = f"""Analyze these search results for '{keyword}':
        {results.get('organic_results', [])}
        
        Provide insights on:
        1. Search intent classification
        2. Content gaps in current top results
        3. Recommended content structure
        4. Optimal content length
        5. Semantic keywords to include"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": analysis_prompt}],
            api_key=st.secrets.get("OPENAI_API_KEY", openai.api_key)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"SERP analysis failed: {str(e)}"

# Streamlit UI Configuration
st.set_page_config(page_title="Brand Voice Generator", layout="wide")

# Sidebar for API Configuration
with st.sidebar:
    st.header("🔑 API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Get from https://platform.openai.com/api-keys")
    serpapi_key = st.text_input("SERP API Key", type="password", help="Get from https://serpapi.com/dashboard")
    
    if openai_key:
        openai.api_key = openai_key
    if serpapi_key:
        serpapi.api_key = serpapi_key

# Main Interface
st.title("🚀 AI Content Generator with Brand Voice")
st.markdown("""
    *Train an AI model on your website's content style, then generate new content that matches your brand voice.*
    """)

# Tab Interface
tab1, tab2, tab3 = st.tabs(["🏋️ Train Brand Voice", "✍️ Generate Content", "🔍 SERP Analysis"])

with tab1:
    st.subheader("Train on Your Website Content")
    sitemap_url = st.text_input(
        "Enter Sitemap URL", 
        placeholder="https://example.com/sitemap.xml",
        help="Should be a direct link to XML sitemap"
    )
    
    if st.button("Analyze Brand Style"):
        if not sitemap_url.startswith('http'):
            st.error("Please enter a valid URL starting with http:// or https://")
        elif not openai.api_key:
            st.error("OpenAI API key required")
        else:
            with st.spinner("🕵️ Discovering URLs..."):
                urls = process_sitemap(sitemap_url)
                st.session_state.cached_urls = urls
                
                if urls:
                    st.info(f"Found {len(urls)} URLs in sitemap")
                    with st.expander("Show First 10 URLs"):
                        st.write(urls[:10])
                    
                    with st.spinner("📖 Analyzing Content Style..."):
                        st.session_state.style_guide = analyze_content(urls)
                        if st.session_state.style_guide:
                            st.success("Style Guide Created!")
                            st.expander("View Full Style Guide").write(st.session_state.style_guide)

with tab2:
    st.subheader("Create New Content")
    topic = st.text_input("Content Topic", placeholder="Content marketing strategies for SaaS")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Content"):
            if not topic:
                st.warning("Please enter a topic")
            elif not st.session_state.style_guide:
                st.warning("Please train brand voice first!")
            else:
                with st.spinner("🧠 Generating Content..."):
                    content = generate_content(topic)
                    st.subheader("Generated Content")
                    st.write(content)
                    st.download_button("Download Content", content, file_name="content.md")
    
    with col2:
        if st.session_state.style_guide:
            st.subheader("Current Style Guide")
            st.write(st.session_state.style_guide[:500] + "...")

with tab3:
    st.subheader("Analyze Search Intent")
    keyword = st.text_input("Keyword to Analyze", placeholder="best content marketing tools")
    
    if st.button("Run SERP Analysis"):
        if not keyword:
            st.warning("Please enter a keyword")
        elif not serpapi.api_key:
            st.error("SERP API key required")
        else:
            with st.spinner("🔎 Analyzing Search Results..."):
                analysis = analyze_serp(keyword)
                st.subheader("Analysis Results")
                st.write(analysis)

st.markdown("---")
st.info("💡 Tip: Start with a valid sitemap URL (e.g., https://www.sitemaps.org/sitemap.xml) for testing")
