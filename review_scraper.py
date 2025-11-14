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
        "justdial": "https://www.justdial.com/Delhi/Fortis-Healthcare/nct-11979510",
        "mouthshut": "https://www.mouthshut.com/product-reviews/fortis-hospital-reviews-926159290"
    },
    "Max": {
        "justdial": "https://www.justdial.com/Delhi/Max-Healthcare/nct-12039409?trkid=13117586-delhi&term=Max",
        "mouthshut": "https://www.mouthshut.com/product-reviews/max-healthcare-hospital-reviews-925878024"
    },
    "Apollo": {
        "justdial": "https://www.justdial.com/Delhi/Apollo-Hospitals/nct-11976235?trkid=13966725-delhi&term=Apollo",
        "mouthshut": "https://www.mouthshut.com/product-reviews/apollo-hospital-greams-road-chennai-reviews-925096286"
    }
}

# ============================================
# PART 2: SELENIUM SETUP (Stealth Mode)
# ============================================

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

# ============================================
# PART 3: REVIEW SCRAPERS
# ============================================

def get_justdial_hospital_links(listing_url, hospital_name):

    print(f"\n[JUSTDIAL] Finding {hospital_name} locations...")
    driver = create_stealth_driver()
    hospital_links = []

    try:
        driver.get(listing_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find all hospital links
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            # Check if it's a hospital detail page
            if hospital_name in href and "/Delhi/" in href and href.startswith("/"):
                full_url = "https://www.justdial.com" + href.split("?")[0]
                if full_url not in hospital_links:
                    hospital_links.append(full_url)

        print(f"Found {len(hospital_links)} {hospital_name} locations")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return hospital_links

def scrape_justdial_reviews(listing_url, hospital_name):

    print(f"\n[JUSTDIAL] Scraping {hospital_name}...")
    all_reviews = []

    # Step 1: Get all hospital location URLs
    hospital_links = get_justdial_hospital_links(listing_url, hospital_name)

    if not hospital_links:
        print(f"No locations found for {hospital_name}")
        return all_reviews

    # Step 2: Scrape each location
    driver = create_stealth_driver()

    try:
        for idx, url in enumerate(hospital_links):
            print(f"  [{idx+1}/{len(hospital_links)}] Scraping: {url}")

            try:
                driver.get(url)
                time.sleep(5)

                # Scroll to load all reviews
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                try:
                    for i in range(10):
                        button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.ID, "reivews_read_all"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(3)
                except Exception as e:
                    print(f"Could not click Read all reviews button: {e}")

                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Get location name for context
                location_name = soup.find("h1")
                location_name = location_name.get_text(strip=True) if location_name else "Unknown Location"

                # Extract reviews
                review_boxes = soup.find_all("div", class_="review_box")
                location_reviews = 0

                for box in review_boxes:
                    review_div = box.find("div", class_=lambda x: x and "revw_star_text" in str(x))
                    if review_div:
                        q_tag = review_div.find("q")
                        if q_tag:
                            text = q_tag.get_text(strip=True)
                            if text and len(text) > 10:
                                # Get rating if available
                                rating_div = box.find("div", class_="userrating_box")

                                all_reviews.append({
                                    "source": "JustDial",
                                    "hospital": hospital_name,
                                    "review": text,
                                })
                                location_reviews += 1

                print(f"Found {location_reviews} reviews at this location")
                time.sleep(random.uniform(2, 4))  # Random delay between locations

            except Exception as e:
                print(f"Error at {url}: {e}")
                continue

        print(f"Total: {len(all_reviews)} reviews from {len(hospital_links)} locations")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return all_reviews

def scrape_mouthshut_reviews(base_url, hospital):
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
                    EC.presence_of_element_located((By.CLASS_NAME, "review-article"))
                )
                print("Reviews loaded successfully")
            except:
                print("No review loaded")
                break

            # Additional wait for dynamic content
            time.sleep(2)

            # Find all review divs
            review_divs = driver.find_elements(By.CSS_SELECTOR, "div.row.review-article")

            if not review_divs:
                print("No reviews found.")
                break

            for div in review_divs:
                try:
                    # Find the review text within each div
                    review_element = div.find_element(By.CSS_SELECTOR, "div.more.reviewdata")
                    text = review_element.text.strip()

                    if text:
                        reviews.append({
                            "source": "MouthShut",
                            "hospital": hospital,
                            "review": text,
                        })
                except Exception as e:
                    print(f"Error extracting review: {e}")
                    continue

            print(f"Extracted {len(reviews)} total reviews so far")

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


# ============================================
# PART 4: MAIN DATA COLLECTION
# ============================================

def collect_all_data():
    all_reviews = []
    all_news = []

    for hospital_name, urls in HOSPITALS.items():
        print(f"\n{'='*50}")
        print(f"COLLECTING DATA FOR: {hospital_name}")
        print(f"{'='*50}")

        # Collect reviews from multiple sources
        try:
            mouthshut_reviews=scrape_mouthshut_reviews(urls["mouthshut"],hospital_name)
            all_reviews.extend(mouthshut_reviews)
            justdial_reviews = scrape_justdial_reviews(urls["justdial"], hospital_name)
            all_reviews.extend(justdial_reviews)
            time.sleep(3)
        except:
            pass

    return all_reviews

# ============================================
# PART 5: DATA STORAGE
# ============================================

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



# ============================================
# PART 7: MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("HOSPITAL COMPARISON PROJECT")
    print("="*50)

    # Step 1: Collect data
    print("\nStep 1: Collecting reviews...")
    reviews= collect_all_data()

    # Step 2: Save data
    print("\nStep 2: Saving data...")
    data = save_data(reviews)