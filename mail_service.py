from sendgrid.helpers.mail import From, To, Subject, PlainTextContent, Mail
from flask import url_for
from random import randint
import sendgrid
import os

# If accepted, you need to do a few things:
# 1. Change the link into whatever your link is (you also may want to write an email template)
# 2. Add a change password feature (it wasn't a priority at the time)
sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

def email_verify(email_address, token):
    message = Mail(from_email=From('pledoit@bu.edu', "BU Computer Science Ambassadors"),
                   to_emails=To(email_address, ""),
                   subject=Subject("Email Verification"),
                   plain_text_content=PlainTextContent("Hello, this is from the BU Computer Science Ambassadors. " +
                                                       "You've signed up for an account or for our mailing service." +
                                                       "Please click the link below to verify.\n" +
                                                       "https://bucsawebsite.specificlanguage.repl.co" + url_for("verify") + "?token=" + token
                                                       + "\n\n\n"
                                                       + " By doing this, you're also signing up for our email list."))
    sg.send(message)


def send_to_mailing_list(to_emails, message, subject):
    message = Mail(from_email=From('pledoit@bu.edu', "BU Computer Science Ambassadors"),
                  to_emails=to_emails,
                  subject=Subject(subject),
                  plain_text_content=PlainTextContent(message))
    sg.send(message)
    # just a quick editor's note.
    # It's almost trivial to add an unsubscribe option at the bottom, but I'm too lazy to do it right now!
    # backend is definitely not a priority.


def generate_token():
    token = ""
    for i in range(10):
        n = randint(0, 2)
        if n == 0:
            c = randint(48, 57)
        elif n == 1:
            c = randint(65, 90)
        else:
            c = randint(97, 122)
        token += chr(c)
    return token