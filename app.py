import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_content(keyword):
    prompt = f"""
    Create a 600-800 word professional legal blog post about '{keyword}' in UK immigration law, 
    following this exact structure:

    1. Introduction (explain the concept and its relevance to human rights)
    2. Legal Framework (cite specific UK laws like Human Rights Act 1998)
    3. Eligibility Criteria
    4. Application Process
    5. Common Challenges
    6. Case Study Example
    7. FAQs
    8. Conclusion with call-to-action for legal advice

    Tone: Professional yet accessible
    Style: Similar to Reiss Edwards' immigration blog
    Avoid: AI patterns - use natural language variations
    Include: Specific UK legal references
    Add: Practical advice and potential pitfalls
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a UK immigration law expert with 15 years experience."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def main():
    keyword = input("Enter immigration law keyword (e.g., 'Human Rights Application'): ")
    content = generate_content(keyword)
    
    # Save to file
    filename = f"{keyword.replace(' ', '_').lower()}_blog.txt"
    with open(filename, "w") as f:
        f.write(content)
    
    print(f"Blog post generated successfully: {filename}")

if __name__ == "__main__":
    main()
