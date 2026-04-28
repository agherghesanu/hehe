import os
import sys
import time
import requests
from datetime import datetime
import pytz

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURATION
URL = "https://plaza.newnewnew.space/en/availables-places/living-place#?gesorteerd-op=prijs%2B"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def check_time_window():
    """Ensure the script only runs between 08:00 and 19:00 Amsterdam time."""
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    now = datetime.now(amsterdam_tz)
    
    if not (8 <= now.hour < 19):
        print(f"Current Amsterdam time is {now.strftime('%H:%M')}. Outside of 08:00-19:00 window. Exiting.")
        sys.exit(0)
    print(f"Current Amsterdam time is {now.strftime('%H:%M')}. Proceeding with check.")

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("No Discord webhook URL found.")
        return
    data = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

def main():
    check_time_window()

    print("Starting headless browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # MUST be headless for GitHub Actions
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(URL)
        
        # Wait for listings to load (waiting for the container that holds the cards)
        # Adjust the CLASS_NAME based on the exact HTML of the listings
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list-item")) 
        )
        
        # Adding a short sleep to allow React/Vue elements to fully render
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        
        if "delft" in page_source:
            # You can make this more specific by looking for specific address elements, 
            # but searching the page source is a robust catch-all.
            msg = f"🚨 **WAKE UP!** 🚨\nNew housing in **Delft** detected!\nCheck the link immediately: {URL}"
            print("Delft housing found! Sending alert...")
            send_discord_alert(msg)
        else:
            print("No housing found in Delft at this time.")

    except Exception as e:
        print(f"An error occurred (Possible CAPTCHA or site structure change): {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()