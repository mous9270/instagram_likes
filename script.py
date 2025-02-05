import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ----- CONFIGURATION -----
USERNAME = "USERNAME"       # Replace with the target public account's username
LIKES_THRESHOLD = 500         # Minimum likes threshold to filter
SCROLL_PAUSE_TIME = 2         # Seconds to wait after scrolling
PAGE_LOAD_WAIT = 5            # Seconds to wait for a reel page to load

# ----- HELPER FUNCTION -----
def parse_like_count(text):
    """
    Converts a string like "500", "1,420", "1.2k", or "1.2m" (possibly with the word "likes")
    into a number.
    """
    # Remove the word "likes" and extra whitespace
    text = text.lower().replace("likes", "").strip()
    try:
        if text.endswith("k"):
            return float(text[:-1].replace(',', '')) * 1000
        elif text.endswith("m"):
            return float(text[:-1].replace(',', '')) * 1000000
        else:
            # Remove commas and non-digit characters
            number = re.sub(r"[^\d.]", "", text)
            return float(number)
    except Exception as e:
        print(f"Error parsing like count from '{text}': {e}")
        return 0

# ----- SET UP SELENIUM -----
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
# Uncomment the next line to run headless (without a visible browser window)
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ----- OPEN THE INSTAGRAM REELS PAGE -----
reels_url = f"https://www.instagram.com/{USERNAME}/reels/"
driver.get(reels_url)
time.sleep(PAGE_LOAD_WAIT)  # Allow time for the reels page to load

# ----- SCROLL TO LOAD MORE REELS -----
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  # No more new reels loaded
    last_height = new_height

# ----- COLLECT ALL REEL LINKS -----
# We assume that reel URLs contain '/reel/' in their href attribute.
reel_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/')]")
reel_urls = []
for elem in reel_elements:
    href = elem.get_attribute("href")
    if href and href not in reel_urls:
        reel_urls.append(href)

print(f"Found {len(reel_urls)} reel URLs.")

# ----- VISIT EACH REEL AND EXTRACT LIKE COUNTS -----
reels_over_threshold = []

for idx, reel_url in enumerate(reel_urls, start=1):
    print(f"\nProcessing Reel {idx}/{len(reel_urls)}: {reel_url}")
    driver.get(reel_url)
    time.sleep(PAGE_LOAD_WAIT)  # Wait for reel page to load

    like_text = ""
    try:
        # Look for an element that contains the text "likes"
        like_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'likes')]"))
        )
        like_text = like_container.text
        print("Found like text:", like_text)
    except Exception as e:
        print("Timeout waiting for like count element.")

    # Parse the like count if text was found; otherwise default to 0
    if like_text:
        like_count = parse_like_count(like_text)
    else:
        like_count = 0
    print(f"Parsed like count: {like_count}")

    if like_count >= LIKES_THRESHOLD:
        reels_over_threshold.append((reel_url, like_count))

# ----- OUTPUT THE RESULTS -----
print("\n--- Reels with more than 500 likes ---")
if reels_over_threshold:
    for reel_url, count in reels_over_threshold:
        print(f"{reel_url} --> {int(count)} likes")
else:
    print("No reels found with more than 500 likes.")

driver.quit()

