# Contact Schema Documentation

Generated on: 2025-07-05 11:33:16

## Standard Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| Id | id | Yes | Length: 18 |
| IsDeleted | boolean | Yes | - |
| LastName | string | Yes | Length: 80 |
| FirstName | string | No | Length: 40 |
| Salutation | picklist | No | Length: 40 |
| MiddleName | string | No | Length: 40 |
| Suffix | string | No | Length: 40 |
| Name | string | Yes | Length: 121 |
| OtherStreet | textarea | No | Length: 255 |
| OtherCity | string | No | Length: 40 |
| OtherState | string | No | Length: 80 |
| OtherPostalCode | string | No | Length: 20 |
| OtherCountry | string | No | Length: 80 |
| OtherLatitude | double | No | - |
| OtherLongitude | double | No | - |
| OtherGeocodeAccuracy | picklist | No | Length: 40 |
| OtherAddress | address | No | - |
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
| Department | string | No | Length: 80 |
| HasOptedOutOfEmail | boolean | Yes | - |
| HasOptedOutOfFax | boolean | Yes | - |
| DoNotCall | boolean | Yes | - |
| LastActivityDate | date | No | - |
| LastCURequestDate | datetime | No | - |
| LastCUUpdateDate | datetime | No | - |
| LastViewedDate | datetime | No | - |
| LastReferencedDate | datetime | No | - |
| EmailBouncedReason | string | No | Length: 255 |
| EmailBouncedDate | datetime | No | - |
| IsEmailBounced | boolean | Yes | - |
| PhotoUrl | url | No | Length: 255 |
| Jigsaw | string | No | Length: 20 |
| Pronouns | picklist | No | Length: 255 |
| GenderIdentity | picklist | No | Length: 255 |
| IsPriorityRecord | boolean | Yes | - |

## Custom Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| VIP__c | boolean | Yes | - |
| Hours__c | double | No | - |
| CityState__c | string | No | Length: 1300 |
| Degree__c | string | No | Length: 100 |
| EmploymentStatus__c | string | No | Length: 255 |
| Asst_Name__c | string | No | Length: 100 |
| Asst_Email__c | email | No | Length: 80 |
| Asst_Phone__c | phone | No | Length: 40 |
| MD__c | boolean | Yes | - |
| CSI_Community__c | picklist | No | Length: 255 |
| Sub_community__c | picklist | No | Length: 255 |
| Role__c | picklist | No | Length: 255 |
| Employment_Status__c | picklist | No | Length: 255 |
| External_ID__c | string | No | Length: 20 |
| FullName__c | string | No | Length: 1300 |
| Last_Visited_By__c | string | No | Length: 255 |
| Last_Visited_Date__c | date | No | - |
| NPI__c | string | No | Length: 20 |
| OwnersIds__c | string | No | Length: 200 |
| Referring_Affiliated_Revenue__c | currency | No | - |
| Referring_Loyalty_Segment__c | string | No | Length: 255 |
| Referring_Member_Revenue__c | currency | No | - |
| Referring_Non_Member_Revenue__c | currency | No | - |
| Referring_Primary_Facility__c | string | No | Length: 255 |
| Referring_Revenue_Share__c | percent | No | - |
| Referring_Total_Revenue__c | percent | No | - |
| Revenue_range__c | textarea | No | Length: 255 |
| Ride_Along__c | boolean | Yes | - |
| Specialty__c | picklist | No | Length: 255 |
| Status__c | picklist | No | Length: 255 |
| Total_Amount_Spent__c | currency | No | - |
| Total_Annual_Amount_Spent__c | currency | No | - |
| Web__c | string | No | Length: 255 |
| Activity_Last_12_Months__c | double | No | - |
| Activity_Last_3_Months__c | double | No | - |
| Days_Since_Last_Visit__c | double | No | - |
| Is_Physician__c | boolean | Yes | - |
| isMyContact__c | boolean | Yes | - |
| Contact_Account_Name__c | string | No | Length: 1300 |
| Last_Visited_By_Rep__c | reference | No | References: User<br>Relationship: Last_Visited_By_Rep__r<br>Length: 18 |
| Active__c | boolean | Yes | - |
| Mailing_Address_Compound__c | string | No | Length: 1300 |
| Other_Address_Compound__c | string | No | Length: 1300 |
| Business_Entity__c | reference | No | References: Account<br>Relationship: Business_Entity__r<br>Length: 18 |
| CFTE_Current__c | double | No | - |
| Employment_Status_MN__c | picklist | No | Length: 255 |
| Epic_ID__c | string | No | Length: 20 |
| Focus_Contact__c | boolean | Yes | - |
| Geography__c | picklist | No | Length: 255 |
| Insurance_Notes__c | textarea | No | Length: 32768 |
| MN_Physician__c | boolean | Yes | - |
| NPI_MN__c | string | No | Length: 20 |
| Network_Leveling__c | multipicklist | No | Length: 4099 |
| Network__c | reference | No | References: Network__c<br>Relationship: Network__r<br>Length: 18 |
| Network_picklist__c | picklist | No | Length: 255 |
| Onboarding_Tasks__c | boolean | Yes | - |
| Outreach_Focus__c | boolean | Yes | - |
| Panel_Status__c | picklist | No | Length: 255 |
| Primary_Address__c | string | No | Length: 250 |
| Primary_Department__c | reference | No | References: Department__c<br>Relationship: Primary_Department__r<br>Length: 18 |
| Primary_Geography__c | picklist | No | Length: 255 |
| Primary_MGMA_Specialty__c | picklist | No | Length: 255 |
| Primary_Practice_Location__c | reference | No | References: Practice_Locations__c<br>Relationship: Primary_Practice_Location__r<br>Length: 18 |
| MN_Primary_SoS__c | reference | No | References: Account<br>Relationship: MN_Primary_SoS__r<br>Length: 18 |
| Provider_Participation__c | multipicklist | No | Length: 4099 |
| Provider_Start_Date__c | date | No | - |
| Provider_Term_Date__c | date | No | - |
| Provider_Type__c | picklist | No | Length: 255 |
| T_Total_Visits__c | double | No | - |
| Secondary_Practice_Location__c | reference | No | References: Practice_Locations__c<br>Relationship: Secondary_Practice_Location__r<br>Length: 18 |
| Specialty_Group__c | picklist | No | Length: 255 |
| Sub_Network__c | picklist | No | Length: 255 |
| Sub_Specialty__c | multipicklist | No | Length: 4099 |
| T_Outpatient_Visits__c | double | No | - |
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
| T_Core_Visits__c | double | No | - |
| T_Out_of_Network_Visits__c | double | No | - |
| T_South_Coastal_Visits__c | double | No | - |
| T_North_Coastal_Visits__c | double | No | - |
| T_Santa_Clarita_Visits__c | double | No | - |
| T_San_Gabriel_Valley_Visits__c | double | No | - |
| T_San_Fernando_Valley_Visits__c | double | No | - |
| T_Long_Beach_Visits__c | double | No | - |
| T_South_Bay_Visits__c | double | No | - |
| T_Downtown_LA_Visits__c | double | No | - |
| T_Southeast_LA_Visits__c | double | No | - |
| T_Primary_Payer_Type__c | string | No | Length: 100 |
| T_Secondary_Payer_Type__c | string | No | Length: 100 |
| T_Primary_City__c | string | No | Length: 100 |
| T_Secondary_City__c | string | No | Length: 100 |
| MN_Secondary_SoS__c | reference | No | References: Account<br>Relationship: MN_Secondary_SoS__r<br>Length: 18 |
| MN_MGMA_Specialty__c | picklist | No | Length: 255 |
| MN_Specialty_Group__c | picklist | No | Length: 255 |
| T_Inpatient_Visits__c | double | No | - |
| MN_Provider_Summary__c | textarea | No | Length: 255 |
| MN_Provider_Detailed_Notes__c | textarea | No | Length: 32768 |
| MN_Tasks_Count__c | double | No | - |
| MN_Name_Specialty_Network__c | string | No | Length: 1300 |

## Relationship Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| MasterRecordId | reference | No | References: Contact<br>Relationship: MasterRecord<br>Length: 18 |
| AccountId | reference | No | References: Account<br>Relationship: Account<br>Length: 18 |
| RecordTypeId | reference | No | References: RecordType<br>Relationship: RecordType<br>Length: 18 |
| ReportsToId | reference | No | References: Contact<br>Relationship: ReportsTo<br>Length: 18 |
| OwnerId | reference | Yes | References: User<br>Relationship: Owner<br>Length: 18 |
| CreatedById | reference | Yes | References: User<br>Relationship: CreatedBy<br>Length: 18 |
| LastModifiedById | reference | Yes | References: User<br>Relationship: LastModifiedBy<br>Length: 18 |
| JigsawContactId | string | No | Relationship: JigsawContact<br>Length: 20 |

## System Fields

| Field Name | Type | Required | Details |
|------------|------|----------|----------|
| CreatedDate | datetime | Yes | - |
| LastModifiedDate | datetime | Yes | - |
| SystemModstamp | datetime | Yes | - |

