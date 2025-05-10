# app.py
import streamlit as st
from openai import OpenAI

# Constants
PHONE = "0161 464 4140"
APPOINTMENT_URL = "https://solicitorsinmanchester.co.uk/book-an-appointment/"
CTA = f"""<div class="cta-box">
<h3>Need Legal Assistance?</h3>
<p>Contact our Manchester experts today: <br>
📞 <strong>{PHONE}</strong> <br>
📅 <a href="{APPOINTMENT_URL}" target="_blank">Book Free Consultation</a></p>
</div>"""

# Streamlit Configuration
st.set_page_config(
    page_title="Manchester Legal Content Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State Initialization
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Style Injection
st.markdown("""
<style>
.cta-box {
    border-left: 5px solid #2c3e50;
    padding: 1.5rem;
    margin: 2rem 0;
    background: #f8f9fa;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.header-text {
    color: #2c3e50;
    border-bottom: 2px solid #2c3e50;
    padding-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

def generate_content(keyword, content_type, creativity, heading_style, content_length, unique_content):
    """
    Generate anti-AI detected legal content with enhanced uniqueness
    """
    if not st.session_state.api_key:
        return "⚠️ Please enter a valid OpenAI API key in the sidebar"
    
    client = OpenAI(api_key=st.session_state.api_key)
    
    uniqueness_rules = """
    - Include specific references to Manchester County Court procedures
    - Mention 2-3 local Manchester legal precedents
    - Use British legal terminology variations (e.g., "solicitor" not "attorney")
    - Add hypothetical client scenarios from Greater Manchester
    """ if unique_content else ""
    
    prompt = f"""
    Create {content_length} of {content_type} content about '{keyword}' for a Manchester solicitors firm.
    Heading Style: {heading_style}
    
    Strict Requirements:
    1. Zero AI detection patterns
    2. Include 3-5 Manchester-specific legal references
    3. Use markdown formatting with H2/H3 headings
    4. Add 2 client case studies (fictional but realistic)
    5. Include current UK legal statistics (2023-2024)
    6. Apply natural keyword variations
    7. Follow E-A-T (Expertise, Authoritativeness, Trustworthiness) principles
    8. Use Oxford comma and UK English spelling
    9. {uniqueness_rules}
    
    Structure:
    - Introduction with local relevance
    - Detailed legal analysis section
    - Client success story example
    - Practical advice section
    - FAQ with 3-5 questions
    - Conclusion with strong CTA
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a senior legal writer specializing in Manchester law with 15 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=creativity,
            max_tokens=4000,
            frequency_penalty=0.8,
            presence_penalty=0.6
        )
        content = response.choices[0].message.content
        return f"{content}\n{CTA}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.api_key = st.text_input("Enter OpenAI API Key:", type="password")
    content_type = st.selectbox("Content Type", ["Service Page", "Blog Article", "Case Study", "Practice Area Guide"])
    heading_style = st.selectbox("Heading Style", ["Professional", "Client-Focused", "Question-Based", "Solution-Oriented"])
    content_length = st.selectbox("Content Length", ["Short (300-500 words)", "Standard (500-800 words)", "Comprehensive (800-1200 words)"])
    unique_content = st.checkbox("Enhanced Uniqueness Mode", True)
    creativity = st.slider("Creativity Level", 0.0, 1.0, 0.35, help="Lower = More Technical, Higher = More Creative")

# Main Interface
st.title("📝 Manchester Legal Content Generator")
st.markdown('<div class="header-text">Create Unique, AI-Undetectable Legal Content</div>', unsafe_allow_html=True)

keyword = st.text_input("🔍 Enter Primary Legal Keyword/Phrase:", 
                       placeholder="Employment tribunal representation in Manchester")

if st.button("Generate Content", type="primary"):
    if not keyword:
        st.warning("Please enter a legal keyword/phrase")
    else:
        with st.spinner("🔍 Crafting 100% Unique Content (60-90 seconds)..."):
            generated_content = generate_content(
                keyword=keyword,
                content_type=content_type,
                creativity=creativity,
                heading_style=heading_style,
                content_length=content_length,
                unique_content=unique_content
            )
            
            st.markdown(generated_content, unsafe_allow_html=True)
            
            # Post-Generation Checklist
            st.success("✅ Content Generated Successfully! Next Steps:")
            st.markdown("""
            1. Run through [Originality.ai](https://originality.ai) plagiarism check
            2. Verify Manchester legal references
            3. Add firm-specific success metrics
            4. Check keyword density with [Ahrefs](https://ahrefs.com)
            5. Legal compliance review by partner
            6. Add relevant case studies
            """)

# Footer
st.markdown("---")
st.markdown(f"""
**Need Immediate Assistance?**  
📞 {PHONE} | 📅 [Schedule Strategic Consultation]({APPOINTMENT_URL})
""")
