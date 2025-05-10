# app.py

import streamlit as st
import openai

# Set page configuration
st.set_page_config(page_title="Legal Content Generator", layout="centered")

# Set OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]  # Add your key in .streamlit/secrets.toml

# App title and description
st.title("📄 Branded Legal Content Generator")
st.write(
    "Generate high-quality, SEO-optimised content for your Manchester-based immigration law firm. "
    "Choose your content type, enter a keyword, and let the app craft persuasive legal content "
    "with embedded calls-to-action (CTAs) to drive client engagement."
)

# Sidebar inputs
st.sidebar.header("✍️ Content Settings")
content_type = st.sidebar.selectbox("Select Content Type:", ["Blog Post", "Service Page", "Landing Page", "FAQ"])
keyword = st.sidebar.text_input("Primary Keyword (e.g. 'immigration solicitor Manchester'):")
length = st.sidebar.selectbox("Content Length:", ["Short", "Standard", "Long"])

# Map length to approximate word count for guidance
length_map = {"Short": "300–500 words", "Standard": "600–800 words", "Long": "1000+ words"}
word_count = length_map[length]

# Generate button
if st.sidebar.button("Generate Content"):
    if not keyword.strip():
        st.error("⚠️ Please enter a keyword before generating content.")
    else:
        # Prompt engineering
        prompt = (
            f"Write a {length.lower()} {content_type.lower()} about \"{keyword}\" "
            "for a Manchester-based immigration law firm's website. "
            "Use UK English spelling. The tone must be formal, professional, informative and reassuring—"
            "suitable for a solicitor's firm (similar to Reiss Edwards). "
            f"Structure the content with clear headings and paragraphs. Aim for {word_count}. "
            "Incorporate the keyword and closely related UK legal terms naturally throughout. "
            "Make it SEO-friendly and accessible to the general public. "
            "Ensure originality—do not copy existing sources. "
            "Include at least two strong calls-to-action such as: "
            "'Call us on 0161 464 4140' or 'book an appointment [here](https://solicitorsinmanchester.co.uk/book-an-appointment/)'. "
            "Place CTAs in logical positions like the introduction and/or conclusion."
        )

        # Display loading status
        st.markdown("⏳ Generating content...")
        
        try:
            # OpenAI API call
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional UK legal copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            # Extract content
            content = response.choices[0].message.content

            # Display result
            st.success("✅ Content generated successfully!")
            st.subheader("📑 Generated Content")
            st.markdown(content, unsafe_allow_html=True)

            # Download button
            st.download_button(
                label="📥 Download Content",
                data=content,
                file_name="legal_content.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"❌ Error generating content: {e}")
