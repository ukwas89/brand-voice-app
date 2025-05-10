# app.py
import streamlit as st
from openai import OpenAI
import os

def setup_openai():
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        st.error(f"API configuration error: {str(e)}")
        st.stop()

client = setup_openai()

def generate_content(keyword):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": """You are a senior UK immigration solicitor. Produce content that:
                 - Uses natural, human-like variations
                 - Avoids repetitive patterns
                 - Includes UK legal specifics
                 - Mixes sentence structures
                 - Adds relevant case examples"""},
                {"role": "user", "content": f"""Create a 700-word UK immigration blog post about {keyword} with:
                 1. Introduction linking to human rights
                 2. Legal framework (cite recent laws)
                 3. Application process steps
                 4. Common challenges
                 5. Real case study
                 6. FAQs
                 7. Conclusion with legal advice reminder"""}
            ],
            temperature=0.75,
            max_tokens=1800
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Content generation failed: {str(e)}")
        return None

def generate_cta(original_cta, blog_content):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Rewrite CTAs to sound more human and varied while keeping legal compliance."},
                {"role": "user", "content": f"""Original CTA: {original_cta}
                
                Blog context: {blog_content[:1000]}
                
                Create 3 variations that:
                - Use different verbs
                - Vary sentence starters
                - Include UK legal keywords
                - Avoid repetitive structures"""}
            ],
            temperature=0.65,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"CTA generation failed: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="UK Law Content Generator", layout="centered")
    
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    
    st.title("UK Immigration Content Generator")
    
    keyword = st.text_input("Enter legal topic keyword:", placeholder="E.g. 'Human Rights Application'")
    original_cta = st.text_area("Paste your original CTA:", height=100)
    
    if st.button("Generate Content"):
        if not keyword:
            st.warning("Please enter a keyword")
            return
            
        with st.spinner("Creating human-written style content..."):
            blog_content = generate_content(keyword)
            
            if blog_content:
                with st.expander("Generated Blog Content", expanded=True):
                    st.write(blog_content)
                
                if original_cta:
                    cta_options = generate_cta(original_cta, blog_content)
                    with st.expander("CTA Variations"):
                        st.write(cta_options if cta_options else "Couldn't generate CTAs")
                
                st.download_button(
                    label="Download Content",
                    data=blog_content,
                    file_name=f"{keyword.replace(' ', '_')}_content.md",
                    mime="text/markdown"
                )

if __name__ == "__main__":
    main()
