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
import glob
import os
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/linkedin_automation.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def find_chrome_binary():
    """Find Chrome or Chromium binary using multiple methods."""
    possible_paths = [
        os.environ.get('CHROME_BINARY_LOCATION'),  # Check environment variable first
        os.environ.get('CHROME_BIN'),
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/local/bin/google-chrome",
        "/usr/bin/chrome",
        "/opt/google/chrome/chrome"
    ]
    
    # Log all possible paths we're checking
    logger.debug(f"Checking browser paths: {possible_paths}")
    
    # Check each path
    for path in possible_paths:
        if path and os.path.exists(path):
            logger.info(f"Browser found at: {path}")
            return path
            
    # Try using 'which' command as fallback for both Chrome and Chromium
    try:
        for browser in ['chromium-browser', 'google-chrome-stable', 'chromium']:
            try:
                browser_path = subprocess.check_output(['which', browser]).decode().strip()
                if os.path.exists(browser_path):
                    logger.info(f"Browser found using 'which' command at: {browser_path}")
                    return browser_path
            except subprocess.CalledProcessError:
                continue
    except Exception as e:
        logger.warning(f"Failed to find browser using 'which' command: {e}")
    
    return None

def verify_chrome_installation():
    """Verify Chrome/Chromium installation and return detailed status."""
    browser_binary = find_chrome_binary()
    if not browser_binary:
        logger.error("No compatible browser binary found")
        return False, "No compatible browser binary found (tried Chrome and Chromium)"
    
    try:
        version_output = subprocess.check_output([browser_binary, '--version']).decode()
        logger.info(f"Browser version: {version_output.strip()}")
        return True, version_output.strip()
    except Exception as e:
        logger.error(f"Error verifying browser: {e}")
        return False, str(e)

def verify_chromedriver():
    """Verify ChromeDriver installation and version with enhanced error checking."""
    # Check multiple possible locations
    chromedriver_paths = [
        os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver'),
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        'chromedriver'
    ]
    
    logger.info("Checking ChromeDriver in following locations:")
    for path in chromedriver_paths:
        logger.info(f"Checking path: {path}")
        
        # Check if path exists
        if path and os.path.exists(path):
            logger.info(f"ChromeDriver found at: {path}")
            try:
                # Check if executable
                if not os.access(path, os.X_OK):
                    logger.warning(f"ChromeDriver at {path} is not executable")
                    try:
                        os.chmod(path, 0o755)
                        logger.info(f"Added executable permission to ChromeDriver at {path}")
                    except Exception as e:
                        logger.error(f"Failed to set executable permission: {e}")
                        continue
                
                # Try to get version
                version_output = subprocess.check_output([path, '--version'], 
                                                       stderr=subprocess.STDOUT).decode()
                logger.info(f"ChromeDriver version at {path}: {version_output.strip()}")
                
                # Update environment variable with working path
                os.environ['CHROMEDRIVER_PATH'] = path
                return True, version_output.strip()
            except subprocess.CalledProcessError as e:
                logger.error(f"Error running ChromeDriver at {path}: {e.output.decode()}")
            except Exception as e:
                logger.error(f"Unexpected error with ChromeDriver at {path}: {e}")
    
    # If we get here, no working ChromeDriver was found
    logger.error("No working ChromeDriver installation found")
    return False, "No working ChromeDriver installation found in any location"

def linkedin_automation(email, password, recipient_name, message):
    """
    Automate LinkedIn message sending process.
    Returns status message indicating success or detailed error message.
    """
    browser = None
    try:
        logger.info("Starting LinkedIn automation")
        
        # Verify Chrome installation first
        chrome_status, chrome_details = verify_chrome_installation()
        if not chrome_status:
            raise WebDriverException(f"Chrome verification failed: {chrome_details}")
        
        # Verify ChromeDriver
        driver_status, driver_details = verify_chromedriver()
        if not driver_status:
            raise WebDriverException(f"ChromeDriver verification failed: {driver_details}")
        
        chrome_binary = find_chrome_binary()
        if not chrome_binary:
            raise WebDriverException("Chrome binary not found after verification")

        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = chrome_binary
        
        # Add debugging options
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--v=1")
        
        # Log Chrome options
        logger.debug(f"Chrome options: {chrome_options.arguments}")

        # Initialize WebDriver with service
        service = Service(
            executable_path=os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver'),
            log_path="/tmp/chromedriver.log"
        )

        logger.info(f"Initializing WebDriver with binary: {chrome_binary}")
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
        logger.error(error_msg, exc_info=True)
        return error_msg
    finally:
        if browser:
            logger.info("Closing browser")
            try:
                browser.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        recipient_name = request.form.get("recipient_name")
        message = request.form.get("message")

        if not all([email, password, recipient_name, message]):
            logger.warning("Form submitted with missing fields")
            return render_template("index.html", error="Please fill in all fields")

        try:
            result = linkedin_automation(email, password, recipient_name, message)
            logger.info("Automation completed with result: " + result)
            return render_template("index.html", result=result)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(error_msg)
            return render_template("index.html", error=error_msg)

    # For GET requests, include system information
    chrome_status, chrome_details = verify_chrome_installation()
    driver_status, driver_details = verify_chromedriver()
    
    system_info = {
        "chrome_installed": chrome_status,
        "chrome_details": chrome_details,
        "chromedriver_installed": driver_status,
        "chromedriver_details": driver_details,
        "chrome_binary_path": find_chrome_binary()
    }
    
    return render_template("index.html", system_info=system_info)

@app.route("/api/system-check", methods=["GET"])
def system_check():
    """API endpoint for checking system status."""
    chrome_status, chrome_details = verify_chrome_installation()
    driver_status, driver_details = verify_chromedriver()
    
    return jsonify({
        "chrome_installed": chrome_status,
        "chrome_details": chrome_details,
        "chromedriver_installed": driver_status,
        "chromedriver_details": driver_details,
        "chrome_binary_path": find_chrome_binary(),
        "environment_variables": {
            "CHROME_BIN": os.environ.get('CHROME_BIN'),
            "CHROMEDRIVER_PATH": os.environ.get('CHROMEDRIVER_PATH')
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Log system information on startup
    logger.info("=== System Information ===")
    chrome_status, chrome_details = verify_chrome_installation()
    logger.info(f"Chrome status: {chrome_status} - {chrome_details}")
    driver_status, driver_details = verify_chromedriver()
    logger.info(f"ChromeDriver status: {driver_status} - {driver_details}")
    logger.info(f"Chrome binary path: {find_chrome_binary()}")
    logger.info("=== End System Information ===")
    
    app.run(host="0.0.0.0", port=port, debug=False)
