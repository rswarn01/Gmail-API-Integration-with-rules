from my_app import app
from my_app.view import EmailProcess


@app.route("/data_ingestion")
def index():
    ep_object = EmailProcess()
    messages = ep_object.get_messages()
    ep_object.get_messages()
    ep_object.store_emails(messages=messages)
    return "Data Ingestion Done, in DB"


@app.route("/filter_email_rules")
def filtered_email():
    EmailProcess().process_emails()
    return "Email filteration Done, check logs in terminal"
