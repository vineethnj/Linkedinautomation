from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

# Function to automate LinkedIn messaging
def linkedin_automation(email, password, recipient_name, message):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Specify the Chrome binary location
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"

    # Initialize the Chrome browser
    browser = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

    try:
        # Open LinkedIn login page
        browser.get('https://www.linkedin.com/login')

        # Wait for the page to load
        time.sleep(2)

        # Locate the email input field and enter the email
        email_input = browser.find_element(By.ID, 'username')
        email_input.send_keys(email)

        # Locate the password input field and enter the password
        password_input = browser.find_element(By.ID, 'password')
        password_input.send_keys(password)

        # Locate the login button and click it
        login_button = browser.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()

        # Wait for the login process to complete
        time.sleep(5)

        # Verify if login was successful by checking the page title or URL
        if 'feed' in browser.current_url:
            print("Login successful!")
        else:
            print("Login failed.")
            return "Login failed."

        # Navigate to the messaging section
        print("Navigating to messaging section...")
        browser.get('https://www.linkedin.com/messaging/')

        # Wait for the messaging page to load
        time.sleep(5)

        # Locate the "Search Message" input field
        print("Locating search message input field...")
        search_message_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search messages"]'))
        )
        search_message_input.send_keys(recipient_name)

        # Wait for the search results to load
        time.sleep(3)

        # Locate the user in the search results and click on it
        print(f"Locating user '{recipient_name}'...")
        user_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//span[text()="{recipient_name}"]'))
        )
        user_element.click()

        # Wait for the chat window to load
        time.sleep(3)

        # Locate the message input field and enter the message
        print("Locating message input field...")
        message_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
        )
        message_input.send_keys(message)

        # Send the message using Ctrl + Enter
        print("Sending message with Ctrl + Enter...")
        message_input.send_keys(Keys.CONTROL + Keys.ENTER)

        # Wait for the message to be sent
        time.sleep(3)

        print("Message sent successfully!")
        return "Message sent successfully!"

    finally:
        # Close the browser
        browser.quit()

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        recipient_name = request.form.get("recipient_name")
        message = request.form.get("message")

        if email and password and recipient_name and message:
            result = linkedin_automation(email, password, recipient_name, message)
            return render_template("index.html", result=result)
        else:
            return render_template("index.html", error="Please fill in all the fields.")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)