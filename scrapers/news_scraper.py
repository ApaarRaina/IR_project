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

# ============================================
# PART 1: CONFIGURATION
# ============================================

HOSPITALS = {
    "Fortis": {
        "news": "https://search.brave.com/news?q=fortis+patient+care+and+medicine"
    },
    "Max": {"news": "https://search.brave.com/news?q=max+patient+care+and+medicine"},
    "Narayana": {
        "news": "https://search.brave.com/news?q=narayana+health+patient+care"
    },
    "Apollo": {
        "news": "https://search.brave.com/news?q=Apollo+patient+care+and+medicine"
    },
    "AIIMS": {"news": "https://search.brave.com/news?q=AIIMS+delhi+patient+care"},
    "Medanta": {"news": "https://search.brave.com/news?q=Medanta+patient+care"},
    "BLK": {"news": "https://search.brave.com/news?q=BLK+hospital+patient+care"},
}


# ============================================
# PART 2: SELENIUM SETUP
# ============================================


def create_stealth_driver():
    chrome_options = Options()

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# ============================================
# PART 3: NEWS SCRAPER
# ============================================


def scrape_news_headlines(base_url, hospital_name):
    print(f"\n[NEWS] Scraping {hospital_name}...")
    news = []

    driver = create_stealth_driver()

    try:
        page = 1
        max_pages = 3  # Limit to 3 pages

        while page <= max_pages:
            print(f"Scraping page {page}...")
            url = f"{base_url}-page-{page}"

            driver.get(url)

            # Wait for news to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.results.svelte-1gc460s")
                    )
                )
                print("News headlines loaded successfully")
            except:
                print("Timeout waiting for news to load")
                break

            # Additional wait for dynamic content
            time.sleep(2)

            # Find all news divs
            news_divs = driver.find_elements(
                By.CSS_SELECTOR, "div.result-content.svelte-md19lk"
            )

            if not news_divs:
                print("No more news found.")
                break

            for div in news_divs:
                try:
                    # Find the news headline within each div
                    headline_element = div.find_element(
                        By.CSS_SELECTOR,
                        "span.snippet-title.svelte-md19lk.line-clamp-2.heading-serpresult",
                    )
                    text = headline_element.text.strip()

                    if text:
                        news.append(
                            {
                                "source": "Brave News",
                                "hospital": hospital_name,
                                "headline": text,
                            }
                        )
                except Exception as e:
                    print(f"Error extracting headline: {e}")
                    continue

            print(f"Extracted {len(news)} total news so far")

            # Check for next page
            try:
                next_page_link = driver.find_element(
                    By.XPATH, f"//ul[@class='pages table']//a[text()='{page + 1}']"
                )
                if next_page_link:
                    page += 1
                    time.sleep(2)
                else:
                    print("No next page found")
                    break
            except:
                print("No next page found")
                break

    finally:
        driver.quit()

    return news


# ============================================
# PART 4: DATA COLLECTION
# ============================================


def collect_all_data():
    hospital_news = {}

    for hospital_name, urls in HOSPITALS.items():
        print(f"\n{'='*50}")
        print(f"Collecting News FOR: {hospital_name}")
        print(f"{'='*50}")

        try:
            news = scrape_news_headlines(urls["news"], hospital_name)
            hospital_news[hospital_name] = {"news": news, "news_count": len(news)}
            time.sleep(3)
        except Exception as e:
            print(f"Error collecting news for {hospital_name}: {e}")
            hospital_news[hospital_name] = {"news": [], "news_count": 0}

    return hospital_news


# ============================================
# PART 5: DATA STORAGE
# ============================================


def save_data(hospital_news):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    combined_data = {
        "hospitals": list(HOSPITALS.keys()),
        "data": hospital_news,
        "collection_date": datetime.now().isoformat(),
    }

    filename = f"hospital_news_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved news data to {filename}")
    return filename


# ============================================
# PART 6: MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("HOSPITAL COMPARISON PROJECT - NEWS COLLECTION")
    print("=" * 50)

    print("\nStep 1: Collecting news...")
    hospital_news = collect_all_data()

    print("\nStep 2: Saving data...")
    filename = save_data(hospital_news)

    print(f"\n{'='*50}")
    print("NEWS COLLECTION COMPLETE!")
    print(f"{'='*50}")
    print(f"File: {filename}")
