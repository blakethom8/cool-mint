## Standard Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| Id | id | Yes | Length: 18 |
| WhoCount | int | No | - |
| WhatCount | int | No | - |
| Subject | combobox | No | Length: 255 |
| ActivityDate | date | No | - |
| Status | picklist | Yes | Length: 255 |
| Priority | picklist | Yes | Length: 20 |
| IsHighPriority | boolean | Yes | - |
| Description | textarea | No | Length: 32000 |
| IsDeleted | boolean | Yes | - |
| IsClosed | boolean | Yes | - |
| IsArchived | boolean | Yes | - |
| TaskSubtype | picklist | No | Length: 40 |
| CompletedDateTime | datetime | No | - |

## Custom Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| MNO_Subtype_c__c | picklist | No | Length: 255 |
| MNO_Primary_Attendees_ID__c | reference | No | References: Primary_Contact__c<br>Relationship: MNO_Primary_Attendees_ID__r<br>Length: 18 |
| MNO_Type__c | picklist | No | Length: 255 |
| MN_Tags__c | multipicklist | No | Length: 4099 |
| MNO_Setting__c | picklist | No | Length: 255 |
| Attendees_Concatenation__c | textarea | No | Length: 255 |
| Comments_Short__c | textarea | No | Length: 255 |

## Relationship Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| WhoId | reference | No | References: Contact, Lead<br>Relationship: Who<br>Length: 18 |
| WhatId | reference | No | References: Account, Activity_Goal__c, Asset, AssetRelationship, Attendees__c, Campaign, Case, Complaint__c, ContactRequest, Contract, Department__c, DiscussionTopic_Bridge__c, Discussion_Topic_Category__c, Discussion_Topic__c, Geo_Region__c, Hours__c, Image, Initiative_Assignment__c, Initiative_Bridge__c, Initiative__c, Liaison_Assignment__c, ListEmail, Location, MN_Target_List__c, Milestones__c, Network__c, OperatingHoursHoliday, Opportunity, Order, Outreach_Effort__c, Phase__c, Practice_Group_Address__c, Practice_Locations__c, Primary_Contact__c, ProcessException, Product2, Project__c, Provider_Practice_Location__c, Quote, ServiceLine_Bridge__c, Service_Line__c, Solution, Sub_ServiceLine__c, Todo__c, Visit_Goal__c, Visit__c, WorkOrder, WorkOrderLineItem, Workstream__c, box__BoxSign_Sigbner__c, box__BoxSign__c<br>Relationship: What<br>Length: 18 |
| OwnerId | reference | Yes | References: Group, User<br>Relationship: Owner<br>Length: 18 |
| AccountId | reference | No | References: Account<br>Relationship: Account<br>Length: 18 |
| CreatedById | reference | Yes | References: User<br>Relationship: CreatedBy<br>Length: 18 |
| LastModifiedById | reference | Yes | References: User<br>Relationship: LastModifiedBy<br>Length: 18 |

## System Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| CreatedDate | datetime | Yes | - |
| LastModifiedDate | datetime | Yes | - |
| SystemModstamp | datetime | Yes | - |

