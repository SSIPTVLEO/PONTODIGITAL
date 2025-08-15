from flask_mail import Mail, Message
from flask import current_app, render_template

mail = Mail()

def send_email(to, subject, template, **kwargs):
    msg = Message(
        subject,
        recipients=[to],
        html=render_template(template + ".html", **kwargs),
        sender=current_app.config["MAIL_DEFAULT_SENDER"]
    )
    mail.send(msg)


