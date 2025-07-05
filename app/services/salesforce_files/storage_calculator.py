#!/usr/bin/env python3
"""
Storage Calculator for Salesforce Contact Data

This script estimates the storage requirements for syncing large volumes
of Salesforce contact data to the local PostgreSQL database.
"""


def calculate_contact_storage(num_contacts: int = 600000) -> dict:
    """Calculate storage requirements for contact data."""

    # Per-contact storage breakdown (in bytes)
    storage_breakdown = {
        "fixed_fields": {
            "uuid_id": 16,  # UUID primary key
            "salesforce_id": 18,  # Salesforce ID (18 chars)
            "booleans": 6,  # 6 boolean fields (1 byte each)
            "dates": 40,  # 5 date/datetime fields (8 bytes each)
            "floats": 32,  # 4 float fields (8 bytes each)
        },
        "variable_string_fields": {
            "short_strings": 800,  # Names, phones, etc. (avg 20 chars × 40 fields)
            "medium_strings": 600,  # Titles, specialties, etc. (avg 50 chars × 12 fields)
            "long_strings": 1200,  # Addresses, descriptions (avg 100 chars × 12 fields)
            "very_long_strings": 400,  # Full names, compounds (avg 200 chars × 2 fields)
        },
        "text_fields": {
            "descriptions": 500,  # Provider notes, participation details
            "addresses": 300,  # Mailing street, compound addresses
        },
        "json_fields": {
            "additional_data": 1500,  # Raw Salesforce data (compressed in JSON)
            "analysis_results": 200,  # Future LLM analysis data
        },
        "postgresql_overhead": {
            "row_header": 28,  # PostgreSQL row header
            "tuple_overhead": 24,  # Tuple overhead
            "alignment_padding": 8,  # Memory alignment
        },
    }

    # Calculate totals
    fixed_total = sum(storage_breakdown["fixed_fields"].values())
    variable_total = sum(storage_breakdown["variable_string_fields"].values())
    text_total = sum(storage_breakdown["text_fields"].values())
    json_total = sum(storage_breakdown["json_fields"].values())
    overhead_total = sum(storage_breakdown["postgresql_overhead"].values())

    bytes_per_contact = (
        fixed_total + variable_total + text_total + json_total + overhead_total
    )

    # Index storage estimates
    index_overhead = bytes_per_contact * 0.25  # ~25% overhead for indexes

    total_per_contact = bytes_per_contact + index_overhead

    # Calculate for all contacts
    total_bytes = total_per_contact * num_contacts
    total_mb = total_bytes / (1024 * 1024)
    total_gb = total_mb / 1024

    # Additional database overhead
    database_overhead = {
        "wal_logs": total_gb * 0.1,  # WAL logs (~10%)
        "temp_space": total_gb * 0.2,  # Temporary processing space (~20%)
        "vacuum_space": total_gb * 0.15,  # VACUUM/maintenance space (~15%)
        "growth_buffer": total_gb * 0.3,  # Growth buffer (~30%)
    }

    total_overhead_gb = sum(database_overhead.values())
    total_storage_gb = total_gb + total_overhead_gb

    return {
        "contacts": num_contacts,
        "bytes_per_contact": round(total_per_contact),
        "kb_per_contact": round(total_per_contact / 1024, 2),
        "contact_data_gb": round(total_gb, 2),
        "index_overhead_gb": round(index_overhead * num_contacts / (1024**3), 2),
        "database_overhead": {k: round(v, 2) for k, v in database_overhead.items()},
        "total_storage_gb": round(total_storage_gb, 2),
        "breakdown": storage_breakdown,
    }


def estimate_sync_time(num_contacts: int = 600000) -> dict:
    """Estimate sync time for different scenarios."""

    # Performance estimates based on typical Bulk API performance
    bulk_api_rate = 3000  # contacts per minute (conservative)
    db_processing_rate = 5000  # contacts per minute for database operations

    # Bottleneck is usually the Bulk API
    effective_rate = min(bulk_api_rate, db_processing_rate)

    sync_time_minutes = num_contacts / effective_rate
    sync_time_hours = sync_time_minutes / 60

    return {
        "contacts": num_contacts,
        "estimated_rate_per_minute": effective_rate,
        "estimated_minutes": round(sync_time_minutes, 1),
        "estimated_hours": round(sync_time_hours, 2),
        "estimated_human_readable": f"{int(sync_time_hours)}h {int((sync_time_hours % 1) * 60)}m",
    }


def analyze_storage_growth(monthly_new_contacts: int = 1000) -> dict:
    """Analyze storage growth over time."""

    base_storage = calculate_contact_storage()

    # Calculate monthly growth
    monthly_growth_gb = (base_storage["kb_per_contact"] * monthly_new_contacts) / (
        1024 * 1024
    )
    yearly_growth_gb = monthly_growth_gb * 12

    # 5-year projection
    five_year_contacts = base_storage["contacts"] + (monthly_new_contacts * 12 * 5)
    five_year_storage = calculate_contact_storage(five_year_contacts)

    return {
        "current_storage_gb": base_storage["total_storage_gb"],
        "monthly_growth_gb": round(monthly_growth_gb, 3),
        "yearly_growth_gb": round(yearly_growth_gb, 2),
        "five_year_projection": {
            "contacts": five_year_contacts,
            "storage_gb": five_year_storage["total_storage_gb"],
            "growth_gb": round(
                five_year_storage["total_storage_gb"]
                - base_storage["total_storage_gb"],
                2,
            ),
        },
    }


def main():
    """Generate comprehensive storage analysis."""

    print("📊 SALESFORCE CONTACT DATA STORAGE ANALYSIS")
    print("=" * 60)

    # Storage calculation
    storage = calculate_contact_storage(600000)

    print(f"\n🗄️  STORAGE REQUIREMENTS (600,000 contacts)")
    print("-" * 40)
    print(f"Per contact storage: {storage['kb_per_contact']} KB")
    print(f"Contact data only: {storage['contact_data_gb']} GB")
    print(f"Index overhead: {storage['index_overhead_gb']} GB")
    print(f"Database overhead:")
    for item, size in storage["database_overhead"].items():
        print(f"  - {item.replace('_', ' ').title()}: {size} GB")
    print(f"\n💾 TOTAL STORAGE NEEDED: {storage['total_storage_gb']} GB")

    # Sync time estimation
    sync_time = estimate_sync_time(600000)
    print(f"\n⏱️  SYNC TIME ESTIMATES")
    print("-" * 40)
    print(
        f"Processing rate: {sync_time['estimated_rate_per_minute']:,} contacts/minute"
    )
    print(f"Estimated time: {sync_time['estimated_human_readable']}")
    print(f"Exact time: {sync_time['estimated_minutes']} minutes")

    # Growth analysis
    growth = analyze_storage_growth(1000)
    print(f"\n📈 STORAGE GROWTH PROJECTION")
    print("-" * 40)
    print(f"Current storage: {growth['current_storage_gb']} GB")
    print(f"Monthly growth: {growth['monthly_growth_gb']} GB")
    print(f"Yearly growth: {growth['yearly_growth_gb']} GB")
    print(f"5-year projection:")
    print(f"  - Contacts: {growth['five_year_projection']['contacts']:,}")
    print(f"  - Storage: {growth['five_year_projection']['storage_gb']} GB")
    print(f"  - Total growth: {growth['five_year_projection']['growth_gb']} GB")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 40)
    if storage["total_storage_gb"] < 10:
        print("✅ Storage requirement is manageable for most systems")
    elif storage["total_storage_gb"] < 50:
        print("⚠️  Consider ensuring adequate disk space for growth")
    else:
        print("🚨 Large storage requirement - plan for enterprise storage")

    print(f"\n🔧 OPTIMIZATION TIPS")
    print("-" * 40)
    print("1. Use incremental syncs to minimize processing")
    print("2. Consider archiving old analysis_results data")
    print("3. Monitor and vacuum database regularly")
    print("4. Use compression for JSON fields if needed")
    print("5. Consider partitioning by date for very large datasets")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
