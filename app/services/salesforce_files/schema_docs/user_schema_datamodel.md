## Standard Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| Id | id | Yes | Length: 18 |
| Username | string | Yes | Length: 80 |
| LastName | string | Yes | Length: 80 |
| FirstName | string | No | Length: 40 |
| MiddleName | string | No | Length: 40 |
| Suffix | string | No | Length: 40 |
| Name | string | Yes | Length: 121 |=
| Address | address | No | - |
| Email | email | Yes | Length: 128 |
| IsProfilePhotoActive | boolean | Yes | - |

## Custom Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| External_ID__c | string | No | Length: 20 |

## Relationship Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| UserRoleId | reference | No | References: UserRole<br>Relationship: UserRole<br>Length: 18 |
| ProfileId | reference | Yes | References: Profile<br>Relationship: Profile<br>Length: 18 |
| ManagerId | reference | No | References: User<br>Relationship: Manager<br>Length: 18 |
| CreatedById | reference | Yes | References: User<br>Relationship: CreatedBy<br>Length: 18 |
| LastModifiedById | reference | Yes | References: User<br>Relationship: LastModifiedBy<br>Length: 18 |
| ContactId | reference | No | References: Contact<br>Relationship: Contact<br>Length: 18 |
| AccountId | reference | No | References: Account<br>Relationship: Account<br>Length: 18 |

## System Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| CreatedDate | datetime | Yes | - |
| LastModifiedDate | datetime | Yes | - |
| SystemModstamp | datetime | Yes | - |

