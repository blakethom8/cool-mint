import logging
import os

from nylas import Client
from nylas.models.drafts import SendMessageRequest
from schemas.nylas_email_schema import Attachment, EmailObject


class NylasService:
    def __init__(self):
        self.client = Client(
            api_key=os.environ.get("NYLAS_API_KEY"),
            api_uri=os.environ.get("NYLAS_API_URI"),
        )

    def download_attachment(self, email: EmailObject, download: bool = False):
        """Download an attachment from Nylas."""
        if not email.attachments:
            raise ValueError("No attachments found in the email")

        attachment: Attachment = email.attachments[0]

        try:
            file_content = self.client.attachments.download_bytes(
                identifier=attachment.grant_id,
                attachment_id=attachment.id,
                query_params={"message_id": email.id},
            )

            if download:
                downloads_dir = "./"
                file_path = os.path.join(downloads_dir, attachment.filename)
                with open(file_path, "wb") as f:
                    f.write(file_content)
                logging.info(f"Attachment saved to {file_path}")

            return {
                "content": file_content,
                "content_type": attachment.content_type,
                "filename": attachment.filename,
            }
        except Exception as e:
            raise Exception(f"Error downloading attachment: {str(e)}")

    def send_email(
        self,
        grant_id: str,
        to: list[str],
        subject: str,
        body: str,
        from_email: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        reply: bool = False,
        reply_to_message_id: str | None = None,
    ):
        """
        Send an email or reply to an email using the Nylas API via draft creation and sending.
        If reply=True, thread_id must be provided.
        """
        request_body: SendMessageRequest = {
            "to": [{"email": email_address} for email_address in to],
            "subject": subject,
            "body": body,
        }
        if from_email:
            request_body["from"] = [
                {"email": email_address} for email_address in from_email
            ]
        if cc:
            request_body["cc"] = [{"email": email_address} for email_address in cc]
        if bcc:
            request_body["bcc"] = [{"email": email_address} for email_address in bcc]
        if reply_to:
            request_body["reply_to"] = [
                {"email": email_address} for email_address in reply_to
            ]
        if reply:
            if not reply_to_message_id:
                raise ValueError("thread_id must be provided when sending a reply.")
            request_body["reply_to_message_id"] = reply_to_message_id

        # Create the draft
        draft = self.client.drafts.create(grant_id, request_body=request_body)
        # Send the draft
        sent_draft = self.client.drafts.send(grant_id, draft[0].id)
        return sent_draft

    def delete_email(self, email: EmailObject):
        """Delete an email using the Nylas API."""
        logging.info(f"Deleting email: {email.id}")
        response = self.client.messages.destroy(
            identifier=email.grant_id, message_id=email.id
        )
        return response

    def add_email_to_folder(self, grant_id: str, message_id: str, folder_id: str):
        """Add an email to a specified folder using the Nylas API."""
        request_body = {"folder_id": folder_id}

        # The identifier for updating messages is the grant_id
        updated_message, request_id = self.client.messages.update(
            identifier=grant_id, message_id=message_id, request_body=request_body
        )
        return updated_message, request_id
