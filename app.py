from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

def linkedin_automation(email, password, recipient_name, message):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size
    chrome_options.add_argument("--start-maximized")
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"

    browser = None
    try:
        browser = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)
        wait = WebDriverWait(browser, 10)  # Create a WebDriverWait object

        # Login process
        browser.get('https://www.linkedin.com/login')
        email_input = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        email_input.send_keys(email)
        
        password_input = wait.until(EC.presence_of_element_located((By.ID, 'password')))
        password_input.send_keys(password)
        
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button.click()

        # Verify login success
        wait.until(EC.url_contains('feed'))

        # Navigate to messaging
        browser.get('https://www.linkedin.com/messaging/')
        
        # Search for recipient
        search_message_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search messages"]'))
        )
        search_message_input.clear()
        search_message_input.send_keys(recipient_name)
        time.sleep(2)  # Allow search results to populate

        # Find and click recipient
        user_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//span[text()="{recipient_name}"]'))
        )
        user_element.click()

        # Send message
        message_input = wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
        )
        message_input.send_keys(message)
        message_input.send_keys(Keys.CONTROL + Keys.ENTER)

        # Wait for message to be sent
        time.sleep(2)
        return "Message sent successfully!"

    except TimeoutException as e:
        return f"Operation timed out: {str(e)}"
    except NoSuchElementException as e:
        return f"Element not found: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"
    finally:
        if browser:
            browser.quit()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        recipient_name = request.form.get("recipient_name")
        message = request.form.get("message")

        if not all([email, password, recipient_name, message]):
            return render_template("index.html", error="Please fill in all the fields.")

        try:
            result = linkedin_automation(email, password, recipient_name, message)
            return render_template("index.html", result=result)
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {str(e)}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=False)  # Set debug=False for production