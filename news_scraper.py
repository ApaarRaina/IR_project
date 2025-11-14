import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import json
from datetime import datetime
import random


HOSPITALS = {
    "Fortis": {
        "news":"https://search.brave.com/news?q=fortis+patient+care+and+medicine"
    },
    "Max": {
        "news":"https://search.brave.com/news?q=max+patient+care+and+medicine"
    },
    "Apollo": {
        "news":"https://search.brave.com/news?q=Apollo+patient+care+and+medicine"
    }
}

def create_stealth_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Hide webdriver
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def scrape_news_headlines(base_url,hospital_name):
    reviews = []

    driver = create_stealth_driver()

    try:
        page = 1
        while True:
            print(f"Scraping page {page}...")
            url = f"{base_url}-page-{page}"

            driver.get(url)

            # Wait for reviews to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.results.svelte-1gc460s"))
                )
                print("News headlines loaded successfully")
            except:
                print("Timeout waiting for reviews to load")
                break

            # Additional wait for dynamic content
            time.sleep(2)

            # Find all review divs
            review_divs = driver.find_elements(By.CSS_SELECTOR, "div.result-content.svelte-md19lk")

            if not review_divs:
                print("No more reviews found.")
                break

            for div in review_divs:
                try:
                    # Find the review text within each div
                    review_element = div.find_element(By.CSS_SELECTOR, "span.snippet-title.svelte-md19lk.line-clamp-2.heading-serpresult")
                    text = review_element.text.strip()

                    if text:
                        reviews.append({
                            "source": "Google News",
                            "hospital": hospital_name,
                            "Headline": text,
                        })
                except Exception as e:
                    print(f"Error extracting headline: {e}")
                    continue

            print(f"Extracted {len(reviews)} total news so far")

            # Check for next page
            try:
                next_page_link = driver.find_element(By.XPATH, f"//ul[@class='pages table']//a[text()='{page + 1}']")
                if next_page_link:
                    page += 1
                    time.sleep(2)  # Be polite to the server
                else:
                    print("No next page found")
                    break
            except:
                print("No next page found")
                break

    finally:
        driver.quit()

    return reviews


def collect_all_data():
    all_news = []

    for hospital_name, urls in HOSPITALS.items():
        print(f"\n{'='*50}")
        print(f"Collecting News FOR: {hospital_name}")
        print(f"{'='*50}")

        # Collect reviews from multiple sources
        try:
            news=scrape_news_headlines(urls['news'],hospital_name)
            all_news.append(news)
            time.sleep(3)
        except:
            pass

    return all_news

def save_data(reviews):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save combined JSON for LLM
    combined_data = {
        "hospitals": list(HOSPITALS.keys()),
        "reviews": reviews,
        "collection_date": datetime.now().isoformat()
    }

    with open(f"hospital_data_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)

    print(f"Saved combined data to hospital_data_{timestamp}.json")

    return combined_data


if __name__ == "__main__":
    print("HOSPITAL COMPARISON PROJECT")
    print("="*50)

    # Step 1: Collect data
    print("\nStep 1: Collecting news...")
    reviews= collect_all_data()

    # Step 2: Save data
    print("\nStep 2: Saving data...")
    data = save_data(reviews)



