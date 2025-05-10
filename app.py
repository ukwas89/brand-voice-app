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

PHONE = "0161 464 4140"  # Added missing constant
APPOINTMENT_URL = "https://solicitorsinmanchester.co.uk/book-an-appointment/"  # Added missing URL

# Rest of the code remains the same...

# Fix the footer section at the bottom
st.markdown("---")
st.markdown(f"""
**Need Support?**  
📞 {PHONE} | 📅 [Book Strategy Session]({APPOINTMENT_URL})
""")
