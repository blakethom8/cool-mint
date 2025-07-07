import sys
import os
import json
from datetime import datetime
from typing import Dict, List

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.salesforce_files.salesforce_service import ReadOnlySalesforceService


class SchemaExplorer:
    def __init__(self):
        self.sf_service = ReadOnlySalesforceService()

    def explore_object(self, object_name: str) -> Dict:
        """Explore a Salesforce object's schema and return field information."""
        print(f"\nExploring {object_name} schema...")

        metadata = self.sf_service.describe_object(object_name)
        fields = metadata["fields"]

        # Organize fields by category
        field_info = {
            "standard_fields": [],
            "custom_fields": [],
            "relationship_fields": [],
            "system_fields": [],  # CreatedBy, LastModifiedBy, etc.
        }

        for field in fields:
            field_data = {
                "name": field["name"],
                "label": field["label"],
                "type": field["type"],
                "length": field.get("length"),
                "required": field["nillable"] == False,
                "updateable": field["updateable"],
                "reference_to": field.get("referenceTo", []),
                "relationship_name": field.get("relationshipName"),
            }

            # Categorize the field
            if field["custom"]:
                field_info["custom_fields"].append(field_data)
            elif field["relationshipName"]:
                field_info["relationship_fields"].append(field_data)
            elif field["name"] in [
                "CreatedById",
                "LastModifiedById",
                "SystemModstamp",
                "CreatedDate",
                "LastModifiedDate",
            ]:
                field_info["system_fields"].append(field_data)
            else:
                field_info["standard_fields"].append(field_data)

        return field_info

    def print_field_summary(self, object_name: str, field_info: Dict):
        """Print a human-readable summary of the fields."""
        print(f"\n{object_name} Field Summary:")
        print("-" * 50)

        for category in field_info:
            fields = field_info[category]
            print(f"\n{category.replace('_', ' ').title()} ({len(fields)}):")
            for field in fields:
                required = "Required" if field["required"] else "Optional"
                if field["reference_to"]:
                    print(f"  • {field['name']} ({field['type']}) - {required}")
                    print(f"    References: {', '.join(field['reference_to'])}")
                    if field["relationship_name"]:
                        print(f"    Relationship: {field['relationship_name']}")
                else:
                    print(f"  • {field['name']} ({field['type']}) - {required}")

    def save_schema_documentation(self, object_name: str, field_info: Dict):
        """Save the schema information to a markdown file."""
        docs_dir = os.path.join(current_dir, "schema_docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        filename = os.path.join(docs_dir, f"{object_name.lower()}_schema.md")

        with open(filename, "w") as f:
            f.write(f"# {object_name} Schema Documentation\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for category in field_info:
                fields = field_info[category]
                f.write(f"## {category.replace('_', ' ').title()}\n\n")

                if fields:
                    f.write("| Field Name | Type | Required | Details |\n")
                    f.write("|------------|------|----------|----------|\n")

                    for field in fields:
                        required = "Yes" if field["required"] else "No"
                        details = []
                        if field["reference_to"]:
                            details.append(
                                f"References: {', '.join(field['reference_to'])}"
                            )
                        if field["relationship_name"]:
                            details.append(
                                f"Relationship: {field['relationship_name']}"
                            )
                        if field["length"]:
                            details.append(f"Length: {field['length']}")

                        detail_str = "<br>".join(details) if details else "-"
                        f.write(
                            f"| {field['name']} | {field['type']} | {required} | {detail_str} |\n"
                        )

                    f.write("\n")
                else:
                    f.write("No fields in this category.\n\n")


def main():
    explorer = SchemaExplorer()

    # List of objects to explore
    objects_to_explore = ["TaskWhoRelation"]  # ["Contact", "Task", "User"]

    for object_name in objects_to_explore:
        try:
            # Get field information
            field_info = explorer.explore_object(object_name)

            # Print summary to console
            explorer.print_field_summary(object_name, field_info)

            # Save detailed documentation
            explorer.save_schema_documentation(object_name, field_info)

            print(f"\n✓ {object_name} schema documentation saved!")

        except Exception as e:
            print(f"\n❌ Error exploring {object_name}: {str(e)}")


if __name__ == "__main__":
    main()
