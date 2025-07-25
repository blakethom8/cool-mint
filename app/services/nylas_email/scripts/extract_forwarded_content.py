#!/usr/bin/env python3
"""
Extract and analyze forwarded email content structure
"""

import os
import sys
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Add the app directory to Python path
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv
load_dotenv()

from database.session import db_session
from database.data_models.email_data import Email


def extract_forwarded_content(html_body):
    """Extract content from forwarded email"""
    soup = BeautifulSoup(html_body, 'html.parser')
    
    # Extract main message (before forwarded content)
    main_message = ""
    
    # Find the forwarded message divider
    forwarded_divider = None
    for elem in soup.find_all(text=re.compile('Forwarded message')):
        forwarded_divider = elem.parent
        break
    
    # Get all text before the forwarded message
    if forwarded_divider:
        current = soup.find('body') or soup
        for elem in current.descendants:
            if elem == forwarded_divider:
                break
            if hasattr(elem, 'text') and elem.name in ['div', 'p', 'span']:
                text = elem.get_text(strip=True)
                if text and "Forwarded message" not in text:
                    main_message += text + " "
    
    # Extract forwarded metadata
    forwarded_info = {}
    gmail_attr = soup.find('div', {'class': 'gmail_attr'})
    if gmail_attr:
        attr_text = gmail_attr.get_text()
        
        # Parse From
        from_match = re.search(r'From:\s*([^<]+)<([^>]+)>', attr_text)
        if from_match:
            forwarded_info['from_name'] = from_match.group(1).strip()
            forwarded_info['from_email'] = from_match.group(2).strip()
        
        # Parse Date
        date_match = re.search(r'Date:\s*([^S]+)', attr_text)
        if date_match:
            forwarded_info['date'] = date_match.group(1).strip()
        
        # Parse Subject
        subject_match = re.search(r'Subject:\s*(.+?)(?:To:|$)', attr_text)
        if subject_match:
            forwarded_info['subject'] = subject_match.group(1).strip()
        
        # Parse To
        to_match = re.search(r'To:\s*([^<]+)<([^>]+)>', attr_text)
        if to_match:
            forwarded_info['to_name'] = to_match.group(1).strip()
            forwarded_info['to_email'] = to_match.group(2).strip()
    
    # Extract forwarded content
    forwarded_content = ""
    quote_container = soup.find('div', {'class': 'gmail_quote_container'})
    if quote_container:
        # Skip the gmail_attr div and get the rest
        for elem in quote_container.find_all(['div', 'p']):
            if 'gmail_attr' not in elem.get('class', []):
                text = elem.get_text(strip=True)
                if text:
                    forwarded_content += text + " "
    
    return {
        'main_message': main_message.strip(),
        'forwarded_info': forwarded_info,
        'forwarded_content': forwarded_content.strip()
    }


def analyze_forwarded_email():
    """Analyze the forwarded lunch email"""
    for session in db_session():
        # Get the forwarded email
        fwd_email = session.query(Email).filter(
            Email.subject.ilike('%Fwd:%')
        ).order_by(Email.date.desc()).first()
        
        if not fwd_email:
            print("No forwarded email found")
            return
        
        print("\n" + "="*80)
        print("FORWARDED EMAIL ANALYSIS")
        print("="*80)
        
        # Basic info
        print(f"\nSubject: {fwd_email.subject}")
        print(f"From: {fwd_email.from_email}")
        print(f"To: {', '.join(fwd_email.to_emails)}")
        
        # Extract structured content
        if fwd_email.body:
            extracted = extract_forwarded_content(fwd_email.body)
            
            print("\n[USER'S REQUEST TO AI]")
            print(extracted['main_message'])
            
            print("\n[FORWARDED EMAIL METADATA]")
            for key, value in extracted['forwarded_info'].items():
                print(f"  {key}: {value}")
            
            print("\n[FORWARDED EMAIL CONTENT]")
            print(extracted['forwarded_content'][:500] + "..." if len(extracted['forwarded_content']) > 500 else extracted['forwarded_content'])
        
        # Extract key information for AI processing
        print("\n" + "="*80)
        print("KEY INFORMATION EXTRACTED")
        print("="*80)
        
        # Parse the user's request
        user_request = extracted['main_message'].lower()
        
        print("\n[IDENTIFIED REQUESTS]")
        if "log" in user_request and "md-to-md" in user_request:
            print("✓ Log MD-to-MD activity")
        if "capture" in user_request and "notes" in user_request:
            print("✓ Capture notes from thread")
        
        print("\n[EXTRACTED ENTITIES]")
        # Extract names
        names = re.findall(r'(?:Dr\.|Devon)\s+([A-Z][a-z]+)', fwd_email.body)
        if names:
            print(f"  Names: {', '.join(set(names))}")
        
        # Extract emails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', fwd_email.body)
        if emails:
            print(f"  Emails: {', '.join(set(emails))}")
        
        # Extract key topics
        print("\n[KEY TOPICS]")
        topics = []
        if "epic" in user_request.lower():
            topics.append("Epic integration")
        if "lunch" in fwd_email.body.lower():
            topics.append("MD-to-MD lunch meeting")
        if "physical therapist" in fwd_email.body.lower():
            topics.append("Physical therapy collaboration")
        if "patients" in user_request.lower():
            topics.append("Patient sharing")
        
        for topic in topics:
            print(f"  - {topic}")
        
        print("\n[ACTION ITEMS IDENTIFIED]")
        if "epic integration" in user_request.lower():
            print("  - Work on Epic integration")
        if "follow up" in fwd_email.body.lower():
            print("  - Follow up items mentioned")
        
        # Show data structure for AI processing
        print("\n" + "="*80)
        print("DATA STRUCTURE FOR AI PROCESSING")
        print("="*80)
        
        ai_data = {
            "email_id": str(fwd_email.id),
            "thread_id": fwd_email.thread_id,
            "user_request": {
                "raw": extracted['main_message'],
                "actions": [
                    "log_md_to_md_activity",
                    "capture_notes_from_thread"
                ]
            },
            "meeting_details": {
                "type": "MD-to-MD lunch",
                "attendees": [
                    {"name": "Devon McDonald", "email": "dvnmcdonald@gmail.com", "role": "Physical Therapist"},
                    {"name": "Blake Thomson", "email": "blakethomson8@gmail.com", "role": "MD"},
                    {"name": "Dr. Uquillis", "role": "MD", "organization": "Cedars"}
                ],
                "date": "Friday, July 25th",
                "topics_discussed": [
                    "Patient sharing",
                    "Epic integration needs"
                ]
            },
            "action_items": [
                "Work on Epic integration"
            ],
            "notes": "Devon McDonald shares patients with us but Epic integration needs improvement"
        }
        
        import json
        print(json.dumps(ai_data, indent=2))
        
        break


if __name__ == "__main__":
    analyze_forwarded_email()