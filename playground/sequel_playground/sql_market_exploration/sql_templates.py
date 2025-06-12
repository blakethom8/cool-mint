"""
SQL Templates for Provider Analysis

This module contains SQL templates for analyzing provider data, specialties,
and organizational relationships.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SQLTemplate:
    id: str
    name: str
    description: str
    sql: str
    required_params: List[str]
    optional_params: List[str]
    output_columns: List[str]
    intent_keywords: List[str]


SQL_TEMPLATES = {
    "provider_specialty_distribution": SQLTemplate(
        id="provider_specialty_distribution",
        name="Provider Specialty Distribution",
        description="Shows the distribution of providers across different specialties",
        sql="""
        SELECT 
            primary_specialty,
            COUNT(*) as provider_count
        FROM providers
        GROUP BY primary_specialty
        ORDER BY provider_count DESC
        LIMIT :limit;
        """,
        required_params=[],
        optional_params=["limit"],
        output_columns=["primary_specialty", "provider_count"],
        intent_keywords=["specialty", "distribution", "count"],
    ),
    "top_providers_by_specialty": SQLTemplate(
        id="top_providers_by_specialty",
        name="Top Providers by Specialty",
        description="Shows the top providers within each specialty based on visit volume",
        sql="""
        WITH provider_visit_totals AS (
            SELECT 
                p.id,
                p.first_name,
                p.last_name,
                p.primary_specialty,
                p.primary_organization,
                p.primary_practice_name,
                SUM(pv.visit_count) as total_visits,
                RANK() OVER (PARTITION BY p.primary_specialty 
                           ORDER BY SUM(pv.visit_count) DESC) as specialty_rank
            FROM providers p
            LEFT JOIN provider_visits pv ON p.id = pv.provider_id
            WHERE (:specialty IS NULL OR p.primary_specialty LIKE :specialty)
            GROUP BY p.id, p.first_name, p.last_name, p.primary_specialty, 
                     p.primary_organization, p.primary_practice_name
        )
        SELECT 
            primary_specialty,
            first_name,
            last_name,
            primary_organization,
            primary_practice_name,
            total_visits
        FROM provider_visit_totals
        WHERE specialty_rank <= :top_n
        ORDER BY primary_specialty, total_visits DESC;
        """,
        required_params=["top_n"],
        optional_params=["specialty"],
        output_columns=[
            "primary_specialty",
            "first_name",
            "last_name",
            "primary_organization",
            "primary_practice_name",
            "total_visits",
        ],
        intent_keywords=["top providers", "visits", "volume", "specialty leaders"],
    ),
    "top_organizations_by_specialty": SQLTemplate(
        id="top_organizations_by_specialty",
        name="Top Organizations by Specialty",
        description="Shows the leading organizations within each specialty based on provider count",
        sql="""
        WITH org_specialty_counts AS (
            SELECT 
                primary_specialty,
                primary_organization,
                COUNT(*) as provider_count,
                RANK() OVER (PARTITION BY primary_specialty 
                           ORDER BY COUNT(*) DESC) as org_rank
            FROM providers
            WHERE (:specialty IS NULL OR primary_specialty LIKE :specialty)
            GROUP BY primary_specialty, primary_organization
        )
        SELECT 
            primary_specialty,
            primary_organization,
            provider_count
        FROM org_specialty_counts
        WHERE org_rank <= :top_n
        ORDER BY primary_specialty, provider_count DESC;
        """,
        required_params=["top_n"],
        optional_params=["specialty"],
        output_columns=["primary_specialty", "primary_organization", "provider_count"],
        intent_keywords=["organizations", "market share", "specialty coverage"],
    ),
    "top_practice_locations": SQLTemplate(
        id="top_practice_locations",
        name="Top Practice Locations by Visit Volume",
        description="Shows the top practice locations based on visit volume with detailed geographic information",
        sql="""
        WITH location_totals AS (
            SELECT 
                p.primary_practice_address,
                p.primary_practice_city,
                p.primary_practice_state,
                p.primary_practice_zip,
                COUNT(DISTINCT p.id) as provider_count,
                SUM(pv.visit_count) as total_visits,
                RANK() OVER (
                    PARTITION BY p.primary_practice_state 
                    ORDER BY SUM(pv.visit_count) DESC
                ) as location_rank
            FROM providers p
            LEFT JOIN provider_visits pv ON p.id = pv.provider_id
            WHERE (:specialty IS NULL OR p.primary_specialty LIKE :specialty)
            GROUP BY 
                p.primary_practice_address,
                p.primary_practice_city,
                p.primary_practice_state,
                p.primary_practice_zip
        )
        SELECT 
            primary_practice_address,
            primary_practice_city,
            primary_practice_state,
            primary_practice_zip,
            provider_count,
            total_visits
        FROM location_totals
        WHERE location_rank <= :top_n
        ORDER BY primary_practice_state, total_visits DESC;
        """,
        required_params=["top_n"],
        optional_params=["specialty"],
        output_columns=[
            "primary_practice_address",
            "primary_practice_city",
            "primary_practice_state",
            "primary_practice_zip",
            "provider_count",
            "total_visits",
        ],
        intent_keywords=["practice locations", "geography", "visit volume"],
    ),
    "practice_location_groups": SQLTemplate(
        id="practice_location_groups",
        name="Provider Groups by Practice Location",
        description="Shows aggregated provider group statistics by practice location",
        sql="""
        WITH location_groups AS (
            SELECT 
                p.primary_practice_address as practice_address,
                p.primary_practice_city as practice_city,
                p.primary_practice_state as practice_state,
                p.primary_organization as organization_name,
                COUNT(DISTINCT p.id) as provider_count,
                STRING_AGG(DISTINCT p.primary_specialty, ', ') as specialties,
                SUM(pv.visit_count) as total_visits,
                RANK() OVER (
                    PARTITION BY p.primary_practice_address, p.primary_practice_city 
                    ORDER BY COUNT(DISTINCT p.id) DESC
                ) as group_rank
            FROM providers p
            LEFT JOIN provider_visits pv ON p.id = pv.provider_id
            WHERE (:specialty IS NULL OR p.primary_specialty LIKE :specialty)
            GROUP BY 
                p.primary_practice_address,
                p.primary_practice_city,
                p.primary_practice_state,
                p.primary_organization
        )
        SELECT 
            practice_address,
            practice_city,
            practice_state,
            organization_name,
            provider_count,
            specialties,
            total_visits
        FROM location_groups
        WHERE group_rank <= :top_n
        ORDER BY 
            practice_state,
            practice_city,
            provider_count DESC;
        """,
        required_params=["top_n"],
        optional_params=["specialty"],
        output_columns=[
            "practice_address",
            "practice_city",
            "practice_state",
            "organization_name",
            "provider_count",
            "specialties",
            "total_visits",
        ],
        intent_keywords=["practice groups", "locations", "provider distribution"],
    ),
    "top_providers_by_location": SQLTemplate(
        id="top_providers_by_location",
        name="Top Providers by Practice Location",
        description="Shows the top performing providers at each practice location",
        sql="""
        WITH provider_location_stats AS (
            SELECT 
                p.id,
                p.first_name,
                p.last_name,
                p.primary_specialty,
                p.primary_organization,
                p.primary_practice_name,
                p.primary_practice_address,
                p.primary_practice_city,
                p.primary_practice_state,
                SUM(pv.visit_count) as total_visits,
                RANK() OVER (
                    PARTITION BY p.primary_practice_address, p.primary_practice_city 
                    ORDER BY SUM(pv.visit_count) DESC
                ) as location_rank
            FROM providers p
            LEFT JOIN provider_visits pv ON p.id = pv.provider_id
            WHERE 
                (:specialty IS NULL OR p.primary_specialty LIKE :specialty)
                AND (:city IS NULL OR p.primary_practice_city LIKE :city)
                AND (:state IS NULL OR p.primary_practice_state = :state)
            GROUP BY 
                p.id,
                p.first_name,
                p.last_name,
                p.primary_specialty,
                p.primary_organization,
                p.primary_practice_name,
                p.primary_practice_address,
                p.primary_practice_city,
                p.primary_practice_state
        )
        SELECT 
            primary_practice_address,
            primary_practice_city,
            primary_practice_state,
            first_name,
            last_name,
            primary_specialty,
            primary_organization,
            primary_practice_name,
            total_visits
        FROM provider_location_stats
        WHERE location_rank <= :top_n
        ORDER BY 
            primary_practice_state,
            primary_practice_city,
            primary_practice_address,
            total_visits DESC;
        """,
        required_params=["top_n"],
        optional_params=["specialty", "city", "state"],
        output_columns=[
            "primary_practice_address",
            "primary_practice_city",
            "primary_practice_state",
            "first_name",
            "last_name",
            "primary_specialty",
            "primary_organization",
            "primary_practice_name",
            "total_visits",
        ],
        intent_keywords=["providers", "locations", "performance", "practice sites"],
    ),
}
