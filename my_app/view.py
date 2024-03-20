import os.path
import sqlite3
import json
import logging
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# class for filter email based on defined rules in JSON file.
class FilterEmail:
    def apply_rules(self, email, rules):
        """Apply rules on email and take actions."""
        for rule in rules["rules"]:
            conditions = rule["conditions"]
            predicate = rule["predicate"]

            if predicate == "All":
                if all(
                    self.check_condition(email, condition) for condition in conditions
                ):
                    self.perform_actions(rule["actions"], email)
                    break
            elif predicate == "Any":
                if any(
                    self.check_condition(email, condition) for condition in conditions
                ):
                    self.perform_actions(rule["actions"], email)
                    break

    def check_condition(self, email, condition):
        """Check if the condition is satisfied for the email, based in rules"""
        field = condition["field"].lower()
        predicate = condition["predicate"]
        value = condition["value"]

        if field == "Received_Time":
            received_time = datetime.fromisoformat(email["received_time"])
            if predicate == "Less than":
                target_time = datetime.fromisoformat(value)
                return received_time < target_time
            elif predicate == "Greater than":
                target_time = datetime.fromisoformat(value)
                return received_time > target_time
        else:
            email_field_value = email[field].lower()
            value = value.lower()
            if predicate == "Contains":
                return value in email_field_value
            elif predicate == "Does not Contain":
                return value not in email_field_value
            elif predicate == "Equals":
                return email_field_value == value
            elif predicate == "Does not equal":
                return email_field_value != value

    def perform_actions(self, actions, email):
        """Perform actions on the email."""
        for action in actions:
            if action == "Mark as read":
                # Code to mark email as read
                print("Marking email as read:", email)
            elif action == "Mark as unread":
                # Code to mark email as unread
                print("Marking email as unread:", email)
            elif action == "Move Message":
                # Code to move email to another folder
                print("Moving email to another folder:", email)

    def process_emails(self, emails, rules):
        """Process emails based on rules."""
        for email in emails:
            self.apply_rules(email, rules)


# class to connect with Gmail API, and get messages.
class EmailProcess:
    def get_messages(self):

        global service
        """Shows basic usage of the Gmail API.
        Lists the user's email.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        logging.info("Started hitting Gmail api")
        print("Started hitting Gmail api")
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        try:
            # Call the Gmail API
            service = build("gmail", "v1", credentials=creds)
            results = (
                service.users()
                .messages()
                .list(userId="me", labelIds=["INBOX"])
                .execute()
            )
            messages = results.get("messages", [])

            logging.info("Got messages successfully")
            print("Got Email messages from Gamil")
            return messages

        except HttpError as error:
            print(f"An error occurred: {error}")
            return ("Failed to export data", str(error))

    # Step 3: Create a database and store emails
    def create_database(self):
        """Creates a SQLite database and a table to store emails."""
        conn = sqlite3.connect("emails.db")
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS emails
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id, subject TEXT, sender sender, snippet TEXT, label TEXT,received_time TIMESTAMP NOT NULL)"""
        )
        conn.commit()
        conn.close()

        logging.info("DB Created successfully")
        print("DB Created successfully")

    def store_emails(self, messages):
        """Stores emails in the database."""
        conn = sqlite3.connect("emails.db")
        c = conn.cursor()

        """here limiting the email, just for small use case."""

        for message in messages[20:80]:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            received_time = datetime.fromtimestamp(int(msg["internalDate"]) / 1000)

            label = "INBOX"
            """we can adjust index as per email structure
                in some of the email its different but we are following majority wise."""
            message_id = msg["id"]
            subject = msg["payload"]["headers"][17]["value"]

            sender = msg["payload"]["headers"][16]["value"]

            body = msg["snippet"]

            """insert data to DB"""
            c.execute(
                "INSERT INTO emails (message_id, subject, sender, snippet, label,received_time) VALUES (?, ?, ?,?,?,?)",
                (message_id, subject, sender, body, label, received_time),
            )
        conn.commit()
        conn.close()
        print("Data filled Successfully")
        logging.info("DB filled successfully")
        return "Data Ingestion Done"

    # Step 4: Process emails and take actions using REST API, as per JSON rules.
    def process_emails(self):
        with open("./rules.json", "r") as file:
            rules = json.load(file)
        """Processes emails based on some rules and takes actions on them."""

        conn = sqlite3.connect("emails.db")
        c = conn.cursor()
        c.execute("SELECT * FROM emails WHERE label='INBOX'")
        emails = c.fetchall()

        # calling function from Other class.
        f = FilterEmail()
        for message in emails:
            email_info = {}
            email_info["from"] = message[3]
            email_info["subject"] = message[2]
            email_info["message"] = message[4]
            email_info["received_time"] = message[6]
            f.apply_rules(email_info, rules)
        conn.close()
