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

# Session State
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Custom CSS
st.markdown("""
<style>
.cta-box {
    border-left: 5px solid #2c3e50;
    padding: 1.5rem;
    margin: 2rem 0;
    background: #f8f9fa;
    border-radius: 8px;
}
.custom-headings textarea {
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

def generate_content(keyword, content_type, creativity, headings, content_length, unique_content):
    """
    Generate content with custom headings and anti-plagiarism measures
    """
    if not st.session_state.api_key:
        return "⚠️ Please enter a valid OpenAI API key in the sidebar"
    
    client = OpenAI(api_key=st.session_state.api_key)
    
    # Structure handling
    heading_instructions = ""
    if headings:
        heading_list = [h.strip() for h in headings.split('\n') if h.strip()]
        heading_instructions = f"STRICT STRUCTURE:\n- Must use these exact headings in order:\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(heading_list)])
    else:
        heading_instructions = "Create logical headings following UK legal content best practices"

    uniqueness_rules = f"""
    - Include 2-3 Manchester-specific legal precedents from the last 3 years
    - Reference Greater Manchester County Court procedures
    - Use uncommon British legal terminology variants
    - Add hypothetical scenarios from Manchester businesses
    """ if unique_content else ""

    prompt = f"""
    Create {content_length} of {content_type} content about '{keyword}' with these requirements:
    
    1. COMPLETE HEADING COMPLIANCE:
    {heading_instructions}
    
    2. ANTI-PLAGIARISM MEASURES:
    - Zero duplicate content from existing online sources
    - 100% original phrasing and structure
    - Unique case studies with fictional but realistic details
    - Use British English spellings (e.g., colour, organisation)
    {uniqueness_rules}
    
    3. CONTENT RULES:
    - Markdown formatting with H2/H3 headings
    - Include 3-5 statistics from UK Ministry of Justice (2023-2024)
    - Add 2 client testimonials (fictional but realistic names)
    - Practical advice section with numbered steps
    - FAQ section with 5 questions
    - Local Manchester service areas focus
    
    4. WRITING STYLE:
    - Expert but approachable tone
    - Avoid legal jargon without explanations
    - Use Oxford comma consistently
    - Vary sentence length and structure
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a Manchester legal content specialist with 10 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=creativity,
            max_tokens=4000,
            frequency_penalty=0.85,
            presence_penalty=0.7
        )
        content = response.choices[0].message.content
        return f"{content}\n{CTA}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.api_key = st.text_input("OpenAI API Key:", type="password")
    content_type = st.selectbox("Content Type", ["Service Page", "Blog Article", "Guide", "Case Study"])
    content_length = st.selectbox("Length", ["Brief (300-500 words)", "Standard (500-800)", "Detailed (800-1200)"])
    creativity = st.slider("Creativity", 0.0, 1.0, 0.3)
    unique_content = st.checkbox("Enhanced Uniqueness Mode", True)
    
    # Custom headings input
    st.markdown('<div class="custom-headings">', unsafe_allow_html=True)
    user_headings = st.text_area(
        "Custom Headings (optional):",
        height=150,
        help="Enter one heading per line. Content will follow this exact structure"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Main Interface
st.title("📝 Legal Content Generator")
st.markdown(f"**Create Unique, Custom-Structured Content for {PHONE}**")

keyword = st.text_input("Primary Keyword:", placeholder="Employment law Manchester")
generate_btn = st.button("Generate Content", type="primary")

if generate_btn:
    if not keyword:
        st.warning("Please enter a keyword")
    else:
        with st.spinner("🔍 Crafting 100% Original Content (2-3 minutes)..."):
            content = generate_content(
                keyword=keyword,
                content_type=content_type,
                creativity=creativity,
                headings=user_headings,
                content_length=content_length,
                unique_content=unique_content
            )
            
            st.markdown(content, unsafe_allow_html=True)
            
            # Validation checklist
            st.success("✅ Success! Quality Control Steps:")
            st.markdown("""
            1. Check heading structure matches requirements
            2. Verify Manchester-specific references
            3. Run through plagiarism checker
            4. Review legal accuracy
            5. Add firm contact details
            """)

st.markdown("---")
st.markdown(f"""
**Need Help?**  
📞 {PHONE} | 📅 [Book Consultation]({APPOINTMENT_URL})
""")
