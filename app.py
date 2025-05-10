import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import tldextract
from openai import OpenAI
from datetime import datetime

# Initialize session states
if 'brand_style' not in st.session_state:
    st.session_state.brand_style = {}
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

def analyze_brand_voice(url, api_key):
    """Analyze brand voice from existing content"""
    client = OpenAI(api_key=api_key)
    
    try:
        # Crawl brand website
        crawled_content = crawl_website(url, max_pages=1)
        combined_text = "\n".join([section['text'] for page in crawled_content.values() for section in page][:2000])
        
        prompt = f"""Analyze this content and return brand style attributes:
        
        {combined_text}
        
        Return JSON format with:
        - tone (casual/professional/friendly/technical)
        - voice (first-person/third-person/active/passive)
        - sentence_structure (simple/complex)
        - common_phrases (list)
        - content_type (blog/commercial/technical/docs)
        - cta_style (direct/indirect)
        - keywords (list)
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return eval(response.choices[0].message.content)
    
    except Exception as e:
        st.error(f"Brand analysis failed: {str(e)}")
        return {}

def generate_seo_assets(content, brand_style, api_key):
    """Generate SEO elements with brand alignment"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Generate SEO assets for this content following brand guidelines:
    
    Brand Style: {brand_style}
    Content: {content}
    
    Return JSON with:
    - primary_keyword
    - secondary_keywords (list)
    - headings (h1-h3 list)
    - content_brief (3 bullet points)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return eval(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def rewrite_cta(original_cta, brand_style, api_key):
    """Rewrite CTA based on brand voice"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Rewrite this CTA following brand guidelines:
    
    Brand Style: {brand_style}
    Original CTA: {original_cta}
    
    Return 3 variations as JSON list in 'ctas' key"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return eval(response.choices[0].message.content)['ctas']
    except Exception as e:
        return [original_cta]

# Streamlit UI Configuration
st.set_page_config(
    page_title="AI Content Optimizer Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Configuration
with st.sidebar:
    st.header("Brand Configuration")
    with st.container(border=True):
        openai_key = st.text_input("OpenAI API Key", type="password")
        brand_url = st.text_input("Brand Reference URL", help="URL to analyze brand voice/style")
        if st.button("Analyze Brand Voice"):
            if brand_url and openai_key:
                with st.spinner("Analyzing brand voice..."):
                    st.session_state.brand_style = analyze_brand_voice(brand_url, openai_key)
            else:
                st.error("Please provide both API key and brand URL")

    if st.session_state.brand_style:
        st.divider()
        st.subheader("Detected Brand Style")
        st.json(st.session_state.brand_style)

# Main Interface
st.title("AI Content Optimizer Pro")
st.markdown("""
    Advanced content optimization with brand voice alignment and SEO enhancements
    """)

# Content Input Section
with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        content = st.text_area("Input Content", height=200, 
                             placeholder="Paste content to optimize...")
    with col2:
        cta_original = st.text_input("Original CTA", 
                                    placeholder="e.g. Buy Now!")
        optimize_cta = st.checkbox("Rewrite CTAs", value=True)

if content and st.button("Generate Optimized Content"):
    if not openai_key:
        st.error("OpenAI API key required")
    else:
        with st.spinner("Processing content..."):
            # Generate SEO assets
            seo_data = generate_seo_assets(content, st.session_state.brand_style, openai_key)
            st.session_state.analysis_data = seo_data
            
            # Rewrite content
            client = OpenAI(api_key=openai_key)
            prompt = f"""Rewrite this content maintaining brand voice and SEO elements:
            
            Brand Style: {st.session_state.brand_style}
            SEO Guidelines: {seo_data}
            Original Content: {content}
            
            Output Requirements:
            - Use {st.session_state.brand_style.get('tone', 'professional')} tone
            - Follow {st.session_state.brand_style.get('voice', 'active')} voice
            - Include primary keyword: {seo_data.get('primary_keyword', '')}
            - Maintain {st.session_state.brand_style.get('sentence_structure', 'simple')} sentences
            """
            
            rewritten = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
            
            st.session_state.rewritten_content = rewritten

# Results Display
if 'rewritten_content' in st.session_state:
    st.divider()
    
    # SEO Assets Column
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("SEO Assets")
        with st.container(border=True):
            st.markdown(f"**Primary Keyword:** `{st.session_state.analysis_data.get('primary_keyword', '')}`")
            st.markdown("**Secondary Keywords:**")
            st.write(", ".join(st.session_state.analysis_data.get('secondary_keywords', [])))
            
            st.divider()
            st.markdown("**Content Structure**")
            for heading in st.session_state.analysis_data.get('headings', []):
                st.write(f"- {heading}")
                
            st.download_button(
                "Download Content Brief",
                "\n".join(st.session_state.analysis_data.get('content_brief', [])),
                file_name="content_brief.md"
            )
    
    # Main Content Column        
    with col2:
        st.subheader("Optimized Content")
        with st.container(border=True):
            st.markdown(st.session_state.rewritten_content)
            
            if optimize_cta and cta_original:
                st.divider()
                st.subheader("CTA Variations")
                ctas = rewrite_cta(cta_original, st.session_state.brand_style, openai_key)
                for i, cta in enumerate(ctas, 1):
                    st.write(f"{i}. {cta}")
            
            st.download_button(
                "Download Full Content",
                st.session_state.rewritten_content,
                file_name="optimized_content.md"
            )

st.divider()
st.markdown("""
    **Features Included:**
    - Brand Voice Analysis
    - SEO Keyword Extraction
    - Content Structure Generation
    - CTA Optimization
    - Tone & Style Adaptation
    - Content Brief Generation
    """)
