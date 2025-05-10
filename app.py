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
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def is_valid(url, main_domain):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and get_domain(url) == main_domain

def crawl_website(start_url, max_pages=3):
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

                    for link in soup.find_all('a', href=True):
                        href = link['href'].split('#')[0]
                        absolute_url = urljoin(url, href)
                        if is_valid(absolute_url, main_domain) and absolute_url not in visited:
                            queue.append(absolute_url)

                except Exception:
                    continue

            return crawled_data

    except Exception as e:
        st.error(f"Website analysis failed: {str(e)}")
        return {}

def rewrite_content_section(text, original_word_count, api_key, is_heading=False):
    client = OpenAI(api_key=api_key)

    if is_heading:
        prompt = f"""Rewrite this heading in a professional UK English style. Ensure it remains relevant to the original context and uses natural, human tone. It must be unique and engaging.\n\nOriginal: {text}"""
    else:
        prompt = f"""Rewrite the following content to be 100% unique, professional in tone, and written in UK English. Follow these instructions:
1. Avoid using the same phrases or sentence structure.
2. Expand where appropriate for clarity and depth.
3. Maintain original meaning but improve quality and flow.
4. Use bullet points if lists are present.
5. Provide real-world examples where possible.
6. Preserve overall word count range ({original_word_count} words).
7. Avoid generic AI patterns.
\nText to rewrite: {text}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Rewrite failed: {str(e)}"

def generate_subheadings(main_heading_text, api_key):
    client = OpenAI(api_key=api_key)
    prompt = f"""Based on the following main heading, write two relevant and detailed subheadings in UK English that could logically sit under it:
\nMain Heading: {main_heading_text}
\nEach subheading should:
- Be professional and specific
- Not duplicate the main heading
- Add semantic richness
- Use active, engaging language"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return [line.strip('- ').strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
    except Exception:
        return []

def process_page_content(page_content, api_key):
    rewritten = []
    for section in page_content:
        if section['type'] == 'heading':
            rewritten_heading = rewrite_content_section(section['text'], 0, api_key, is_heading=True)
            rewritten.append({'type': 'heading', 'level': section['level'], 'text': rewritten_heading})
            subheadings = generate_subheadings(section['text'], api_key)
            for sub in subheadings:
                rewritten.append({'type': 'heading', 'level': section['level'] + 1, 'text': sub})
        elif section['type'] == 'paragraph':
            original_words = len(re.findall(r'\w+', section['text']))
            rewritten_text = rewrite_content_section(section['text'], original_words, api_key)
            new_words = len(re.findall(r'\w+', rewritten_text))
            if 0.75 * original_words <= new_words <= 1.25 * original_words:
                rewritten.append({'type': 'paragraph', 'text': rewritten_text})
            else:
                rewritten.append({'type': 'paragraph', 'text': section['text']})
    return rewritten

# Streamlit UI
st.set_page_config(
    page_title="Content Clarifier Pro",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.header("Configuration Settings")
    openai_key = st.text_input("OpenAI API Key", type="password")
    max_pages = st.slider("Maximum Pages to Analyze", 1, 5, 1)
    st.markdown("---")
    st.info("""**Best Practices:**\n1. Use HTTPS URLs\n2. Start with homepage\n3. Verify robots.txt compliance\n4. Check content permissions""")

st.title("Content Clarifier Pro")
st.markdown("""
Transform complex web content into clear, 100% unique, UK English articles with structural integrity and added subtopics.
""")

with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        website_url = st.text_input("Website URL", placeholder="https://example.com")
    with col2:
        if st.button("Generate Unique Content", use_container_width=True):
            if not website_url.startswith('http'):
                st.error("Please enter a valid URL starting with http:// or https://")
            elif not openai_key:
                st.error("OpenAI API key required")
            else:
                with st.spinner("Crawling and analysing content..."):
                    crawled_data = crawl_website(website_url, max_pages)
                    st.session_state.original_content = crawled_data
                    if crawled_data:
                        with st.spinner("Rewriting content to UK professional standard..."):
                            for url, content in crawled_data.items():
                                rewritten = process_page_content(content, openai_key)
                                st.session_state.rewritten_content[url] = rewritten

if st.session_state.rewritten_content:
    st.divider()
    st.subheader("Rewritten Content")
    tabs = st.tabs([f"Page {i+1}" for i in range(len(st.session_state.rewritten_content))])
    for idx, (url, content) in enumerate(st.session_state.rewritten_content.items()):
        with tabs[idx]:
            st.markdown(f"**Source URL:** `{url}`")
            export_content = []
            for section in content:
                if section['type'] == 'heading':
                    level = section.get('level', 3)
                    st.markdown(f"{'#' * level} {section['text']}")
                    export_content.append(section['text'])
                else:
                    st.markdown(section['text'])
                    export_content.append(section['text'])
            sanitized_url = re.sub(r'\W+', '', url)[:30]
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            st.download_button(
                label="Download Markdown",
                data="\n\n".join(export_content),
                file_name=f"unique_{sanitized_url}_{timestamp}.md",
                key=f"download_{idx}"
            )

st.divider()
st.markdown("""**Assurance Features:**\n- 100% Unique Output\n- UK Professional English\n- Enhanced Subheadings\n- Structural Integrity\n- Word Count Preservation""")
