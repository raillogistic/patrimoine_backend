import imaplib
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
from django.core.mail import get_connection, send_mail, send_mass_mail


def send_and_save_email(
    subject,
    content,
    recipients,
    backend_config,
    cc=[],
    cci=[],
    folder=None,
    attachements=None,
):
    # Send the email using SMTP
    IMAP_SERVER = backend_config.get("IMAP_SERVER")
    EMAIL_USER = backend_config.get("EMAIL_USER")
    EMAIL_PASSWORD = backend_config.get("EMAIL_PASSWORD")
    SMTP_SERVER = backend_config.get("SMTP_SERVER")
    SMTP_PORT = backend_config.get("SMTP_PORT")
    if cc is None:
        cc = []
    if cci is None:
        cci = []
    # try:
    # Step 1: Create the email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(recipients)
    msg["Cc"] = ", ".join(cc)  # Add CC recipients to the email headers
    msg["Subject"] = subject
    print(
        "xxxxxxxxxxx",
        attachements,
    )

    msg.attach(MIMEText(content, "html"))  # Use 'plain' for plain text emails

    if attachements is None:
        attachements = []
    for file_field in attachements:
        file_name = file_field.name.split("/")[-1]  # Get the file's name
        with file_field.open("rb") as file:  # Open each Django FileField
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())  # Read the file content
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{file_name}"',
            )
            msg.attach(part)

    # if attachment_file:
    #     if attachment_file_name is None:
    #         attachment_file_name = "attachment.pdf"
    #     # Handle file object directly
    #     part = MIMEBase("application", "octet-stream")
    #     part.set_payload(attachment_file.read())
    #     encoders.encode_base64(part)
    #     part.add_header(
    #         "Content-Disposition",
    #         f'attachment; filename="{attachment_file_name}.pdf"',
    #     )
    #     msg.attach(part)

    # Combine recipients, CC, and BCC for sending
    all_recipients = recipients + cc + cci

    # Step 2: Send the email via SMTP
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()  # Enable encryption
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_USER, all_recipients, msg.as_string())
        print("Email sent successfully.")

    # Step 3: Save the email to the 'Sent' folder via IMAP
    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap:
        imap.login(EMAIL_USER, EMAIL_PASSWORD)
        current_date = datetime.now(pytz.UTC)
        imap.append(
            f"INBOX.{folder}",
            "",
            imaplib.Time2Internaldate(current_date),
            msg.as_bytes(),
        )
        print("Email saved to 'Sent' folder successfully.")


# except Exception as e:
#     print(f"An error occurred: {e}")


def send_emails(
    subject,
    message,
    recipient_list,
    html_message=None,
    from_email=None,
    backend_config=None,
):
    if backend_config:
        connection = get_connection(
            host=backend_config.get("EMAIL_HOST"),
            port=backend_config.get("EMAIL_PORT"),
            username=backend_config.get("EMAIL_HOST_USER"),
            password=backend_config.get("EMAIL_HOST_PASSWORD"),
            use_tls=backend_config.get("EMAIL_USE_TLS", False),
            use_ssl=backend_config.get("EMAIL_USE_SSL", False),
        )
    else:
        # Use default backend if no config is provided
        connection = get_connection()

    send_mail(
        subject,
        message,
        from_email or connection.username,
        recipient_list,
        connection=connection,
        html_message=html_message,
    )


def send_email(to, title, body, html):
    send_mail(
        from_email="erp@rail-logistic.dz",
        message="",
        recipient_list=(to,),
        subject=title,
        html_message=html,
        fail_silently=False,
    )
