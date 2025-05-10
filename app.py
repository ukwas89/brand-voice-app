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
    page_title="Manchester Legal Content Architect",
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
    border-left: 4px solid #2c3e50;
    padding: 1.5rem;
    margin: 2rem 0;
    background: #f8f9fa;
    border-radius: 8px;
}
.heading-input textarea {
    font-family: monospace;
    font-size: 14px;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

def parse_headings(headers_input):
    """Parse user-input headings with validation"""
    headings = []
    errors = []
    
    for i, line in enumerate(headers_input.split('\n')):
        line = line.strip()
        if not line:
            continue
            
        if ':' not in line:
            errors.append(f"Line {i+1}: Missing colon separator")
            continue
            
        level_part, _, heading_text = line.partition(':')
        level_part = level_part.strip().upper()
        heading_text = heading_text.strip()
        
        if not heading_text:
            errors.append(f"Line {i+1}: Missing heading text")
            continue
            
        if level_part not in ['H1', 'H2', 'H3', 'H4', 'H5']:
            errors.append(f"Line {i+1}: Invalid heading level '{level_part}'")
            continue
            
        headings.append((level_part, heading_text))
    
    return headings, errors

def generate_content(keyword, content_type, creativity, headings, content_length, unique_content):
    """Generate content with custom heading hierarchy"""
    if not st.session_state.api_key:
        return "⚠️ Please enter a valid OpenAI API key in the sidebar"
    
    client = OpenAI(api_key=st.session_state.api_key)
    
    # Heading instructions
    heading_instructions = ""
    if headings:
        heading_instructions = "STRICT HEADING STRUCTURE REQUIREMENTS:\n"
        for level, text in headings:
            heading_instructions += f"- {level}: {text}\n"
        heading_instructions += "Maintain this exact hierarchy and wording"
    else:
        heading_instructions = "Create SEO-optimized heading structure with H1-H3 levels"

    uniqueness_rules = """
    - Include 3-5 Manchester-specific legal references post-2020
    - Use uncommon British legal terminology variants
    - Add fictional client scenarios with Manchester business names
    - Reference recent Manchester County Court decisions
    """ if unique_content else ""

    prompt = f"""
    Create {content_length} of {content_type} content about '{keyword}' with:
    
    1. HEADING COMPLIANCE:
    {heading_instructions}
    
    2. ANTI-PLAGIARISM MEASURES:
    - 100% original content with zero duplication
    - Unique phrasing patterns
    - Original case studies with fictional details
    - British English spellings and legal terms
    {uniqueness_rules}
    
    3. CONTENT RULES:
    - HTML formatting for headings (no markdown)
    - Include 4-7 UK legal statistics (2023-2024)
    - Add 3 practical client advice sections
    - Local Manchester area focus
    - FAQ with 5 questions
    - Natural keyword integration (1-1.5% density)
    
    4. WRITING STANDARDS:
    - E-A-T (Expertise, Authoritativeness, Trustworthiness) compliant
    - Clear hierarchy from H1 to H5
    - Conversational but professional tone
    - Oxford comma usage
    - Varied sentence structures
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a Manchester legal content expert with 15 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=creativity,
            max_tokens=4000,
            frequency_penalty=0.9,
            presence_penalty=0.7
        )
        content = response.choices[0].message.content
        return f"{content}\n{CTA}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.api_key = st.text_input("OpenAI API Key:", type="password")
    content_type = st.selectbox("Content Type", ["Service Page", "Legal Guide", "Case Study", "Blog Post"])
    content_length = st.selectbox("Content Length", ["Brief (400 words)", "Standard (700)", "Detailed (1000)"])
    creativity = st.slider("Creativity Level", 0.0, 1.0, 0.3)
    unique_content = st.checkbox("Enhanced Uniqueness Mode", True)
    
    # Heading input
    st.subheader("Custom Headings")
    heading_input = st.text_area(
        "Input headings (H1-H5):",
        height=200,
        help="Enter one heading per line using format: H1: Main Title\nH2: Subheading\nH3: Sub-subheading",
        placeholder="H1: Employment Law Manchester\nH2: Employee Rights\nH3: Workplace Discrimination\nH2: Employer Obligations"
    )

# Main Interface
st.title("📝 Legal Content Generator with Custom Headings")
st.markdown(f"**Create Unique, Structured Content for {PHONE}**")

# Parse headings
headings, errors = parse_headings(heading_input)
if errors:
    for error in errors:
        st.error(error)

keyword = st.text_input("Primary Keyword:", placeholder="Employment tribunal Manchester")
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
                headings=headings,
                content_length=content_length,
                unique_content=unique_content
            )
            
            st.markdown(content, unsafe_allow_html=True)
            
            # Quality assurance
            st.success("✅ Content Generated! Verification Steps:")
            st.markdown("""
            1. Validate heading hierarchy
            2. Check Manchester references
            3. Run plagiarism scan
            4. Verify legal accuracy
            5. Add firm contact details
            6. Test mobile responsiveness
            """)

st.markdown("---")
st.markdown(f"""
**Need Assistance?**  
📞 {PHONE} | 📅 [Schedule Consultation]({APPOINTMENT_URL})
""")
