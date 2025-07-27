#!/usr/bin/env python3
"""
Reparse an existing email to populate the new enhanced fields
"""

import os
import sys

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from services.nylas_email_service import NylasEmailService
from database.data_models.email_data import Email
from database.data_models.email_parsed_data import EmailParsed


def reparse_email(email_id: str):
    """Reparse a specific email with enhanced parsing"""
    
    for session in db_session():
        nylas_service = NylasEmailService(session)
        
        # Get the email
        email = session.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            print(f"Email {email_id} not found")
            return
        
        print(f"Original Email:")
        print(f"Subject: {email.subject}")
        print(f"From: {email.from_email}")
        print(f"Is Forwarded (old): {email.is_forwarded}")
        
        # Apply parsing
        content = email.body_plain or email.body
        
        # Clean content
        email.clean_body = nylas_service._clean_email_content(email.body, email.body_plain)
        
        # Detect forwarding
        email.is_forwarded = nylas_service._detect_forwarded_email(email.subject, email.clean_body)
        
        # Parse forwarded content
        if email.is_forwarded:
            user_instruction, extracted_thread = nylas_service._parse_forwarded_email(email.clean_body)
            email.user_instruction = user_instruction
            email.extracted_thread = extracted_thread
        
        # Save changes
        session.commit()
        
        print(f"\nUpdated Email:")
        print(f"Is Forwarded: {email.is_forwarded}")
        print(f"Has User Instruction: {email.has_user_instruction}")
        
        if email.user_instruction:
            print(f"\nUser Instruction:")
            print(email.user_instruction)
        
        if email.extracted_thread:
            print(f"\nExtracted Thread Preview:")
            print(email.extracted_thread[:500] + "...")
        
        print(f"\nConversation for LLM:")
        print(email.conversation_for_llm[:500] + "...")


if __name__ == "__main__":
    # Reparse the forwarded Ortho Lunch email
    reparse_email("7c1b11f8-0ed6-4bb0-94b1-a438fea2b973")