import subprocess
import sys
import time

def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "=" * 70)
    print(f"RUNNING: {description}")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ {description} failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("HOSPITAL COMPARISON PROJECT - FULL PIPELINE")
    print("=" * 70)
    
    scripts = [
        ("review_scraper.py", "Review Collection"),
        ("news_scraper.py", "News Collection"),
        ("merge_data.py", "Data Merging"),
        ("analysis_using_ollama.py", "Multi-Model Analysis")
    ]
    
    results = {}
    
    for script, description in scripts:
        print(f"\n[{scripts.index((script, description)) + 1}/{len(scripts)}]")
        success = run_script(script, description)
        results[description] = success
        
        if not success:
            print(f"\nPipeline stopped at: {description}")
            print("Please fix the errors and try again")
            break
        
        # Wait between steps
        if script != scripts[-1][0]:
            print("\nWaiting 5 seconds before next step...")
            time.sleep(5)
    
    # Print summary
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    for description, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{description}: {status}")
    
    if all(results.values()):
        print("\n🎉 All steps completed successfully!")
        print("\nGenerated files:")
        print("- hospital_reviews_*.json")
        print("- hospital_news_*.json")
        print("- all_hospitals_combined_*.json")
        print("- hospital_*_*.json (individual hospital files)")
        print("- analysis_*.txt")
        print("- model_comparison_*.json")
    else:
        print("\n⚠ Some steps failed. Please check the errors above.")