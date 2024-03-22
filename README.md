# Gmail-API-Integration-with-rules

# Gmail Email Processor

This project is a Python script that utilizes the Gmail API to fetch emails from a Gmail account, applies certain rules to these emails, and takes actions based on these rules, such as marking emails as read or unread and moving messages.

## Project Steps:
## SECTION 1:
1. **get_nessage**: The script authenticates to Google's Gmail API using OAuth 2.0 authentication. and get all the emails.

2. **create_db**: we are using Squlite3 db, creating an email table adding Message-Id, Subject, Sender, Snippet, Label, Status, and Time 
3. **Store Emalis**: In the part, we are string emails to the DB table.
4. **Rule-based Processing**: The script applies rules defined in a JSON file to the fetched emails. These rules specify conditions based on email properties such as sender, subject, message content, and received date/time. Depending on whether the conditions are met, the script performs certain actions on the emails.


## SECTION 2:
1. **Apply Rules**: After fetching rules from the JSON file, we are applying those based on condition, predicate or other criteria.

## How It Works:

The script uses Python and the `google-api-python-client` library to interact with the Gmail API. It authenticates using OAuth 2.0 to gain access to the Gmail account. Once authenticated, it fetches emails from the Gmail inbox and applies rules specified in a JSON file. Based on the conditions specified in the rules, the script takes actions on the emails, such as marking them as read or unread and moving messages.

## Steps to Use or Run the Project:

1. **Obtain OAuth 2.0 Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable the Gmail API for your project.
   - Create OAuth 2.0 credentials (OAuth client ID) and download the JSON file containing your client ID and secret.

2. **Install Dependencies**:
   - Ensure you have Python installed on your system.
   - Install the required Python libraries using the following command:
   - We need to install virtual env to run the app. (in pipfile all the module and libraries are mentioned we can use that           file directly to install.
     ```
     pipenv install
     pipenv install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
     ```

3. **Configure Credentials**:
   - Place the downloaded JSON file containing your OAuth 2.0 credentials in the project directory.
   - Rename the JSON file to `credentials.json`.
   - I've not added my file on Git Hub for security reasons.

4. **Define Rules**:
   - Define your email processing rules in a JSON file. Follow the provided template for specifying conditions and actions.

5. **Run the Script**:
   - Execute the Python script by running the following command:
     ```
     python run.py
     ```

6. **Review Output**:
   - The script will fetch emails from your Gmail inbox, apply the specified rules, and take actions accordingly.
   - Review the console output to see the status of email processing and any errors encountered, Can check DB also.

7. **Customize**:
   - Modify the script and rules file as needed to suit your specific requirements.

## Note:
- Ensure that your Gmail account allows access to less secure apps or has 2-step verification enabled with an app password.
- Make sure to handle sensitive data, such as OAuth 2.0 credentials, securely.
