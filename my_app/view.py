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
# SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
]


# class for filter email based on defined rules in JSON file.
class FilterEmail:
    def apply_rules(self, service, email, rules):
        """Apply rules on email and take actions."""
        for rule in rules["rules"]:
            conditions = rule["conditions"]
            predicate = rule["predicate"]

            if predicate == "All":
                if all(
                    self.check_condition(email, condition) for condition in conditions
                ):
                    self.perform_actions(service, rule["actions"], email)
                    break
            elif predicate == "Any":
                if any(
                    self.check_condition(email, condition) for condition in conditions
                ):
                    self.perform_actions(service, rule["actions"], email)
                    break

    def check_condition(self, email, condition):
        """Check if the condition is satisfied for the email, based in rules"""
        field = condition["field"].lower()
        predicate = condition["predicate"]
        value = condition["value"]

        if field == "received_time":
            received_time = datetime.fromisoformat(email["received_time"])
            if predicate.lower() == "less than":
                target_time = datetime.fromisoformat(value)
                return received_time < target_time
            elif predicate.lower() == "greater than":
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

    def perform_actions(self, service, actions, email):
        action = actions["action"]
        message_id = email["message_id"]
        old_label = email["label"]
        """Takes action on emails."""
        conn = sqlite3.connect("emails.db")
        c = conn.cursor()
        if action.lower() == "mark as read":
            c.execute(
                f"UPDATE emails SET status='READ' WHERE message_id='{message_id}'"
            )
            service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

        elif action.lower() == "mark as unread":
            c.execute(
                "UPDATE emails SET status='UNREAD' WHERE message_id=?", (message_id,)
            )
            service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
            ).execute()

        elif action.lower() == "move message":
            # Get the email from the database
            new_label_id = actions["label_id"]  # Replace with the desired label ID
            # Move the message
            if old_label != new_label_id:
                c.execute(
                    "UPDATE emails SET label=? WHERE message_id=?",
                    (new_label_id, message_id),
                )
                service.users().messages().modify(
                    userId="me",
                    id=message_id,
                    body={"removeLabelIds": [old_label], "addLabelIds": [new_label_id]},
                ).execute()
                print(message_id, "moved to folder", new_label_id)
        conn.commit()
        conn.close()

    print("Action done")

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

        print("User authorized")
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
            return service, messages

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
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT, subject TEXT, sender sender, snippet TEXT, label TEXT,status TEXT,received_time TIMESTAMP NOT NULL)"""
        )
        conn.commit()
        conn.close()

        logging.info("DB Created successfully")
        print("DB Created successfully")

    def store_emails(self, messages):
        """Stores emails in the database."""
        print("Started Data ingestion")
        conn = sqlite3.connect("emails.db")
        c = conn.cursor()

        """here limiting the email, just for small use case."""

        for message in messages[:100]:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            received_time = datetime.fromtimestamp(int(msg["internalDate"]) / 1000)

            label = msg["labelIds"][-1]

            """we can adjust index as per email structure
                in some of the email its different but we are following majority wise."""
            message_id = msg["id"]
            subject = msg["payload"]["headers"][17]["value"]
            sender = msg["payload"]["headers"][16]["value"]
            body = msg["snippet"]

            """insert data to DB"""
            c.execute(
                "INSERT INTO emails (message_id, subject, sender, snippet, label,status,received_time) VALUES (?, ?, ?,?,?,?,?)",
                (message_id, subject, sender, body, label, "UNREAD", received_time),
            )
        conn.commit()
        conn.close()
        print("Data filled Successfully")
        logging.info("DB filled successfully")
        return "Data Ingestion Done"

    # Step 4: Process emails and take actions using REST API, as per JSON rules.
    def process_emails(self):

        # Authenticate to Gmail API and move the message
        email_process = EmailProcess()
        service, messages = email_process.get_messages()

        with open("./rules.json", "r") as file:
            rules = json.load(file)
        """Processes emails based on some rules and takes actions on them."""

        conn = sqlite3.connect("emails.db")
        c = conn.cursor()
        c.execute("SELECT * FROM emails")
        emails = c.fetchall()

        # calling function from Other class.
        f = FilterEmail()
        for message in emails:
            email_info = {}
            email_info["message_id"] = message[1]
            email_info["from"] = message[3]
            email_info["subject"] = message[2]
            email_info["message"] = message[4]
            email_info["received_time"] = message[7]
            email_info["label"] = message[5]
            print(email_info["label"])
            f.apply_rules(service, email_info, rules)
        conn.close()
