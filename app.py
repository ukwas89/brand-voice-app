import streamlit as st
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import openai
import serpapi

# Initialize session state
if 'style_guide' not in st.session_state:
    st.session_state.style_guide = None

def process_sitemap(sitemap_url):
    """Extract URLs from sitemap.xml"""
    try:
        response = requests.get(sitemap_url)
        root = ET.fromstring(response.content)
        return [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except Exception as e:
        st.error(f"Error processing sitemap: {str(e)}")
        return []

def analyze_content(urls):
    """Analyze website content and create style guide"""
    all_content = []
    for url in urls[:5]:  # Limit to first 5 pages for demo
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('main') or soup.body
            all_content.append(main_content.get_text()[:2000])
        except Exception as e:
            st.warning(f"Couldn't process {url}: {str(e)}")
    
    if not all_content:
        return None
        
    prompt = f"""Analyze this content and create detailed style guidelines covering:
    - Brand voice characteristics
    - Tone preferences
    - Writing style
    - Content structure preferences
    - Any specific linguistic patterns
    
    Content samples:
    {" ".join(all_content)}"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        api_key=st.secrets["OPENAI_API_KEY"]
    )
    return response.choices[0].message.content

def generate_content(topic, serp_analysis=None):
    """Generate content using brand voice"""
    prompt = f"""Write a comprehensive article about: {topic}
    
    Style Guidelines:
    {st.session_state.style_guide}
    
    {f"SERP Analysis Insights: {serp_analysis}" if serp_analysis else ""}
    
    Structure the content with:
    - Engaging introduction
    - 3-5 main sections with subheadings
    - Practical examples
    - Conclusion with key takeaways"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        api_key=st.secrets["OPENAI_API_KEY"]
    )
    return response.choices[0].message.content

def analyze_serp(keyword):
    """Analyze search results intent"""
    client = serpapi.Client(api_key=st.secrets["SERPAPI_KEY"])
    results = client.search({
        'q': keyword,
        'engine': 'google',
        'num': 10
    })
    
    analysis_prompt = f"""Analyze these search results for keyword '{keyword}':
    {results['organic_results']}
    
    Identify:
    1. Dominant search intent
    2. Common content patterns
    3. Recommended structure
    4. Missing content opportunities"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": analysis_prompt}],
        api_key=st.secrets["OPENAI_API_KEY"]
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("Brand Voice Content Generator 🚀")

# Sidebar for configuration
with st.sidebar:
    st.header("API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SERP API Key", type="password")
    
    if openai_key:
        openai.api_key = openai_key
    if serpapi_key:
        serpapi.api_key = serpapi_key

# Main workflow
tab1, tab2, tab3 = st.tabs(["Train Brand Voice", "Generate Content", "SERP Analysis"])

with tab1:
    st.subheader("Train Brand Voice")
    sitemap_url = st.text_input("Enter Website Sitemap URL")
    
    if st.button("Analyze Brand Voice"):
        with st.spinner("Processing sitemap and analyzing content..."):
            urls = process_sitemap(sitemap_url)
            if urls:
                st.session_state.style_guide = analyze_content(urls)
                st.success("Brand voice analysis completed!")
                st.expander("View Style Guide").write(st.session_state.style_guide)

with tab2:
    st.subheader("Generate Content")
    topic = st.text_input("Enter Content Topic")
    
    if st.button("Create Content"):
        if not st.session_state.style_guide:
            st.warning("Please train brand voice first!")
        else:
            with st.spinner("Generating content..."):
                content = generate_content(topic)
                st.subheader("Generated Content")
                st.write(content)
                st.download_button("Download Content", content, file_name="generated_content.md")

with tab3:
    st.subheader("SERP Intent Analysis")
    keyword = st.text_input("Enter Keyword")
    
    if st.button("Analyze SERP"):
        with st.spinner("Analyzing search results..."):
            analysis = analyze_serp(keyword)
            st.subheader("Analysis Results")
            st.write(analysis)

st.markdown("---")
st.info("Note: This is a demo version. Processing limited to 5 pages for analysis.")
