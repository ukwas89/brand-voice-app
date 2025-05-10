# app.py
import os
import streamlit as st
from openai import OpenAI

# Constants
CTA = "\n\n[Contact us today at 0161 464 4140 or book your consultation online](https://solicitorsinmanchester.co.uk/book-an-appointment/)"
PHONE = "0161 464 4140"
APPOINTMENT_URL = "https://solicitorsinmanchester.co.uk/book-an-appointment/"

# Streamlit UI
st.set_page_config(page_title="Legal Content Generator", page_icon="⚖️")

st.title("⚖️ Manchester Solicitors Content Generator")
st.markdown("Create professional legal content with integrated CTAs")

with st.sidebar:
    st.header("Configuration")
    # API Key Input
    api_key = st.text_input("Enter OpenAI API Key:", 
                          type="password",
                          help="Get your API key from https://platform.openai.com/account/api-keys")
    
    content_type = st.selectbox(
        "Content Type",
        ("Service Page", "Blog Post", "FAQ Section", "Landing Page")
    )
    creativity = st.slider("Creativity Level", 0.0, 1.0, 0.5)

def generate_content(keyword, content_type, creativity):
    """
    Generate SEO-optimized content using OpenAI API
    """
    if not api_key:
        return "Please enter a valid OpenAI API key in the sidebar"
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Create professional legal content about {keyword} for a solicitor's website in Manchester. 
    Content type: {content_type}. Follow these guidelines:
    - Use UK English legal terminology
    - Avoid AI-generated patterns
    - Include natural keyword placement
    - Structure with clear headings
    - Focus on client benefits
    - Maintain authoritative tone
    - Include 3-5 key points
    
    Wrap the content in proper HTML formatting without <html> tags.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal content writer for UK solicitors."},
                {"role": "user", "content": prompt}
            ],
            temperature=creativity,
            max_tokens=2000
        )
        content = response.choices[0].message.content
        return f"{content}\n\n{CTA}"
    except Exception as e:
        return f"Error generating content: {str(e)}"

keyword = st.text_input("Primary Keyword", placeholder="Employment law advice")
generate_button = st.button("Generate Content")

if generate_button and keyword:
    with st.spinner("Generating professional content..."):
        generated_content = generate_content(keyword, content_type, creativity)
        st.markdown(generated_content, unsafe_allow_html=True)
        
        st.success("Content generated! Remember to:")
        st.markdown("1. Review for accuracy\n2. Add specific case examples\n3. Verify legal references")
elif generate_button:
    st.warning("Please enter a keyword to generate content")

st.markdown("---")
st.markdown(f"**Need help?** Call {PHONE} or [book online]({APPOINTMENT_URL})")
