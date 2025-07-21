"""
Enhanced Database Seeding Script for Provider CRM - Large Dataset

This script generates a comprehensive, large-scale realistic example dataset for the Provider CRM application.
It creates providers, visits, outreach efforts, and referrals with proper relationships and realistic
healthcare industry data focused on the San Francisco Bay Area.

Enhanced features:
- Much larger provider pools (200+ per specialty)
- More visit records per provider (12-24 per year)
- Expanded geographic coverage within Bay Area
- More realistic provider groups and specialties
- Enhanced data variety and relationships

Usage:
    python -m database.seed_data_expanded

Or from the seeding script:
    python seed_database_expanded.py
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import func
from database.session import db_session
from database.data_models.provider_crm import (
    Provider,
    ProviderVisits,
    OutreachEfforts,
    ProviderReferrals,
)


class EnhancedCRMDataSeeder:
    """Generates comprehensive, large-scale realistic example data for the CRM database focused on San Francisco Bay Area."""

    # Expanded healthcare specialties for comprehensive Bay Area coverage
    SPECIALTIES = [
        "Cardiology",
        "Neurology",
        "Orthopedic Surgery",
        "Gastroenterology",
        "Dermatology",
        "Endocrinology",
        "Oncology",
        "Primary Care",
        "Pediatrics",
        "Ophthalmology",
        "Pulmonology",
        "Rheumatology",
        "Urology",
        "Otolaryngology",
        "Anesthesiology",
        "Emergency Medicine",
        "Radiology",
        "Pathology",
        "Psychiatry",
        "Obstetrics and Gynecology",
        "General Surgery",
        "Plastic Surgery",
        "Nephrology",
        "Hematology",
        "Infectious Disease",
        "Pain Management",
        "Sports Medicine",
        "Geriatrics",
        "Allergy and Immunology",
        "Nuclear Medicine",
    ]

    # Expanded list of names for more variety
    FIRST_NAMES = [
        "James",
        "Mary",
        "John",
        "Patricia",
        "Robert",
        "Jennifer",
        "Michael",
        "Linda",
        "William",
        "Elizabeth",
        "David",
        "Barbara",
        "Richard",
        "Susan",
        "Joseph",
        "Jessica",
        "Thomas",
        "Sarah",
        "Christopher",
        "Karen",
        "Charles",
        "Nancy",
        "Daniel",
        "Lisa",
        "Matthew",
        "Betty",
        "Anthony",
        "Helen",
        "Mark",
        "Sandra",
        "Donald",
        "Donna",
        "Steven",
        "Carol",
        "Paul",
        "Ruth",
        "Andrew",
        "Sharon",
        "Joshua",
        "Michelle",
        "Kenneth",
        "Laura",
        "Kevin",
        "Sarah",
        "Brian",
        "Kimberly",
        "George",
        "Deborah",
        "Edward",
        "Dorothy",
        "Ronald",
        "Lisa",
        "Timothy",
        "Nancy",
        "Jason",
        "Karen",
        "Jeffrey",
        "Betty",
        "Ryan",
        "Helen",
        "Jacob",
        "Sandra",
        "Gary",
        "Donna",
        "Nicholas",
        "Carol",
        "Eric",
        "Ruth",
        "Jonathan",
        "Sharon",
        "Stephen",
        "Michelle",
        "Larry",
        "Laura",
        "Justin",
        "Sarah",
        "Scott",
        "Kimberly",
        "Brandon",
        "Deborah",
        "Benjamin",
        "Dorothy",
        "Samuel",
        "Amy",
        "Gregory",
        "Angela",
        "Frank",
        "Ashley",
        "Raymond",
        "Brenda",
        "Alexander",
        "Emma",
        "Patrick",
        "Olivia",
        "Jack",
        "Cynthia",
        "Dennis",
        "Marie",
        "Jerry",
        "Janet",
        "Tyler",
        "Catherine",
        "Aaron",
        "Frances",
        "Jose",
        "Christine",
        "Henry",
        "Samantha",
        "Adam",
        "Debra",
        "Douglas",
        "Rachel",
        "Nathan",
        "Carolyn",
        "Peter",
        "Virginia",
        "Zachary",
        "Maria",
        "Kyle",
        "Heather",
    ]

    LAST_NAMES = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
        "Taylor",
        "Moore",
        "Jackson",
        "Martin",
        "Lee",
        "Perez",
        "Thompson",
        "White",
        "Harris",
        "Sanchez",
        "Clark",
        "Ramirez",
        "Lewis",
        "Robinson",
        "Walker",
        "Young",
        "Allen",
        "King",
        "Wright",
        "Scott",
        "Torres",
        "Nguyen",
        "Hill",
        "Flores",
        "Green",
        "Adams",
        "Nelson",
        "Baker",
        "Hall",
        "Rivera",
        "Campbell",
        "Mitchell",
        "Carter",
        "Roberts",
        "Gomez",
        "Phillips",
        "Evans",
        "Turner",
        "Diaz",
        "Parker",
        "Cruz",
        "Edwards",
        "Collins",
        "Reyes",
        "Stewart",
        "Morris",
        "Morales",
        "Murphy",
        "Cook",
        "Rogers",
        "Gutierrez",
        "Ortiz",
        "Morgan",
        "Cooper",
        "Peterson",
        "Bailey",
        "Reed",
        "Kelly",
        "Howard",
        "Ramos",
        "Kim",
        "Cox",
        "Ward",
        "Richardson",
        "Watson",
        "Brooks",
        "Chavez",
        "Wood",
        "James",
        "Bennett",
        "Gray",
        "Mendoza",
        "Ruiz",
        "Hughes",
        "Price",
        "Alvarez",
        "Castillo",
        "Sanders",
        "Patel",
        "Myers",
        "Long",
        "Ross",
        "Foster",
        "Jimenez",
        "Powell",
        "Jenkins",
        "Perry",
        "Russell",
        "Sullivan",
        "Bell",
        "Coleman",
        "Butler",
        "Henderson",
        "Barnes",
        "Gonzales",
        "Fisher",
        "Vasquez",
        "Simmons",
        "Romero",
        "Jordan",
        "Patterson",
        "Alexander",
        "Hamilton",
        "Graham",
    ]

    # Significantly expanded provider groups for realistic Bay Area coverage
    PROVIDER_GROUPS = [
        # Major Health Systems
        "UCSF Health Network",
        "Stanford Health Care",
        "Kaiser Permanente Northern California",
        "Sutter Health Bay Area",
        "California Pacific Medical Center",
        "John Muir Health",
        "Washington Hospital Healthcare System",
        "Mills-Peninsula Health Services",
        "El Camino Health",
        "Santa Clara Valley Medical Center",
        # Specialty Groups - Cardiology
        "Bay Area Cardiology Associates",
        "SF Heart & Vascular Institute",
        "Peninsula Cardiac Center",
        "East Bay Cardiovascular Group",
        "Marin Heart Institute",
        "South Bay Cardiology Partners",
        "Golden Gate Heart Center",
        "Pacific Cardiac Associates",
        "North Bay Heart Specialists",
        "Silicon Valley Cardiology",
        # Specialty Groups - Neurology
        "SF NeuroCare Partners",
        "Bay Area Neurology Group",
        "Peninsula Neurological Associates",
        "East Bay Neuroscience Center",
        "Marin Neurology Clinic",
        "South Bay Brain & Spine",
        "Golden Gate Neurology",
        "Pacific Neurological Institute",
        "North Bay Neuro Associates",
        "Silicon Valley Neurology",
        # Specialty Groups - Orthopedics
        "Golden Gate Orthopedics",
        "Bay Area Bone & Joint",
        "Peninsula Orthopedic Associates",
        "East Bay Sports Medicine",
        "Marin Orthopedic Group",
        "South Bay Spine Center",
        "SF Orthopedic Institute",
        "Pacific Joint & Bone",
        "North Bay Orthopedics",
        "Silicon Valley Spine",
        # Primary Care Groups
        "Bay Area Family Practice",
        "SF Primary Care Partners",
        "Peninsula Medical Group",
        "East Bay Family Medicine",
        "Marin Primary Care",
        "South Bay Family Health",
        "Golden Gate Family Physicians",
        "Pacific Primary Care",
        "North Bay Family Practice",
        "Silicon Valley Medical Group",
        # Multi-Specialty Groups
        "Bay Area Comprehensive Care",
        "SF Medical Specialists",
        "Peninsula Health Partners",
        "East Bay Medical Associates",
        "Marin Specialty Clinic",
        "South Bay Healthcare Group",
        "Golden Gate Medical Center",
        "Pacific Specialty Partners",
        "North Bay Health Alliance",
        "Silicon Valley Specialists",
        # Additional Specialty Groups
        "Bay Digestive Health Partners",
        "SF Skin & Laser Center",
        "Peninsula Endocrine Associates",
        "East Bay Cancer Center",
        "Marin Pediatric Group",
        "South Bay Eye Institute",
        "Golden Gate Pulmonary",
        "Pacific Rheumatology",
        "North Bay Urology",
        "Silicon Valley ENT",
        # Independent Practice Groups
        "Bay Area Independent Physicians",
        "SF Solo Practice Network",
        "Peninsula Medical Partners",
        "East Bay Provider Alliance",
        "Marin Medical Collective",
        "South Bay Physician Group",
        "Golden Gate Healthcare",
        "Pacific Medical Network",
        "North Bay Medical Group",
        "Silicon Valley Health Partners",
    ]

    # Parent healthcare organizations and systems in the Bay Area
    PARENT_ORGANIZATIONS = [
        # Major Health Systems
        "UCSF Health",
        "Stanford Health Care",
        "Kaiser Permanente Northern California",
        "Sutter Health",
        "CommonSpirit Health",
        "John Muir Health",
        "El Camino Health",
        "Santa Clara Valley Medical Center",
        # Large Medical Groups
        "Palo Alto Medical Foundation",
        "Brown & Toland Physicians",
        "Hill Physicians Medical Group",
        "One Medical",
        # Specialty-Specific Groups
        "Bay Area Surgical Specialists",
        "Northern California Cardiovascular Group",
        "Bay Area Cancer Care",
        "Peninsula Orthopedic Associates",
        "Golden Gate Neurosurgery",
        "Bay Area Dermatology Associates",
        # Independent Practice Indicator
        "Independent Practice",
    ]

    # Expanded Bay Area locations with more comprehensive coverage
    LOCATIONS = [
        # San Francisco
        ("San Francisco", "CA", "94102", "450 Sutter St"),
        ("San Francisco", "CA", "94115", "2333 Buchanan St"),
        ("San Francisco", "CA", "94107", "1001 Potrero Ave"),
        ("San Francisco", "CA", "94118", "3838 California St"),
        ("San Francisco", "CA", "94122", "1701 Divisadero St"),
        ("San Francisco", "CA", "94158", "505 Parnassus Ave"),
        ("San Francisco", "CA", "94110", "3555 Cesar Chavez St"),
        ("San Francisco", "CA", "94117", "1001 Potrero Ave"),
        # Oakland/East Bay
        ("Oakland", "CA", "94609", "747 52nd St"),
        ("Oakland", "CA", "94611", "3100 Telegraph Ave"),
        ("Berkeley", "CA", "94704", "2450 Ashby Ave"),
        ("Fremont", "CA", "94538", "39141 Civic Center Dr"),
        ("Hayward", "CA", "94541", "27400 Hesperian Blvd"),
        ("Pleasanton", "CA", "94566", "5555 W Las Positas Blvd"),
        ("Concord", "CA", "94520", "2540 East St"),
        ("Walnut Creek", "CA", "94596", "1425 S Main St"),
        ("Richmond", "CA", "94804", "901 Nevin Ave"),
        ("Antioch", "CA", "94509", "4643 Lone Tree Way"),
        # Peninsula
        ("Palo Alto", "CA", "94304", "725 Welch Rd"),
        ("San Mateo", "CA", "94401", "100 S San Mateo Dr"),
        ("Redwood City", "CA", "94063", "1150 Veterans Blvd"),
        ("Mountain View", "CA", "94040", "701 E El Camino Real"),
        ("Menlo Park", "CA", "94025", "1215 Crane St"),
        ("Foster City", "CA", "94404", "1001 Sneath Ln"),
        ("Burlingame", "CA", "94010", "1740 Marco Polo Way"),
        ("San Carlos", "CA", "94070", "455 Hickey Blvd"),
        ("Millbrae", "CA", "94030", "1777 Borel Pl"),
        ("Half Moon Bay", "CA", "94019", "225 S Cabrillo Hwy"),
        # South Bay
        ("San Jose", "CA", "95128", "751 S Bascom Ave"),
        ("Santa Clara", "CA", "95051", "700 Lawrence Expy"),
        ("Sunnyvale", "CA", "94086", "401 Old San Francisco Rd"),
        ("Cupertino", "CA", "95014", "10100 Torre Ave"),
        ("Campbell", "CA", "95008", "1875 S Bascom Ave"),
        ("Los Gatos", "CA", "95032", "815 Pollard Rd"),
        ("Saratoga", "CA", "95070", "13425 Sousa Ln"),
        ("Milpitas", "CA", "95035", "1601 E Calaveras Blvd"),
        ("Gilroy", "CA", "95020", "9030 Monterey St"),
        ("Morgan Hill", "CA", "95037", "17400 Depot St"),
        # North Bay
        ("Daly City", "CA", "94015", "1900 Sullivan Ave"),
        ("San Rafael", "CA", "94903", "99 Montecillo Rd"),
        ("Vallejo", "CA", "94589", "975 Sereno Dr"),
        ("Santa Rosa", "CA", "95403", "1165 Montgomery Dr"),
        ("Petaluma", "CA", "94952", "1425 C St"),
        ("Napa", "CA", "94558", "1001 Trancas St"),
        ("Fairfield", "CA", "94533", "1010 Nut Tree Rd"),
        ("Vacaville", "CA", "95687", "1010 Nut Tree Rd"),
        ("Novato", "CA", "94945", "1625 Hill Rd"),
        ("Mill Valley", "CA", "94941", "1010 Sir Francis Drake Blvd"),
    ]

    OUTREACH_TYPES = [
        "phone_call",
        "email",
        "in_person_visit",
        "conference_meeting",
        "lunch_meeting",
        "webinar",
        "medical_conference",
        "hospital_visit",
        "virtual_meeting",
        "breakfast_meeting",
        "medical_symposium",
        "clinical_rounds_visit",
        "educational_seminar",
        "networking_event",
        "dinner_meeting",
    ]

    OUTREACH_OUTCOMES = [
        "contacted",
        "no_answer",
        "left_voicemail",
        "meeting_scheduled",
        "referral_committed",
        "needs_follow_up",
        "not_interested",
        "information_requested",
        "contract_discussion",
        "pricing_inquiry",
        "service_demo_scheduled",
        "trial_period_agreed",
        "partnership_interest",
        "follow_up_in_quarter",
    ]

    OUTREACH_SPECIALISTS = [
        "Sarah Johnson",
        "Mike Chen",
        "Lisa Rodriguez",
        "David Kim",
        "Jennifer Walsh",
        "Robert Taylor",
        "Amanda Foster",
        "Chris Martinez",
        "Emily Davis",
        "Brian Wilson",
        "Jessica Brown",
        "Kevin Lee",
        "Michelle Garcia",
        "Steven Anderson",
        "Rachel Miller",
        "Daniel Thompson",
        "Ashley White",
        "Matthew Harris",
        "Lauren Clark",
        "Andrew Lewis",
        "Stephanie Young",
        "Joshua Allen",
        "Nicole King",
        "Ryan Wright",
        "Samantha Scott",
        "Tyler Torres",
        "Victoria Nguyen",
        "Benjamin Hill",
        "Megan Flores",
        "Jonathan Green",
    ]

    REFERRAL_REASONS = [
        "Specialty consultation",
        "Cardiac evaluation",
        "Orthopedic assessment",
        "Neurological evaluation",
        "Dermatological examination",
        "Gastroenterology consultation",
        "Endocrine evaluation",
        "Oncology consultation",
        "Psychiatric evaluation",
        "Pediatric care",
        "Ophthalmologic examination",
        "Pulmonary function testing",
        "Rheumatologic assessment",
        "Urological consultation",
        "ENT evaluation",
        "Pain management consultation",
        "Sports medicine evaluation",
        "Geriatric assessment",
        "Allergy testing",
        "Sleep study referral",
        "Surgical consultation",
        "Second opinion",
        "Pre-operative clearance",
        "Post-operative follow-up",
        "Diagnostic imaging",
        "Laboratory consultation",
        "Physical therapy referral",
        "Occupational therapy",
        "Speech therapy",
        "Nutritional counseling",
        "Mental health screening",
        "Substance abuse counseling",
    ]

    SERVICES_RENDERED = [
        "Office visit",
        "Consultation",
        "Diagnostic testing",
        "Procedure",
        "Follow-up visit",
        "Annual physical",
        "Preventive care",
        "Emergency visit",
        "Specialist consultation",
        "Diagnostic imaging",
        "Laboratory testing",
        "Therapy session",
        "Surgical procedure",
        "Minor procedure",
        "Injection",
        "Biopsy",
        "Endoscopy",
        "Colonoscopy",
        "Cardiac catheterization",
        "Stress test",
        "Sleep study",
        "Pulmonary function test",
        "Allergy testing",
        "Physical therapy",
        "Occupational therapy",
        "Speech therapy",
        "Wound care",
        "Chronic care management",
        "Medication management",
        "Immunization",
        "Health screening",
        "Wellness visit",
        "Telemedicine visit",
        "Group visit",
        "House call",
    ]

    def __init__(self, session: Session):
        self.session = session
        self.providers: List[Provider] = []

    def generate_npi(self) -> str:
        """Generate a realistic 10-digit NPI number."""
        return f"{random.randint(1000000000, 9999999999)}"

    def generate_phone(self) -> str:
        """Generate a realistic Bay Area phone number."""
        area_codes = ["415", "510", "650", "925", "408", "707", "669", "628", "341"]
        area_code = random.choice(area_codes)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"({area_code}) {exchange}-{number}"

    def generate_email(self, first_name: str, last_name: str, group_name: str) -> str:
        """Generate a realistic email address."""
        domain_part = (
            group_name.lower().replace(" ", "").replace("&", "").replace("-", "")[:20]
        )
        # Add some variety to email formats
        formats = [
            f"{first_name.lower()}.{last_name.lower()}@{domain_part}.com",
            f"{first_name[0].lower()}{last_name.lower()}@{domain_part}.com",
            f"{first_name.lower()}{last_name[0].lower()}@{domain_part}.com",
            f"dr.{last_name.lower()}@{domain_part}.com",
        ]
        return random.choice(formats)

    def create_providers(self, providers_per_specialty: int = 200) -> List[Provider]:
        """Create realistic provider records for Bay Area specialties with significantly more providers per specialty."""
        providers = []

        for specialty in self.SPECIALTIES:
            for _ in range(providers_per_specialty):
                first_name = random.choice(self.FIRST_NAMES)
                last_name = random.choice(self.LAST_NAMES)
                group_name = random.choice(self.PROVIDER_GROUPS)
                city, state, zip_code, address = random.choice(self.LOCATIONS)

                # Determine primary organization based on practice type and specialty
                if (
                    random.random() < 0.4
                ):  # 40% chance of being part of a major health system
                    primary_org = random.choice(
                        self.PARENT_ORGANIZATIONS[:8]
                    )  # Major health systems
                elif (
                    random.random() < 0.7
                ):  # 30% chance of being part of a medical group
                    if specialty in [
                        "Cardiology",
                        "Surgery",
                        "Oncology",
                        "Orthopedic Surgery",
                        "Neurology",
                        "Dermatology",
                    ]:
                        primary_org = random.choice(
                            self.PARENT_ORGANIZATIONS[12:18]
                        )  # Specialty groups
                    else:
                        primary_org = random.choice(
                            self.PARENT_ORGANIZATIONS[8:12]
                        )  # Large medical groups
                else:  # 30% chance of being independent
                    primary_org = "Independent Practice"

                provider = Provider(
                    npi=self.generate_npi(),
                    first_name=first_name,
                    last_name=last_name,
                    primary_specialty=specialty,
                    primary_practice_name=group_name,
                    primary_organization=primary_org,
                    primary_practice_address=address,
                    primary_practice_city=city,
                    primary_practice_state=state,
                    primary_practice_zip=zip_code,
                    phone=self.generate_phone(),
                    email=self.generate_email(first_name, last_name, group_name),
                )

                providers.append(provider)

        self.session.add_all(providers)
        self.session.commit()
        self.providers = providers

        print(
            f"✅ Created {len(providers)} providers across {len(self.SPECIALTIES)} specialties and {len(self.PROVIDER_GROUPS)} provider groups"
        )
        return providers

    def create_provider_visits(
        self, visit_records_per_provider: int = 24
    ) -> List[ProviderVisits]:
        """Create realistic provider visit records with much higher visit counts for comprehensive data."""
        visits = []

        for provider in self.providers:
            # Generate multiple visit records per provider (monthly records for 2 years)
            for _ in range(random.randint(12, visit_records_per_provider)):
                # Generate date range (last 24 months)
                end_date = datetime.now() - timedelta(days=random.randint(0, 730))
                start_date = end_date - timedelta(days=random.randint(30, 90))

                # More realistic visit counts per record
                base_visits = random.randint(10, 150)
                # Adjust by specialty (some specialties naturally have higher volumes)
                specialty_multipliers = {
                    "Primary Care": 2.0,
                    "Pediatrics": 1.8,
                    "Emergency Medicine": 3.0,
                    "Cardiology": 1.5,
                    "Dermatology": 1.3,
                    "Ophthalmology": 1.4,
                    "Orthopedic Surgery": 0.8,
                    "Neurology": 0.9,
                    "Oncology": 1.2,
                }
                multiplier = specialty_multipliers.get(provider.primary_specialty, 1.0)
                visit_count = int(base_visits * multiplier)

                # Generate more realistic charges based on specialty and visit count
                charge_ranges = {
                    "Primary Care": (100, 500),
                    "Emergency Medicine": (500, 3000),
                    "Orthopedic Surgery": (1000, 8000),
                    "Cardiology": (300, 2000),
                    "Oncology": (500, 5000),
                    "Neurology": (400, 1500),
                    "Dermatology": (150, 800),
                }
                min_charge, max_charge = charge_ranges.get(
                    provider.primary_specialty, (200, 1500)
                )

                # Calculate total charges more realistically - per visit charge * visit count
                avg_charge_per_visit = random.uniform(min_charge, max_charge)
                total_charges = Decimal(
                    str(avg_charge_per_visit * visit_count)
                ).quantize(Decimal("0.01"))

                visit = ProviderVisits(
                    provider_id=provider.id,
                    specialty=provider.primary_specialty,
                    practice_location=f"{provider.primary_practice_address}, {provider.primary_practice_city}, {provider.primary_practice_state}",
                    services_rendered=random.choice(self.SERVICES_RENDERED),
                    visit_count=visit_count,
                    total_charges=total_charges,
                    visit_start_date=start_date,
                    visit_end_date=end_date,
                )

                visits.append(visit)

        self.session.add_all(visits)
        self.session.commit()

        print(f"✅ Created {len(visits)} provider visit records")
        return visits

    def create_outreach_efforts(
        self, efforts_per_provider: int = 12
    ) -> List[OutreachEfforts]:
        """Create realistic outreach effort records with more comprehensive outreach tracking."""
        efforts = []

        for provider in self.providers:
            for _ in range(random.randint(6, efforts_per_provider)):
                # Generate outreach date (last 12 months)
                outreach_date = datetime.now() - timedelta(days=random.randint(0, 365))

                # Determine if follow-up is needed with more realistic distribution
                follow_up_required = random.choices(
                    ["Yes", "No"],
                    weights=[35, 65],  # 35% chance of follow-up needed
                )[0]

                follow_up_date = None
                if follow_up_required == "Yes":
                    follow_up_date = outreach_date + timedelta(
                        days=random.randint(7, 45)
                    )

                # Generate more varied and realistic comments
                outcome = random.choice(self.OUTREACH_OUTCOMES)
                specialty_comments = {
                    "Primary Care": f"Discussed primary care referral patterns and network adequacy. Outcome: {outcome}.",
                    "Cardiology": f"Reviewed cardiac care pathways and emergency protocols. Outcome: {outcome}.",
                    "Orthopedic Surgery": f"Explored surgical volume opportunities and post-op care coordination. Outcome: {outcome}.",
                    "Oncology": f"Discussed cancer care coordination and treatment protocols. Outcome: {outcome}.",
                }

                comment_templates = [
                    f"Discussed referral network optimization in {provider.primary_specialty}. Outcome: {outcome}.",
                    f"Explored value-based care opportunities with {provider.primary_practice_name}. Outcome: {outcome}.",
                    f"Reviewed quality metrics and patient satisfaction scores. Outcome: {outcome}.",
                    f"Provider engagement session focusing on Bay Area network expansion. Outcome: {outcome}.",
                    f"Collaborative care discussion for {provider.primary_practice_city} market. Outcome: {outcome}.",
                    specialty_comments.get(
                        provider.primary_specialty,
                        f"Standard outreach for {provider.primary_specialty}. Outcome: {outcome}.",
                    ),
                ]

                effort = OutreachEfforts(
                    provider_id=provider.id,
                    outreach_date=outreach_date,
                    outreach_type=random.choice(self.OUTREACH_TYPES),
                    outreach_specialist=random.choice(self.OUTREACH_SPECIALISTS),
                    comments=random.choice(comment_templates),
                    follow_up_required=follow_up_required,
                    follow_up_date=follow_up_date,
                )

                efforts.append(effort)

        self.session.add_all(efforts)
        self.session.commit()

        print(f"✅ Created {len(efforts)} outreach effort records")
        return efforts

    def create_provider_referrals(
        self, referrals_count: int = 5000
    ) -> List[ProviderReferrals]:
        """Create realistic provider referral records with emphasis on cross-specialty referrals and higher volume."""
        referrals = []

        # Create referral patterns that make clinical sense
        referral_patterns = {
            "Primary Care": [
                "Cardiology",
                "Dermatology",
                "Endocrinology",
                "Gastroenterology",
                "Orthopedic Surgery",
                "Ophthalmology",
            ],
            "Emergency Medicine": [
                "Cardiology",
                "Orthopedic Surgery",
                "Neurology",
                "General Surgery",
                "Psychiatry",
            ],
            "Cardiology": ["General Surgery", "Endocrinology"],
            "Neurology": ["General Surgery", "Psychiatry", "Pain Management"],
            "Orthopedic Surgery": ["Pain Management", "Rheumatology"],
            "Gastroenterology": ["General Surgery", "Oncology", "Pathology"],
            "Oncology": ["Pain Management", "Psychiatry", "Pathology"],
        }

        for _ in range(referrals_count):
            # Select referring provider
            referring_provider = random.choice(self.providers)

            # Try to use realistic referral patterns first
            potential_specialties = referral_patterns.get(
                referring_provider.primary_specialty, []
            )
            if (
                potential_specialties and random.random() < 0.7
            ):  # 70% chance of following pattern
                target_specialty = random.choice(potential_specialties)
                # Find providers in target specialty
                target_providers = [
                    p for p in self.providers if p.primary_specialty == target_specialty
                ]
                if target_providers:
                    referred_to_provider = random.choice(target_providers)
                else:
                    # Fallback to any different provider
                    referred_to_provider = random.choice(
                        [p for p in self.providers if p.id != referring_provider.id]
                    )
            else:
                # Random cross-specialty referral
                potential_providers = [
                    p
                    for p in self.providers
                    if p.primary_specialty != referring_provider.primary_specialty
                ]
                if potential_providers:
                    referred_to_provider = random.choice(potential_providers)
                else:
                    continue  # Skip if no valid providers found

            # Generate date range (last 18 months)
            end_date = datetime.now() - timedelta(days=random.randint(0, 545))
            start_date = end_date - timedelta(days=random.randint(30, 120))

            # Generate specialty-specific referral reason with more variety
            referral_reasons = [
                f"{referred_to_provider.primary_specialty} consultation",
                f"Specialist evaluation - {referred_to_provider.primary_specialty}",
                f"Complex case referral to {referred_to_provider.primary_specialty}",
                f"Second opinion - {referred_to_provider.primary_specialty}",
                f"Procedural referral - {referred_to_provider.primary_specialty}",
                random.choice(self.REFERRAL_REASONS),
            ]
            reason = random.choice(referral_reasons)

            # Generate referral count based on specialty relationship
            base_count = random.randint(1, 25)
            # High-volume specialties get more referrals
            if referring_provider.primary_specialty == "Primary Care":
                base_count = random.randint(10, 60)
            elif referring_provider.primary_specialty == "Emergency Medicine":
                base_count = random.randint(5, 40)

            referral = ProviderReferrals(
                referring_provider_id=referring_provider.id,
                referred_to_provider_id=referred_to_provider.id,
                referral_reason=reason,
                referral_count=base_count,
                referral_start_date=start_date,
                referral_end_date=end_date,
            )

            referrals.append(referral)

        self.session.add_all(referrals)
        self.session.commit()

        print(f"✅ Created {len(referrals)} provider referral records")
        return referrals

    def clear_existing_data(self):
        """Clear all existing CRM data (use with caution!)."""
        print("🗑️  Clearing existing CRM data...")

        # Delete in reverse order of dependencies
        self.session.query(ProviderReferrals).delete()
        self.session.query(OutreachEfforts).delete()
        self.session.query(ProviderVisits).delete()
        self.session.query(Provider).delete()

        self.session.commit()
        print("✅ Existing data cleared")

    def seed_all_data(
        self,
        providers_per_specialty: int = 200,
        visit_records_per_provider: int = 24,
        efforts_per_provider: int = 12,
        referrals_count: int = 5000,
        clear_existing: bool = False,
    ):
        """Seed all CRM data with comprehensive, large-scale realistic Bay Area examples."""

        if clear_existing:
            self.clear_existing_data()

        print(
            "🌱 Starting LARGE-SCALE CRM database seeding for San Francisco Bay Area..."
        )
        print(
            f"📈 Target Scale: {len(self.SPECIALTIES) * providers_per_specialty:,} providers across {len(self.SPECIALTIES)} specialties"
        )

        # Create data in dependency order
        print("👥 Creating providers...")
        self.create_providers(providers_per_specialty)

        print("🏥 Creating provider visits...")
        self.create_provider_visits(visit_records_per_provider)

        print("📞 Creating outreach efforts...")
        self.create_outreach_efforts(efforts_per_provider)

        print("🔄 Creating provider referrals...")
        self.create_provider_referrals(referrals_count)

        print("\n🎉 LARGE-SCALE Database seeding completed successfully!")
        print(f"📊 Final Dataset Summary:")
        print(
            f"   - {len(self.providers):,} Providers ({providers_per_specialty} per specialty)"
        )
        print(
            f"   - ~{len(self.providers) * visit_records_per_provider:,} Provider Visit Records (estimated)"
        )
        print(
            f"   - ~{len(self.providers) * efforts_per_provider:,} Outreach Efforts (estimated)"
        )
        print(f"   - {referrals_count:,} Provider Referrals")
        print(f"   - Coverage: {len(self.SPECIALTIES)} medical specialties")
        print(
            f"   - Provider Groups: {len(self.PROVIDER_GROUPS)} different healthcare organizations"
        )
        print(f"   - Geographic Coverage: {len(self.LOCATIONS)} Bay Area locations")
        print(
            f"   - Total Records: ~{len(self.providers) * (visit_records_per_provider + efforts_per_provider) + referrals_count:,}"
        )
        print("\n🎯 Dataset Features:")
        print("   ✓ Realistic referral patterns between specialties")
        print("   ✓ Volume-adjusted visit counts by specialty type")
        print("   ✓ Comprehensive Bay Area geographic coverage")
        print("   ✓ Varied outreach types and outcomes")
        print("   ✓ Specialty-specific charge ranges")
        print("   ✓ Multi-year historical data (24 months)")


def main():
    """Main function to run the enhanced large-scale seeding script."""
    print("🚀 ENHANCED CRM Database Seeding Script - Large-Scale Bay Area Dataset")
    print("=" * 80)
    print("📋 This will create a comprehensive synthetic dataset including:")
    print("   • 6,000+ Providers (200 per specialty across 30 specialties)")
    print("   • 144,000+ Visit records (24 per provider)")
    print("   • 72,000+ Outreach efforts (12 per provider)")
    print("   • 5,000+ Referral relationships")
    print("   • Total: ~227,000+ database records")
    print("=" * 80)

    # Get database session
    session = next(db_session())

    try:
        seeder = EnhancedCRMDataSeeder(session)

        # Seed with comprehensive Bay Area focused data
        seeder.seed_all_data(
            providers_per_specialty=200,  # 200 providers per specialty = 6,000 total providers
            visit_records_per_provider=24,  # 24 visit records per provider = ~144,000 visit records
            efforts_per_provider=12,  # 12 outreach efforts per provider = ~72,000 outreach records
            referrals_count=5000,  # 5,000 referral relationships
            clear_existing=True,  # Set to False to keep existing data
        )

        print("\n💡 Pro Tips for Development:")
        print("   • Use database indexing on provider_id, specialty, and date fields")
        print("   • Consider partitioning visit data by date for performance")
        print("   • Implement pagination for large result sets")
        print("   • Use specialty-based filtering for focused queries")
        print("   • Geographic clustering by city/zip for location-based features")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


# Additional utility functions for development and testing
class DatasetAnalyzer:
    """Utility class to analyze the generated dataset."""

    def __init__(self, session: Session):
        self.session = session

    def analyze_dataset(self):
        """Generate analysis report of the seeded data."""
        print("\n📊 DATASET ANALYSIS REPORT")
        print("=" * 50)

        # Provider analysis
        provider_count = self.session.query(Provider).count()

        # Get specialty distribution
        specialty_counts = (
            self.session.query(
                Provider.primary_specialty, func.count(Provider.id).label("count")
            )
            .group_by(Provider.primary_specialty)
            .all()
        )

        # Get unique counts
        unique_specialties = len(specialty_counts)
        unique_groups = (
            self.session.query(Provider.primary_practice_name).distinct().count()
        )
        unique_cities = (
            self.session.query(Provider.primary_practice_city).distinct().count()
        )

        print(f"👥 Total Providers: {provider_count:,}")
        print(f"🏥 Specialties: {unique_specialties}")
        print(f"🏢 Provider Groups: {unique_groups}")
        print(f"📍 Geographic Locations: {unique_cities}")

        # Visit analysis
        visit_count = self.session.query(ProviderVisits).count()
        total_charges = (
            self.session.query(func.sum(ProviderVisits.total_charges)).scalar() or 0
        )
        total_visits = (
            self.session.query(func.sum(ProviderVisits.visit_count)).scalar() or 0
        )

        print(f"\n🏥 Visit Records: {visit_count:,}")
        print(f"👥 Total Patient Visits: {total_visits:,}")
        print(f"💰 Total Charges: ${total_charges:,.2f}")

        # Outreach analysis
        outreach_count = self.session.query(OutreachEfforts).count()
        follow_up_needed = (
            self.session.query(OutreachEfforts)
            .filter(OutreachEfforts.follow_up_required == "Yes")
            .count()
        )

        print(f"\n📞 Outreach Records: {outreach_count:,}")
        if outreach_count > 0:
            print(
                f"⏰ Follow-ups Needed: {follow_up_needed:,} ({follow_up_needed / outreach_count * 100:.1f}%)"
            )
        else:
            print("⏰ Follow-ups Needed: 0 (0.0%)")

        # Referral analysis
        referral_count = self.session.query(ProviderReferrals).count()
        total_referrals = (
            self.session.query(func.sum(ProviderReferrals.referral_count)).scalar() or 0
        )

        print(f"\n🔄 Referral Records: {referral_count:,}")
        print(f"👥 Total Referrals: {total_referrals:,}")

        print(
            f"\n📈 GRAND TOTAL RECORDS: {provider_count + visit_count + outreach_count + referral_count:,}"
        )

        # Top specialties by provider count
        if specialty_counts:
            print(f"\n🏆 Top 5 Specialties by Provider Count:")
            top_specialties = sorted(
                specialty_counts, key=lambda x: x.count, reverse=True
            )[:5]
            for specialty, count in top_specialties:
                print(f"   • {specialty}: {count} providers")


if __name__ == "__main__":
    main()

    # Optionally run analysis after seeding
    print("\n" + "=" * 80)
    analyze = input("Would you like to run dataset analysis? (y/n): ").lower().strip()
    if analyze == "y":
        session = next(db_session())
        try:
            analyzer = DatasetAnalyzer(session)
            analyzer.analyze_dataset()
        finally:
            session.close()
