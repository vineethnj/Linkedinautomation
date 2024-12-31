from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
import time
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/linkedin_automation.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome-stable', '--version'])
        version = output.decode('utf-8').strip()
        logger.info(f"Chrome version: {version}")
        return version
    except Exception as e:
        logger.error(f"Error getting Chrome version: {e}")
        return None

def check_chrome_installation():
    try:
        # First try using 'which' command
        chrome_path = subprocess.check_output(['which', 'google-chrome-stable']).decode().strip()
        if os.path.exists(chrome_path):
            logger.info(f"Chrome found at: {chrome_path}")
            return chrome_path
    except:
        # If 'which' fails, check common locations
        chrome_paths = [
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            "/usr/local/bin/google-chrome",
            "/usr/bin/chrome",
            "/opt/google/chrome/chrome"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Chrome found at: {path}")
                return path
            
    logger.error("Chrome not found in any location")
    return None

def linkedin_automation(email, password, recipient_name, message):
    browser = None
    try:
        # Log environment information
        logger.info("Starting LinkedIn automation")
        chrome_path = check_chrome_installation()
        
        if not chrome_path:
            raise WebDriverException("Chrome binary not found. Please ensure Chrome is installed.")

        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = chrome_path

        # Additional debugging options
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument("--log-level=0")

        # Check if chromedriver exists
        chromedriver_path = "/usr/local/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            logger.error(f"Chromedriver not found at {chromedriver_path}")
            raise WebDriverException(f"Chromedriver not found at {chromedriver_path}")

        logger.info(f"Using Chrome binary at: {chrome_path}")
        logger.info(f"Using Chromedriver at: {chromedriver_path}")

        # Initialize WebDriver with service
        service = Service(
            executable_path=chromedriver_path,
            log_path="/tmp/chromedriver.log"
        )

        browser = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
        wait = WebDriverWait(browser, 10)
        logger.info("WebDriver initialized successfully")

        # Navigate to LinkedIn login
        logger.info("Navigating to LinkedIn login page")
        browser.get('https://www.linkedin.com/login')

        # Login process
        logger.info("Attempting login")
        email_input = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        email_input.send_keys(email)
        
        password_input = wait.until(EC.presence_of_element_located((By.ID, 'password')))
        password_input.send_keys(password)
        
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button.click()

        # Verify login success
        logger.info("Verifying login success")
        wait.until(EC.url_contains('feed'))
        logger.info("Login successful")

        # Navigate to messaging
        logger.info("Navigating to messaging section")
        browser.get('https://www.linkedin.com/messaging/')
        
        # Search for recipient
        logger.info(f"Searching for recipient: {recipient_name}")
        search_message_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search messages"]'))
        )
        search_message_input.clear()
        search_message_input.send_keys(recipient_name)
        time.sleep(2)  # Allow search results to populate

        # Click on recipient
        logger.info("Selecting recipient")
        user_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//span[text()="{recipient_name}"]'))
        )
        user_element.click()

        # Send message
        logger.info("Sending message")
        message_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
        )
        message_input.send_keys(message)
        message_input.send_keys(Keys.CONTROL + Keys.ENTER)

        logger.info("Message sent successfully")
        return "Message sent successfully!"

    except TimeoutException as e:
        error_msg = f"Operation timed out: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except NoSuchElementException as e:
        error_msg = f"Element not found: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except WebDriverException as e:
        error_msg = f"WebDriver error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        if browser:
            logger.info("Closing browser")
            browser.quit()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        recipient_name = request.form.get("recipient_name")
        message = request.form.get("message")

        if not all([email, password, recipient_name, message]):
            logger.warning("Form submitted with missing fields")
            return render_template("index.html", error="Please fill in all the fields.")

        try:
            result = linkedin_automation(email, password, recipient_name, message)
            logger.info("Automation completed with result: " + result)
            return render_template("index.html", result=result)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(error_msg)
            return render_template("index.html", error=error_msg)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)