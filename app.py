# app.py
import os
import streamlit as st
from openai import OpenAI

# Constants
CTA = """<div class="cta-box">
<h3>Need Legal Assistance?</h3>
<p>Contact our Manchester experts today: <br>
📞 <strong>0161 464 4140</strong> <br>
📅 <a href="https://solicitorsinmanchester.co.uk/book-an-appointment/" target="_blank">Book Free Consultation</a></p>
</div>"""

# Configure OpenAI
def generate_content(keyword, content_type, creativity, heading_style, content_length, unique_content):
    """
    Generate SEO-optimized content with anti-AI measures
    """
    if not st.session_state.api_key:
        return "⚠️ Please enter a valid OpenAI API key in the sidebar"
    
    client = OpenAI(api_key=st.session_state.api_key)
    
    # Anti-AI prompt engineering
    uniqueness_rules = """
    - Use uncommon legal terminology specific to Manchester jurisdiction
    - Include regional case law examples
    - Vary sentence structure complexity
    - Apply British English spelling variations
    - Insert 2-3 unique analogies
    - Reference local Manchester legal procedures
    """ if unique_content else ""
    
    length_map = {
        "Short (300-500 words)": "500",
        "Medium (500-800 words)": "800", 
        "Long (800-1200 words)": "1200"
    }
    
    prompt = f"""
    Create {content_length} legal content about '{keyword}' for Manchester solicitors website. 
    Content type: {content_type}. Heading style: {heading_style}.
    
    Follow these strict rules:
    1. Use original phrasing never seen online
    2. Include 5-7 specific Manchester legal precedents
    3. Apply {heading_style} heading structure
    4. Use UK Legal Practice Guidelines
    5. Add 3 hypothetical client scenarios
    6. Include current year legal statistics {uniqueness_rules}
    7. Avoid typical AI patterns and transitions
    8. Use markdown formatting with:
       - <h2> for main headings  
       - <h3> for subheadings
       - Bullet points for lists
       - Bold key terms
    9. Maintain natural keyword density (1-2%)
    10. Insert 2-3 rhetorical questions
    
    Structure:
    - Introduction with client pain points
    - 5 key legal principles
    - Manchester-specific application
    - Client success story example
    - FAQ section with 3 questions
    - Conclusion with action incentive
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a Manchester legal expert with 20 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=creativity,
            max_tokens=4000,
            frequency_penalty=0.7,  # Reduce repetition
            presence_penalty=0.5    # Encourage novel concepts
        )
        content = response.choices[0].message.content
        return f"{content}\n{CTA}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="Legal Content Architect", page_icon="⚖️", layout="wide")

with st.sidebar:
    st.header("🔑 Configuration")
    st.session_state.api_key = st.text_input("OpenAI API Key:", type="password")
    content_type = st.selectbox("Content Type", ["Service Page", "Blog Post", "Case Study", "Landing Page", "FAQ Hub"])
    heading_style = st.selectbox("Heading Style", ["Professional", "Conversational", "Academic", "Client-Focused"])
    content_length = st.selectbox("Content Length", ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"])
    unique_content = st.checkbox("Enable Strict Uniqueness Mode", True)
    creativity = st.slider("Creativity Level", 0.0, 1.0, 0.3, help="Lower = More Factual, Higher = More Creative")

st.title("⚖️ Manchester Legal Content Generator")
st.markdown("""
<style>
.cta-box {
    border-left: 5px solid #2c3e50;
    padding: 1rem;
    margin: 2rem 0;
    background: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)

keyword = st.text_input("🔍 Primary Legal Keyword/Phrase", placeholder="Employment tribunal representation Manchester")
generate_btn = st.button("Generate Comprehensive Content")

if generate_btn:
    if not keyword:
        st.warning("Please enter a legal keyword/phrase")
    else:
        with st.spinner("🧠 Crafting 100% Unique Legal Content (This may take 60-90 seconds)..."):
            result = generate_content(
                keyword=keyword,
                content_type=content_type,
                creativity=creativity,
                heading_style=heading_style,
                content_length=content_length,
                unique_content=unique_content
            )
            
            st.markdown(result, unsafe_allow_html=True)
            st.success("✅ Content Generated! Next Steps:")
            st.markdown("""
            1. Run through [Originality.ai](https://originality.ai) plagiarism check
            2. Verify Manchester legal references
            3. Add firm-specific success metrics
            4. Check keyword density with [Ahrefs](https://ahrefs.com)
            5. Review with senior partner
            """)

st.markdown("---")
st.markdown(f"""
**Need Support?**  
📞 {PHONE} | 📅 [Book Strategy Session]({APPOINTMENT_URL})
""")
