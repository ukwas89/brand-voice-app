# app.py
import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_content(keyword):
    prompt = f"""
    Create a comprehensive 700-900 word professional legal blog post about '{keyword}' in UK immigration law,
    following this exact structure:

    1. Introduction (explain concept and human rights relevance)
    2. Legal Framework (cite UK laws: Human Rights Act 1998, Immigration Rules)
    3. Eligibility Criteria (bullet points with explanations)
    4. Application Process (step-by-step guide)
    5. Common Challenges (with practical examples)
    6. Case Study (realistic scenario with outcome)
    7. FAQs (5 questions with detailed answers)
    8. Conclusion (summary and importance of legal advice)

    Style Requirements:
    - Professional tone with accessible language
    - UK English spelling and legal terminology
    - Varied sentence structures
    - Natural paragraph transitions
    - Integrated statistics where appropriate
    - References to recent case law (2018-2023)
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a senior UK immigration solicitor with 20 years experience writing authoritative legal content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_cta(original_cta, blog_content):
    prompt = f"""
    Rewrite this Call-to-Action (CTA) while maintaining its core message:
    Original CTA: "{original_cta}"

    Requirements:
    - Align with this blog content: {blog_content[:1000]}...
    - Use different wording structure
    - Include urgency elements
    - Add UK legal specific references
    - Maintain professional tone
    - Keep under 150 words
    - Include natural language variations
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a legal marketing specialist expert in converting legal content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.set_page_config(page_title="UK Immigration Content Generator", layout="wide")
    
    st.title("🇬🇧 UK Immigration Content Generator")
    st.markdown("---")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        keyword = st.text_input("Enter legal topic keyword:", placeholder="e.g., Human Rights Application")
        original_cta = st.text_area("Paste your original CTA:", height=150)
        
        if st.button("Generate Content"):
            if not keyword:
                st.warning("Please enter a keyword")
                return
                
            with st.spinner("Generating professional content..."):
                blog_content = generate_content(keyword)
                cta_rewrite = generate_cta(original_cta, blog_content) if original_cta else "No CTA provided"
                
                st.session_state.blog_content = blog_content
                st.session_state.cta_rewrite = cta_rewrite
                
    with col2:
        if 'blog_content' in st.session_state:
            st.subheader("Generated Content")
            with st.expander("View Blog Content", expanded=True):
                st.write(st.session_state.blog_content)
                
            if st.session_state.cta_rewrite:
                st.markdown("---")
                st.subheader("Optimized CTA")
                with st.expander("View Rewritten CTA"):
                    st.write(st.session_state.cta_rewrite)
                    
                st.download_button(
                    label="Download Content",
                    data=f"{st.session_state.blog_content}\n\nCTA:\n{st.session_state.cta_rewrite}",
                    file_name=f"{keyword.replace(' ', '_')}_content.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()
