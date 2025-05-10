# app.py
import streamlit as st
from openai import OpenAI
import os

def generate_content(api_key, keyword):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": """You are a senior UK immigration solicitor. Create content that:
                 - Uses natural, human-like English
                 - Avoids AI patterns
                 - Includes UK legal references
                 - Contains practical examples"""},
                {"role": "user", "content": f"""Create a professional blog post about {keyword} covering:
                 1. Introduction (human rights context)
                 2. Legal basis (UK laws)
                 3. Application process
                 4. Common issues
                 5. Case study example
                 6. FAQs
                 7. Conclusion with legal advice"""}
            ],
            temperature=0.7,
            max_tokens=1800
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Content generation failed: {str(e)}")
        return None

def generate_cta(api_key, original_cta, blog_content):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Create 3 human-written CTA variations that align with legal content."},
                {"role": "user", "content": f"""Original CTA: {original_cta}
                
                Blog context: {blog_content[:1000]}
                
                Generate CTAs that:
                - Vary sentence structure
                - Use active language
                - Include UK legal terms
                - Sound natural"""}
            ],
            temperature=0.6,
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"CTA generation failed: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="UK Immigration Content Generator", layout="centered")
    
    st.sidebar.title("API Configuration")
    api_key = st.sidebar.text_input("Enter OpenAI API Key:", 
                                  type="password",
                                  help="Get your API key from https://platform.openai.com/account/api-keys")
    
    st.title("🇬🇧 AI Legal Content Generator")
    st.markdown("---")
    
    keyword = st.text_input("Legal Topic Keyword:", placeholder="E.g. 'Human Rights Application'")
    original_cta = st.text_area("Your Existing CTA:", height=100)
    
    if st.button("Generate Content"):
        if not api_key:
            st.error("Please enter a valid OpenAI API key")
            return
        if not keyword:
            st.error("Please enter a legal topic keyword")
            return
            
        with st.spinner("Creating professional content..."):
            blog_content = generate_content(api_key, keyword)
            
            if blog_content:
                with st.expander("Generated Blog Content", expanded=True):
                    st.markdown(blog_content)
                
                if original_cta:
                    cta_variations = generate_cta(api_key, original_cta, blog_content)
                    with st.expander("CTA Variations", expanded=True):
                        st.markdown(cta_variations if cta_variations else "Error generating CTAs")
                
                st.download_button(
                    label="Download Content",
                    data=f"{blog_content}\n\n---\nCTA Options:\n{cta_variations if cta_variations else ''}",
                    file_name=f"{keyword.replace(' ', '_')}_content.md",
                    mime="text/markdown"
                )

if __name__ == "__main__":
    main()
