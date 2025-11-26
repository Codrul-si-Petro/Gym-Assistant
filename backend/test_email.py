import os
import smtplib
from email.mime.text import MIMEText

# Load credentials from environment variables
GMAIL_USER = os.getenv("GMAIL_APP_USER")
print(GMAIL_USER)
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
print(GMAIL_PASS)

if not GMAIL_USER or not GMAIL_PASS:
    raise ValueError("Set GMAIL_APP_USER and GMAIL_APP_PASSWORD environment variables")

# Create the message
msg = MIMEText("This is a test email body", "plain")
msg["Subject"] = "Test Email"
msg["From"] = GMAIL_USER
msg["To"] = "codreanu.andrei1125@gmail.com"  # replace with your email

# Send the email
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(GMAIL_USER, GMAIL_PASS)
    server.send_message(msg)

print("Email sent successfully!")
