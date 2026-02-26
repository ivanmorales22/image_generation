import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class JerseyScraper:
    def __init__(self, destination_folder="data/raw"):
        self.destination_folder = destination_folder
        self.driver = None
        self.wait = None
        
        # Ensure destination exists
        if not os.path.exists(self.destination_folder):
            os.makedirs(self.destination_folder)

    def _setup_driver(self):
        """Internal method to initialize the Chrome driver."""
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        options.add_argument("--headless") 
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def _scroll_to_bottom(self):
        """Scrolls the page to ensure all lazy-loaded items are present."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_kit_urls(self, team_url):
        """Navigates to team page and extracts all home-kit URLs."""
        print(f"\n--- Accessing: {team_url} ---")
        self.driver.get(team_url)
        self._scroll_to_bottom()

        elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '-home-kit/')]")
        # Use a set to automatically handle uniqueness
        urls = {el.get_attribute("href") for el in elements if el.get_attribute("href")}
        print(f"Found {len(urls)} unique home jerseys.")
        return list(urls)

    def download_image(self, kit_url):
        """Navigates to a specific kit page and downloads the main image."""
        try:
            self.driver.get(kit_url)
            
            # Extract Title for Filename
            title_el = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            file_name = title_el.text.lower().strip().replace(" ", "_").replace("/", "-") + ".jpg"
            
            # Extract Image Source
            img_el = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//img[contains(@src, 'cdn.footballkitarchive.com')]")
            ))
            img_url = img_el.get_attribute("src")

            # Request and Save
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                path = os.path.join(self.destination_folder, file_name)
                with open(path, 'wb') as f:
                    f.write(response.content)
                print(f" Saved: {file_name}")
            else:
                print(f" Failed to download: {img_url}")

        except Exception as e:
            print(f" Error processing {kit_url}: {e}")

    def scrape_team(self, team_url):
        """Orchestrates the scraping process for a single team."""
        if not self.driver:
            self._setup_driver()

        kit_urls = self.get_kit_urls(team_url)
        
        for url in kit_urls:
            self.download_image(url)
            time.sleep(1.5) # Polite delay

    def close(self):
        """Closes the browser session."""
        if self.driver:
            print("\nClosing browser...")
            self.driver.quit()

# --- Execution Block ---
if __name__ == "__main__":
    TEAMS = [
        "https://www.footballkitarchive.com/olympiacos-piraeus-kits/"
    ]

    scraper = JerseyScraper(destination_folder="../data/raw")
    try:
        for team in TEAMS:
            scraper.scrape_team(team)
    finally:
        scraper.close()