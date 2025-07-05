## Standard Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| Id | id | Yes | Length: 18 |
| LastName | string | Yes | Length: 80 |
| FirstName | string | No | Length: 40 |
| Salutation | picklist | No | Length: 40 |
| MiddleName | string | No | Length: 40 |
| Suffix | string | No | Length: 40 |
| Name | string | Yes | Length: 121 |
| MailingStreet | textarea | No | Length: 255 |
| MailingCity | string | No | Length: 40 |
| MailingState | string | No | Length: 80 |
| MailingPostalCode | string | No | Length: 20 |
| MailingCountry | string | No | Length: 80 |
| MailingLatitude | double | No | - |
| MailingLongitude | double | No | - |
| MailingGeocodeAccuracy | picklist | No | Length: 40 |
| MailingAddress | address | No | - |
| Phone | phone | No | Length: 40 |
| Fax | phone | No | Length: 40 |
| MobilePhone | phone | No | Length: 40 |
| HomePhone | phone | No | Length: 40 |
| OtherPhone | phone | No | Length: 40 |
| Email | email | No | Length: 80 |
| Title | string | No | Length: 128 |
| LastActivityDate | date | No | - |
| LastViewedDate | datetime | No | - |
| LastReferencedDate | datetime | No | - |

## Custom Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| External_ID__c | string | No | Length: 20 |
| FullName__c | string | No | Length: 1300 |
| NPI__c | string | No | Length: 20 |
| Specialty__c | picklist | No | Length: 255 |
| Days_Since_Last_Visit__c | double | No | - |
| Is_Physician__c | boolean | Yes | - |
| isMyContact__c | boolean | Yes | - |
| Contact_Account_Name__c | string | No | Length: 1300 |
| Last_Visited_By_Rep__c | reference | No | References: User<br>Relationship: Last_Visited_By_Rep__r<br>Length: 18 |
| Active__c | boolean | Yes | - |
| Mailing_Address_Compound__c | string | No | Length: 1300 |
| Other_Address_Compound__c | string | No | Length: 1300 |
| Business_Entity__c | reference | No | References: Account<br>Relationship: Business_Entity__r<br>Length: 18 |
| Employment_Status_MN__c | picklist | No | Length: 255 |
| Epic_ID__c | string | No | Length: 20 |
| Geography__c | picklist | No | Length: 255 |
| MN_Physician__c | boolean | Yes | - |
| NPI_MN__c | string | No | Length: 20 |
| Network__c | reference | No | References: Network__c<br>Relationship: Network__r<br>Length: 18 |
| Network_picklist__c | picklist | No | Length: 255 |
| Onboarding_Tasks__c | boolean | Yes | - |
| Outreach_Focus__c | boolean | Yes | - |
| Panel_Status__c | picklist | No | Length: 255 |
| Primary_Address__c | string | No | Length: 250 |
| Primary_Geography__c | picklist | No | Length: 255 |
| Primary_MGMA_Specialty__c | picklist | No | Length: 255 |
| Primary_Practice_Location__c | reference | No | References: Practice_Locations__c<br>Relationship: Primary_Practice_Location__r<br>Length: 18 |
| MN_Primary_SoS__c | reference | No | References: Account<br>Relationship: MN_Primary_SoS__r<br>Length: 18 |
| Provider_Participation__c | multipicklist | No | Length: 4099 |
| Provider_Start_Date__c | date | No | - |
| Provider_Term_Date__c | date | No | - |
| Provider_Type__c | picklist | No | Length: 255 |
| Secondary_Practice_Location__c | reference | No | References: Practice_Locations__c<br>Relationship: Secondary_Practice_Location__r<br>Length: 18 |
| Specialty_Group__c | picklist | No | Length: 255 |
| Sub_Network__c | picklist | No | Length: 255 |
| Sub_Specialty__c | multipicklist | No | Length: 4099 |
| MN_Primary_Geography__c | picklist | No | Length: 255 |
| MN_Address__Street__s | textarea | No | Length: 255 |
| MN_Address__City__s | string | No | Length: 40 |
| MN_Address__PostalCode__s | string | No | Length: 20 |
| MN_Address__StateCode__s | picklist | No | Length: 10 |
| MN_Address__CountryCode__s | picklist | No | Length: 10 |
| MN_Address__Latitude__s | double | No | - |
| MN_Address__Longitude__s | double | No | - |
| MN_Address__GeocodeAccuracy__s | picklist | No | Length: 40 |
| MN_Address__c | address | No | - |
| Last_Outreach_Activity_Date__c | date | No | - |
| MN_Secondary_SoS__c | reference | No | References: Account<br>Relationship: MN_Secondary_SoS__r<br>Length: 18 |
| MN_MGMA_Specialty__c | picklist | No | Length: 255 |
| MN_Specialty_Group__c | picklist | No | Length: 255 |
| MN_Provider_Summary__c | textarea | No | Length: 255 |
| MN_Provider_Detailed_Notes__c | textarea | No | Length: 32768 |
| MN_Tasks_Count__c | double | No | - |
| MN_Name_Specialty_Network__c | string | No | Length: 1300 |

## Relationship Fields
| LastModifiedById | reference | Yes | References: User<br>Relationship: 

## System Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| CreatedDate | datetime | Yes | - |
| LastModifiedDate | datetime | Yes | - |
| SystemModstamp | datetime | Yes | - |

