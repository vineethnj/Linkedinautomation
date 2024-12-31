import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.options import Options

# Function to automate LinkedIn messaging
def linkedin_automation(email, password, recipient_name, message):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize the Chrome browser
    browser = webdriver.Chrome(options=chrome_options)
    # Initialize the Chrome browser
    

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
            st.success("Login successful!")
        else:
            st.error("Login failed.")
            return

        # Navigate to the messaging section
        st.write("Navigating to messaging section...")
        browser.get('https://www.linkedin.com/messaging/')

        # Wait for the messaging page to load
        time.sleep(5)

        # Locate the "Search Message" input field
        st.write("Locating search message input field...")
        search_message_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search messages"]'))
        )
        search_message_input.send_keys(recipient_name)

        # Wait for the search results to load
        time.sleep(3)

        # Locate the user in the search results and click on it
        st.write(f"Locating user '{recipient_name}'...")
        user_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//span[text()="{recipient_name}"]'))
        )
        user_element.click()

        # Wait for the chat window to load
        time.sleep(3)

        # Locate the message input field and enter the message
        st.write("Locating message input field...")
        message_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
        )
        message_input.send_keys(message)

        # Send the message using Ctrl + Enter
        st.write("Sending message with Ctrl + Enter...")
        message_input.send_keys(Keys.CONTROL + Keys.ENTER)

        # Wait for the message to be sent
        time.sleep(3)

        st.success("Message sent successfully!")

    finally:
        # Close the browser
        browser.quit()

# Streamlit UI
st.title("LinkedIn Message Automation")

# Input fields
email = st.text_input("Enter your LinkedIn email:")
password = st.text_input("Enter your LinkedIn password:", type="password")
recipient_name = st.text_input("Enter the recipient's name:")
message = st.text_area("Enter your message:")

# Button to trigger the automation
if st.button("Send Message"):
    if email and password and recipient_name and message:
        linkedin_automation(email, password, recipient_name, message)
    else:
        st.error("Please fill in all the fields.")