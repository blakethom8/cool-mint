#!/usr/bin/env python3
"""Data validation for email action extractions"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import re

# Add parent directories to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))


class ValidationResult(BaseModel):
    """Result of a validation check"""
    field: str
    is_valid: bool
    message: str
    severity: str = "warning"  # error, warning, info
    suggested_value: Optional[Any] = None


class CallLogValidator:
    """Validates extracted call log data"""
    
    def __init__(self):
        self.physician_titles = {'dr', 'dr.', 'md', 'm.d.', 'do', 'd.o.'}
        self.valid_settings = {'In-Person', 'Virtual', 'Phone', 'Hybrid'}
        self.valid_mno_types = {'MD_to_MD_Visits', 'BD_Outreach', 'Internal_Meeting'}
        
    def validate_all(self, data: Dict) -> List[ValidationResult]:
        """Run all validations on extracted data"""
        results = []
        
        # Validate each field
        results.extend(self.validate_subject(data.get('subject', '')))
        results.extend(self.validate_participants(data.get('participants', [])))
        results.extend(self.validate_date(data.get('activity_date')))
        results.extend(self.validate_duration(data.get('duration_minutes')))
        results.extend(self.validate_md_to_md_consistency(data))
        results.extend(self.validate_meeting_setting(data.get('meeting_setting')))
        
        return results
    
    def validate_subject(self, subject: str) -> List[ValidationResult]:
        """Validate subject line"""
        results = []
        
        if not subject:
            results.append(ValidationResult(
                field="subject",
                is_valid=False,
                message="Subject is required",
                severity="error"
            ))
            return results
        
        # Check length
        if len(subject) < 10:
            results.append(ValidationResult(
                field="subject",
                is_valid=False,
                message="Subject too short (min 10 characters)",
                severity="warning"
            ))
        elif len(subject) > 100:
            results.append(ValidationResult(
                field="subject",
                is_valid=False,
                message="Subject too long (max 100 characters)",
                severity="warning",
                suggested_value=subject[:97] + "..."
            ))
        
        # Check for MD-to-MD consistency
        if 'md-to-md' in subject.lower() or 'md to md' in subject.lower():
            if 'MD-to-MD' not in subject:
                results.append(ValidationResult(
                    field="subject",
                    is_valid=False,
                    message="Use consistent 'MD-to-MD' formatting",
                    severity="info",
                    suggested_value=re.sub(r'md[\s-]?to[\s-]?md', 'MD-to-MD', subject, flags=re.IGNORECASE)
                ))
        
        return results
    
    def validate_participants(self, participants: List[Dict]) -> List[ValidationResult]:
        """Validate participant data"""
        results = []
        
        if not participants:
            results.append(ValidationResult(
                field="participants",
                is_valid=False,
                message="At least one participant required",
                severity="error"
            ))
            return results
        
        # Check each participant
        for i, participant in enumerate(participants):
            if not isinstance(participant, dict):
                results.append(ValidationResult(
                    field=f"participants[{i}]",
                    is_valid=False,
                    message="Participant must be a dictionary with name and role",
                    severity="error"
                ))
                continue
                
            name = participant.get('name', '')
            if not name:
                results.append(ValidationResult(
                    field=f"participants[{i}].name",
                    is_valid=False,
                    message="Participant name is required",
                    severity="error"
                ))
            
            # Check for physician titles
            if self._has_physician_title(name) and 'role' in participant:
                role = participant.get('role', '').lower()
                if not any(term in role for term in ['physician', 'doctor', 'md', 'specialist']):
                    results.append(ValidationResult(
                        field=f"participants[{i}].role",
                        is_valid=False,
                        message=f"Role doesn't match physician title for {name}",
                        severity="warning"
                    ))
        
        return results
    
    def validate_date(self, activity_date: Optional[str]) -> List[ValidationResult]:
        """Validate activity date"""
        results = []
        
        if not activity_date:
            results.append(ValidationResult(
                field="activity_date",
                is_valid=False,
                message="Activity date should be specified",
                severity="warning"
            ))
            return results
        
        # Try to parse date
        try:
            if isinstance(activity_date, str):
                date = datetime.fromisoformat(activity_date.replace('Z', '+00:00'))
            else:
                date = activity_date
                
            # Check if date is in future
            if date > datetime.now():
                results.append(ValidationResult(
                    field="activity_date",
                    is_valid=False,
                    message="Activity date cannot be in the future",
                    severity="error"
                ))
            
            # Check if date is too old
            elif date < datetime.now() - timedelta(days=90):
                results.append(ValidationResult(
                    field="activity_date",
                    is_valid=False,
                    message="Activity date is over 90 days old",
                    severity="warning"
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                field="activity_date",
                is_valid=False,
                message=f"Invalid date format: {str(e)}",
                severity="error"
            ))
        
        return results
    
    def validate_duration(self, duration: Optional[int]) -> List[ValidationResult]:
        """Validate duration"""
        results = []
        
        if duration is None:
            return results  # Duration is optional
        
        if not isinstance(duration, (int, float)):
            results.append(ValidationResult(
                field="duration_minutes",
                is_valid=False,
                message="Duration must be a number",
                severity="error"
            ))
        elif duration <= 0:
            results.append(ValidationResult(
                field="duration_minutes",
                is_valid=False,
                message="Duration must be positive",
                severity="error"
            ))
        elif duration > 480:  # 8 hours
            results.append(ValidationResult(
                field="duration_minutes",
                is_valid=False,
                message="Duration seems too long (over 8 hours)",
                severity="warning"
            ))
        
        return results
    
    def validate_md_to_md_consistency(self, data: Dict) -> List[ValidationResult]:
        """Validate MD-to-MD field consistency"""
        results = []
        
        is_md_to_md = data.get('is_md_to_md', False)
        mno_type = data.get('mno_type', '')
        subject = data.get('subject', '').lower()
        participants = data.get('participants', [])
        
        # Count physicians
        physician_count = sum(1 for p in participants 
                            if self._has_physician_title(p.get('name', '')))
        
        # Check consistency
        if is_md_to_md:
            if mno_type != 'MD_to_MD_Visits':
                results.append(ValidationResult(
                    field="mno_type",
                    is_valid=False,
                    message="MNO type should be 'MD_to_MD_Visits' for MD-to-MD activities",
                    severity="error",
                    suggested_value="MD_to_MD_Visits"
                ))
            
            if physician_count < 2:
                results.append(ValidationResult(
                    field="is_md_to_md",
                    is_valid=False,
                    message="MD-to-MD requires at least 2 physicians",
                    severity="warning"
                ))
            
            if 'md-to-md' not in subject and 'md to md' not in subject:
                results.append(ValidationResult(
                    field="subject",
                    is_valid=False,
                    message="MD-to-MD activities should mention it in subject",
                    severity="info"
                ))
        
        return results
    
    def validate_meeting_setting(self, setting: str) -> List[ValidationResult]:
        """Validate meeting setting"""
        results = []
        
        if not setting:
            results.append(ValidationResult(
                field="meeting_setting",
                is_valid=False,
                message="Meeting setting is required",
                severity="error"
            ))
        elif setting not in self.valid_settings:
            results.append(ValidationResult(
                field="meeting_setting",
                is_valid=False,
                message=f"Invalid setting. Must be one of: {', '.join(self.valid_settings)}",
                severity="error",
                suggested_value="In-Person"
            ))
        
        return results
    
    def _has_physician_title(self, name: str) -> bool:
        """Check if name contains physician title"""
        name_lower = name.lower()
        return any(f' {title}' in name_lower or name_lower.startswith(f'{title} ') 
                  for title in self.physician_titles)


class ValidationSummary:
    """Summarizes validation results"""
    
    @staticmethod
    def summarize(results: List[ValidationResult]) -> Dict:
        """Create summary of validation results"""
        summary = {
            'total_checks': len(results),
            'errors': sum(1 for r in results if r.severity == 'error'),
            'warnings': sum(1 for r in results if r.severity == 'warning'),
            'info': sum(1 for r in results if r.severity == 'info'),
            'is_valid': all(r.is_valid or r.severity != 'error' for r in results),
            'fields_with_issues': list(set(r.field for r in results if not r.is_valid))
        }
        
        # Group by field
        by_field = {}
        for result in results:
            if result.field not in by_field:
                by_field[result.field] = []
            by_field[result.field].append(result)
        
        summary['by_field'] = by_field
        
        return summary


# Example usage
def validate_extraction_example():
    """Example of validating extracted data"""
    
    # Sample extracted data
    extracted_data = {
        'subject': 'md to md lunch with Dr. Smith',
        'participants': [
            {'name': 'Dr. John Smith', 'role': 'Cardiologist'},
            {'name': 'Blake Thomson', 'role': 'Physician Liaison'}
        ],
        'activity_date': '2024-12-15T12:00:00',
        'duration_minutes': 90,
        'is_md_to_md': True,
        'mno_type': 'BD_Outreach',  # Wrong type
        'meeting_setting': 'In-Person'
    }
    
    # Validate
    validator = CallLogValidator()
    results = validator.validate_all(extracted_data)
    
    # Show results
    print("Validation Results:")
    print("-" * 50)
    
    for result in results:
        icon = "✓" if result.is_valid else "✗"
        print(f"{icon} {result.field}: {result.message} [{result.severity}]")
        if result.suggested_value:
            print(f"   Suggested: {result.suggested_value}")
    
    # Show summary
    summary = ValidationSummary.summarize(results)
    print("\nSummary:")
    print(f"Total checks: {summary['total_checks']}")
    print(f"Errors: {summary['errors']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Valid for submission: {summary['is_valid']}")


if __name__ == '__main__':
    print("Data Validation for Email Actions")
    print("=" * 50)
    validate_extraction_example()