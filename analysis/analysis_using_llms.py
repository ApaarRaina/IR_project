import subprocess
import json
import requests
from datetime import datetime
import glob
import os

# ============================================
# PART 1: LLM FUNCTIONS
# ============================================

def analyze_with_ollama(prompt):
    """Analyze with local Ollama (llama3)"""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Ollama error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Ollama error: Request timed out after 5 minutes"
    except Exception as e:
        return f"Error calling Ollama: {e}"

def analyze_with_openrouter(prompt):
    """Analyze with OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer Token",  # Replace with your key
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"OpenRouter error: {e}"

def analyze_with_huggingface(prompt):
    """Analyze with HuggingFace Inference API"""
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {
        "Authorization": "Bearer Token",  # Replace with your key
        "Content-Type": "application/json"
    }
    data = {"inputs": prompt, "parameters": {"max_new_tokens": 2048}}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"]
        elif "error" in result:
            return f"HuggingFace error: {result['error']}"
        return str(result)
    except Exception as e:
        return f"HuggingFace error: {e}"

# ============================================
# PART 2: PROMPT BUILDER
# ============================================

def build_comprehensive_prompt(hospital_data):
    """Build detailed analysis prompt with defined parameters"""
    
    hospitals_list = list(hospital_data['data'].keys())
    
    # Build summary statistics
    stats = []
    for hospital in hospitals_list:
        h_data = hospital_data['data'][hospital]
        stats.append(f"{hospital}: {h_data['review_count']} reviews, {h_data['news_count']} news items")
    
    prompt = f"""I have collected comprehensive review and news data for {len(hospitals_list)} hospitals in Delhi:
{chr(10).join([f"{i+1}. {h}" for i, h in enumerate(hospitals_list)])}

DATA SUMMARY:
{chr(10).join(stats)}

COMPARISON PARAMETERS:
1. Patient Satisfaction & Overall Experience
2. Medical Staff Quality & Expertise
3. Cleanliness & Hygiene Standards
4. Infrastructure & Facilities
5. Emergency Care Response Time
6. Specialized Treatments (Cancer, Cardiology, Orthopedics, Neurology)
7. Cost & Affordability
8. Wait Times & Appointment Availability
9. Post-treatment Care & Follow-up
10. Recent News & Reputation

COMPLETE DATA:
{json.dumps(hospital_data['data'], indent=2)}

DETAILED ANALYSIS REQUIRED:

A. OVERALL RANKING:
- Rank ALL hospitals from best to worst (1-{len(hospitals_list)})
- Provide overall score for each hospital (out of 10)
- Justify rankings with specific data examples from reviews
- Use actual quotes from reviews in [brackets]

B. PARAMETER-WISE COMPARISON:
For EACH of the 10 parameters listed above:
- Rank hospitals for that specific parameter
- Provide specific evidence from reviews/news
- Quote actual patient feedback in [brackets]
- Identify best and worst performer for each parameter

C. SPECIALIZATION ANALYSIS:
Which hospital is BEST for:
- Cancer treatment (cite specific reviews mentioning cancer care)
- Heart surgery/Cardiology (cite specific reviews)
- Orthopedics/Bone surgery (cite specific reviews)
- Neurology/Brain surgery (cite specific reviews)
- Emergency care (cite specific reviews about emergency response)
- General consultation (cite specific reviews)
- Pediatric care (cite specific reviews about children)

D. STRENGTHS & WEAKNESSES:
For EACH hospital, provide:
- Top 3 Strengths (with quoted review examples in [brackets])
- Top 3 Weaknesses (with quoted review examples in [brackets])
- Critical issues that need immediate attention

E. PATIENT RECOMMENDATIONS:

**Best Hospital For:**
- Emergency cases (explain why with evidence)
- Planned surgeries (explain why with evidence)
- Budget-conscious patients (explain why with evidence)
- Cancer patients (explain why with evidence)
- Heart patients (explain why with evidence)
- Orthopedic patients (explain why with evidence)
- Quality of care regardless of cost (explain why)

**Hospitals to Avoid For:**
- List any specific conditions or situations where certain hospitals should be avoided
- Cite specific complaints from reviews

F. HOSPITAL IMPROVEMENT RECOMMENDATIONS:

For EACH hospital, provide 5 actionable suggestions:
1. Immediate priority (based on most frequent complaints)
2. Staff training needs (based on patient feedback)
3. Infrastructure improvements (based on patient feedback)
4. Service enhancements (based on patient feedback)
5. Patient communication improvements (based on patient feedback)

Use actual review quotes to support each suggestion.

G. RED FLAGS & CRITICAL WARNINGS:
- Critical safety issues found in any hospital (with evidence)
- Patterns of serious complaints (with examples)
- Recent negative news that patients should know about
- Any malpractice or negligence mentioned in reviews

H. MODEL COMPARISON NOTES:
- If you are OpenRouter or HuggingFace, note any differences in your analysis approach
- Highlight areas where you might have different insights than other models

CRITICAL REQUIREMENTS:
✓ Use ONLY the data provided above
✓ Quote actual reviews in [brackets] as evidence for EVERY claim
✓ Be specific with hospital names, not generalizations
✓ Provide numerical rankings where requested
✓ Consider all branches of each hospital together
✓ Base recommendations on data, not assumptions
✓ If data is insufficient for a parameter, clearly state "Insufficient data"

Please provide a thorough, evidence-based analysis."""
    
    return prompt

# ============================================
# PART 3: MULTI-MODEL COMPARISON
# ============================================

def compare_model_outputs(prompt, combined_file):
    """Run analysis with multiple models and compare"""
    
    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ollama Analysis
    print("\n" + "=" * 70)
    print("ANALYZING WITH OLLAMA (llama3)...")
    print("=" * 70)
    ollama_result = analyze_with_ollama(prompt)
    results['ollama_llama3'] = {
        "model": "Ollama Llama3",
        "result": ollama_result,
        "timestamp": datetime.now().isoformat()
    }
    print(ollama_result)
    
    # Save Ollama result immediately
    ollama_file = f"analysis_ollama_{timestamp}.txt"
    with open(ollama_file, 'w', encoding='utf-8') as f:
        f.write(ollama_result)
    print(f"\n✓ Saved Ollama analysis to: {ollama_file}")
    
    # OpenRouter Analysis (uncomment if you have API key)
    print("\n" + "=" * 70)
    print("ANALYZING WITH OPENROUTER (Mistral-7B)...")
    print("=" * 70)
    openrouter_result = analyze_with_openrouter(prompt)
    results['openrouter_mistral'] = {
        "model": "OpenRouter Mistral-7B",
        "result": openrouter_result,
        "timestamp": datetime.now().isoformat()
    }
    print(openrouter_result)
    
    # Save OpenRouter result
    openrouter_file = f"analysis_openrouter_{timestamp}.txt"
    with open(openrouter_file, 'w', encoding='utf-8') as f:
        f.write(openrouter_result)
    print(f"\n✓ Saved OpenRouter analysis to: {openrouter_file}")
    
    # HuggingFace Analysis (uncomment if you have API key)
    print("\n" + "=" * 70)
    print("ANALYZING WITH HUGGING FACE (Mistral-7B-Instruct)...")
    print("=" * 70)
    hf_result = analyze_with_huggingface(prompt)
    results['huggingface_mistral'] = {
        "model": "HuggingFace Mistral-7B-Instruct",
        "result": hf_result,
        "timestamp": datetime.now().isoformat()
    }
    print(hf_result)
    
    # Save HuggingFace result
    hf_file = f"analysis_huggingface_{timestamp}.txt"
    with open(hf_file, 'w', encoding='utf-8') as f:
        f.write(hf_result)
    print(f"\n✓ Saved HuggingFace analysis to: {hf_file}")
    
    # Save comparison results
    comparison_data = {
        "source_file": combined_file,
        "analysis_date": datetime.now().isoformat(),
        "models_used": list(results.keys()),
        "results": results,
        "prompt": prompt
    }
    
    comparison_filename = f"model_comparison_{timestamp}.json"
    with open(comparison_filename, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"✓ Comparison results saved to: {comparison_filename}")
    print(f"{'=' * 70}")
    
    return results

# ============================================
# PART 4: FIND LATEST COMBINED FILE
# ============================================

def find_latest_combined_file():
    """Find the most recent combined hospital data file"""
    combined_files = glob.glob("all_hospitals_combined_*.json")
    
    if not combined_files:
        print("Error: No combined hospital data file found")
        print("Please run merge_data.py first")
        return None
    
    latest_file = max(combined_files, key=os.path.getctime)
    print(f"Using data file: {latest_file}")
    return latest_file

# ============================================
# PART 5: MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("COMPREHENSIVE HOSPITAL COMPARISON ANALYSIS")
    print("Using Multiple LLM Models")
    print("=" * 70)
    
    # Find latest combined file
    combined_file = find_latest_combined_file()
    
    if not combined_file:
        print("\n✗ Analysis failed: No combined data file found")
        print("Please run the following scripts in order:")
        print("1. python review_scraper.py")
        print("2. python news_scraper.py")
        print("3. python merge_data.py")
        exit(1)
    
    # Load hospital data
    print(f"\nLoading hospital data from: {combined_file}")
    with open(combined_file, "r", encoding="utf-8") as f:
        hospital_data = json.load(f)
    
    print(f"Loaded data for {len(hospital_data['data'])} hospitals")
    print(f"Total reviews: {hospital_data.get('total_reviews', 'Unknown')}")
    print(f"Total news: {hospital_data.get('total_news', 'Unknown')}")
    
    # Build prompt
    print("\nBuilding comprehensive analysis prompt...")
    prompt = build_comprehensive_prompt(hospital_data)
    
    # Save prompt for reference
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = f"analysis_prompt_{timestamp}.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"✓ Saved prompt to: {prompt_file}")
    
    # Run multi-model analysis
    print("\nStarting multi-model analysis...")
    print("This may take several minutes...")
    
    results = compare_model_outputs(prompt, combined_file)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"Models used: {', '.join(results.keys())}")
    print("\nCheck the generated files for detailed results:")
    print("- analysis_ollama_*.txt")
    print("- analysis_openrouter_*.txt (if enabled)")
    print("- analysis_huggingface_*.txt (if enabled)")
    print("- model_comparison_*.json")