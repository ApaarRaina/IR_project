import json
from datetime import datetime
import os
import glob

def find_latest_files():
    """Find the most recent review and news files"""
    review_files = glob.glob("hospital_reviews_*.json")
    news_files = glob.glob("hospital_news_*.json")
    
    if not review_files or not news_files:
        print("Error: Could not find review or news files")
        print(f"Review files found: {len(review_files)}")
        print(f"News files found: {len(news_files)}")
        return None, None
    
    # Get the latest files
    latest_review = max(review_files, key=os.path.getctime)
    latest_news = max(news_files, key=os.path.getctime)
    
    print(f"Using review file: {latest_review}")
    print(f"Using news file: {latest_news}")
    
    return latest_review, latest_news

def merge_hospital_data(reviews_file, news_file):
    """Merge reviews and news data into single hospital JSON files"""
    
    print("\nMerging hospital data...")
    
    with open(reviews_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)
    
    with open(news_file, 'r', encoding='utf-8') as f:
        news_data = json.load(f)
    
    merged_data = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get all unique hospital names from both datasets
    all_hospitals = set(reviews_data['data'].keys()) | set(news_data['data'].keys())
    
    for hospital in all_hospitals:
        print(f"Merging data for {hospital}...")
        
        merged_data[hospital] = {
            "hospital_name": hospital,
            "reviews": reviews_data['data'].get(hospital, {}).get('reviews', []),
            "review_count": reviews_data['data'].get(hospital, {}).get('review_count', 0),
            "news": news_data['data'].get(hospital, {}).get('news', []),
            "news_count": news_data['data'].get(hospital, {}).get('news_count', 0),
            "collection_date": datetime.now().isoformat()
        }
        
        # Save individual hospital file
        hospital_filename = f"hospital_{hospital.lower()}_{timestamp}.json"
        with open(hospital_filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data[hospital], f, indent=2, ensure_ascii=False)
        print(f"  Saved {hospital_filename}")
    
    # Save combined file
    combined_filename = f"all_hospitals_combined_{timestamp}.json"
    combined_data = {
        "hospitals": list(merged_data.keys()),
        "data": merged_data,
        "collection_date": datetime.now().isoformat(),
        "total_hospitals": len(merged_data),
        "total_reviews": sum(h['review_count'] for h in merged_data.values()),
        "total_news": sum(h['news_count'] for h in merged_data.values())
    }
    
    with open(combined_filename, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"Saved combined file: {combined_filename}")
    print(f"{'='*50}")
    print(f"Total hospitals: {combined_data['total_hospitals']}")
    print(f"Total reviews: {combined_data['total_reviews']}")
    print(f"Total news: {combined_data['total_news']}")
    
    return combined_filename

if __name__ == "__main__":
    print("HOSPITAL DATA MERGER")
    print("="*50)
    
    # Find latest files automatically
    reviews_file, news_file = find_latest_files()
    
    if reviews_file and news_file:
        combined_file = merge_hospital_data(reviews_file, news_file)
        print(f"\n✓ Merged data saved to: {combined_file}")
    else:
        print("\n✗ Merge failed: Missing required files")
        print("Please run review_scraper.py and news_scraper.py first")