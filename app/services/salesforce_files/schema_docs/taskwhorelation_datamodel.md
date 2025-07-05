## Standard Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| Id | id | Yes | Length: 18 |
| IsDeleted | boolean | Yes | - |
| Type | string | No | Length: 50 |

## Custom Fields

No fields in this category.

## Relationship Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| RelationId | reference | No | References: Contact, Lead<br>Relationship: Relation<br>Length: 18 |
| TaskId | reference | No | References: Task<br>Relationship: Task<br>Length: 18 |
| AccountId | reference | No | References: Account<br>Relationship: Account<br>Length: 18 |
| CreatedById | reference | Yes | References: User<br>Relationship: CreatedBy<br>Length: 18 |
| LastModifiedById | reference | Yes | References: User<br>Relationship: LastModifiedBy<br>Length: 18 |

## System Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| CreatedDate | datetime | Yes | - |
| LastModifiedDate | datetime | Yes | - |
| SystemModstamp | datetime | Yes | - |

