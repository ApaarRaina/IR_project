import subprocess
import json
from datetime import datetime

def analyze_with_llm(reviews,news):
    print("\n" + "="*50)
    print("ANALYZING DATA WITH OLLAMA...")
    print("="*50)

    prompt = f"""I have collected review and news data for three hospitals in Delhi:
1. Fortis Healthcare
2. Max Healthcare  
3. Apollo Hospitals

Here is the data:

REVIEWS ({len(reviews['reviews'])} total):
{json.dumps(reviews['reviews'], indent=2)}

NEWS ({len(news['reviews'])} total):
{json.dumps(news['reviews'], indent=2)}

Based on this data, please provide:

1. Overall Ranking: Which hospital is the best and why?
2. Key Strengths: What are each hospital's main strengths?
3. Key Weaknesses: What are the common complaints?
4. Patient Satisfaction: Which has the best patient reviews?
5. Recent News: Any recent positive or negative news?
6. Recommendation: Which hospital would you recommend for different scenarios (emergency care, surgery, general consultation)?

Please be thorough and cite specific examples from the data given. Also do take all branches of fortis and all branches of max and all branches of apollo as one and then compare all of them

Please give examples from the data given to you like I want the sentence in brackets. and only use that data given."""

    try:
        # Run Ollama model via subprocess (e.g., llama3)
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True
        )

        if result.returncode == 0:
            analysis = result.stdout.strip()

            print("\n" + "="*50)
            print("ANALYSIS COMPLETE!")
            print("="*50)
            print(analysis)

            return analysis
        else:
            print("Ollama error:", result.stderr)
            return None

    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

with open("hospital_data_20251113_015741.json", "r", encoding="utf-8") as f:
    reviews = json.load(f)

with open("hospital_data_20251114_013156.json", "r", encoding="utf-8") as f:
    news = json.load(f)

analyze_with_llm(reviews,news)