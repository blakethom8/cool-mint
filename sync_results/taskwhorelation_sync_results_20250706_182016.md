# TaskWhoRelation Sync Results

**Sync Mode:** full
**Start Time:** 2025-07-06 18:20:10.248476
**End Time:** 2025-07-06 18:20:16.244581
**Duration:** 0:00:05.996105

## Summary Statistics

- **Total Processed:** 20
- **Total Successful:** 17
- **Total Failed:** 3
- **Batches Processed:** 1
- **Success Rate:** 85.00%

## Successful Records

```json
[
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxq4AA",
    "task_id": "00TUJ00000disvz2AA",
    "relation_id": "0038Z00003aegKpQAI",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxr4AA",
    "task_id": "00TUJ00000disw02AA",
    "relation_id": "0038Z00003ae5r9QAA",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxs4AA",
    "task_id": "00TUJ00000disw12AA",
    "relation_id": "0038Z00003aeGinQAE",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxt4AA",
    "task_id": "00TUJ00000disw22AA",
    "relation_id": "0038Z00003adkI8QAI",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxw4AA",
    "task_id": "00TUJ00000disw52AA",
    "relation_id": "0038Z00003afTkwQAE",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxx4AA",
    "task_id": "00TUJ00000disw62AA",
    "relation_id": "0038Z00003ae5r9QAA",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxy4AA",
    "task_id": "00TUJ00000disw72AA",
    "relation_id": "0038Z00003advDFQAY",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vxz4AA",
    "task_id": "00TUJ00000disw82AA",
    "relation_id": "0038Z00003aeEAbQAM",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vy04AA",
    "task_id": "00TUJ00000disw92AA",
    "relation_id": "0038Z00003afzCjQAI",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vy14AA",
    "task_id": "00TUJ00000diswA2AQ",
    "relation_id": "0038Z00003afyI7QAI",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vy24AA",
    "task_id": "00TUJ00000diswB2AQ",
    "relation_id": "0038Z00003aeEKXQA2",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vy54AA",
    "task_id": "00TUJ00000diswE2AQ",
    "relation_id": "003UJ00000KBn1wYAD",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k2vy64AA",
    "task_id": "00TUJ00000diswF2AQ",
    "relation_id": "0038Z00003aeEPhQAM",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k3j6r4AA",
    "task_id": "00TUJ00000dj6xL2AQ",
    "relation_id": "0038Z00003aepq8QAA",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k3j6s4AA",
    "task_id": "00TUJ00000dj6xM2AQ",
    "relation_id": "0038Z00003aepq8QAA",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k3j6t4AA",
    "task_id": "00TUJ00000dj6xN2AQ",
    "relation_id": "0038Z00003aepq8QAA",
    "error": null,
    "action": "inserted"
  },
  {
    "success": true,
    "salesforce_id": "0RTUJ00000k3j6u4AA",
    "task_id": "00TUJ00000dj6xO2AQ",
    "relation_id": "0038Z00003aepq8QAA",
    "error": null,
    "action": "inserted"
  }
]
```

## Failed Records

```json
[
  {
    "success": false,
    "salesforce_id": "0RTUJ00000k2vxv4AA",
    "task_id": "00TUJ00000disw42AA",
    "relation_id": "0038Z00003aeExNQAU",
    "error": "(psycopg2.errors.ForeignKeyViolation) insert or update on table \"sf_taskwhorelations\" violates foreign key constraint \"sf_taskwhorelations_task_id_fkey\"\nDETAIL:  Key (task_id)=(00TUJ00000disw42AA) is not present in table \"sf_activities\".\n\n[SQL: INSERT INTO sf_taskwhorelations (salesforce_id, is_deleted, type, relation_id, task_id, created_by_id, last_modified_by_id, sf_created_date, sf_last_modified_date, sf_system_modstamp, created_at, updated_at) VALUES (%(salesforce_id)s, %(is_deleted)s, %(type)s, %(relation_id)s, %(task_id)s, %(created_by_id)s, %(last_modified_by_id)s, %(sf_created_date)s, %(sf_last_modified_date)s, %(sf_system_modstamp)s, %(created_at)s, %(updated_at)s) ON CONFLICT ON CONSTRAINT sf_taskwhorelations_salesforce_id_key DO UPDATE SET is_deleted = excluded.is_deleted, type = excluded.type, relation_id = excluded.relation_id, task_id = excluded.task_id, created_by_id = excluded.created_by_id, last_modified_by_id = excluded.last_modified_by_id, sf_last_modified_date = excluded.sf_last_modified_date, sf_system_modstamp = excluded.sf_system_modstamp RETURNING sf_taskwhorelations.id]\n[parameters: {'salesforce_id': '0RTUJ00000k2vxv4AA', 'is_deleted': False, 'type': 'Contact', 'relation_id': '0038Z00003aeExNQAU', 'task_id': '00TUJ00000disw42AA', 'created_by_id': '005UJ000002LtoLYAS', 'last_modified_by_id': '005UJ000002LtoLYAS', 'sf_created_date': '2024-09-24T06:32:04.000+0000', 'sf_last_modified_date': '2024-09-24T06:32:04.000+0000', 'sf_system_modstamp': '2025-06-01T13:34:46.000+0000', 'created_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 207689), 'updated_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 207691)}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
    "action": null
  },
  {
    "success": false,
    "salesforce_id": "0RTUJ00000k2vy34AA",
    "task_id": "00TUJ00000diswC2AQ",
    "relation_id": "0038Z00003aeGeCQAU",
    "error": "(psycopg2.errors.ForeignKeyViolation) insert or update on table \"sf_taskwhorelations\" violates foreign key constraint \"sf_taskwhorelations_task_id_fkey\"\nDETAIL:  Key (task_id)=(00TUJ00000diswC2AQ) is not present in table \"sf_activities\".\n\n[SQL: INSERT INTO sf_taskwhorelations (salesforce_id, is_deleted, type, relation_id, task_id, created_by_id, last_modified_by_id, sf_created_date, sf_last_modified_date, sf_system_modstamp, created_at, updated_at) VALUES (%(salesforce_id)s, %(is_deleted)s, %(type)s, %(relation_id)s, %(task_id)s, %(created_by_id)s, %(last_modified_by_id)s, %(sf_created_date)s, %(sf_last_modified_date)s, %(sf_system_modstamp)s, %(created_at)s, %(updated_at)s) ON CONFLICT ON CONSTRAINT sf_taskwhorelations_salesforce_id_key DO UPDATE SET is_deleted = excluded.is_deleted, type = excluded.type, relation_id = excluded.relation_id, task_id = excluded.task_id, created_by_id = excluded.created_by_id, last_modified_by_id = excluded.last_modified_by_id, sf_last_modified_date = excluded.sf_last_modified_date, sf_system_modstamp = excluded.sf_system_modstamp RETURNING sf_taskwhorelations.id]\n[parameters: {'salesforce_id': '0RTUJ00000k2vy34AA', 'is_deleted': False, 'type': 'Contact', 'relation_id': '0038Z00003aeGeCQAU', 'task_id': '00TUJ00000diswC2AQ', 'created_by_id': '005UJ000002LtoLYAS', 'last_modified_by_id': '005UJ000002LtoLYAS', 'sf_created_date': '2024-09-24T06:32:04.000+0000', 'sf_last_modified_date': '2024-09-24T06:32:04.000+0000', 'sf_system_modstamp': '2025-06-08T12:10:29.000+0000', 'created_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 234279), 'updated_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 234280)}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
    "action": null
  },
  {
    "success": false,
    "salesforce_id": "0RTUJ00000k2vy44AA",
    "task_id": "00TUJ00000diswD2AQ",
    "relation_id": "003UJ00000CAX5VYAX",
    "error": "(psycopg2.errors.ForeignKeyViolation) insert or update on table \"sf_taskwhorelations\" violates foreign key constraint \"sf_taskwhorelations_task_id_fkey\"\nDETAIL:  Key (task_id)=(00TUJ00000diswD2AQ) is not present in table \"sf_activities\".\n\n[SQL: INSERT INTO sf_taskwhorelations (salesforce_id, is_deleted, type, relation_id, task_id, created_by_id, last_modified_by_id, sf_created_date, sf_last_modified_date, sf_system_modstamp, created_at, updated_at) VALUES (%(salesforce_id)s, %(is_deleted)s, %(type)s, %(relation_id)s, %(task_id)s, %(created_by_id)s, %(last_modified_by_id)s, %(sf_created_date)s, %(sf_last_modified_date)s, %(sf_system_modstamp)s, %(created_at)s, %(updated_at)s) ON CONFLICT ON CONSTRAINT sf_taskwhorelations_salesforce_id_key DO UPDATE SET is_deleted = excluded.is_deleted, type = excluded.type, relation_id = excluded.relation_id, task_id = excluded.task_id, created_by_id = excluded.created_by_id, last_modified_by_id = excluded.last_modified_by_id, sf_last_modified_date = excluded.sf_last_modified_date, sf_system_modstamp = excluded.sf_system_modstamp RETURNING sf_taskwhorelations.id]\n[parameters: {'salesforce_id': '0RTUJ00000k2vy44AA', 'is_deleted': False, 'type': 'Contact', 'relation_id': '003UJ00000CAX5VYAX', 'task_id': '00TUJ00000diswD2AQ', 'created_by_id': '005UJ000002LtoLYAS', 'last_modified_by_id': '005UJ000002LtoLYAS', 'sf_created_date': '2024-09-24T06:32:04.000+0000', 'sf_last_modified_date': '2024-09-24T06:32:04.000+0000', 'sf_system_modstamp': '2025-06-08T12:10:29.000+0000', 'created_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 235688), 'updated_at': datetime.datetime(2025, 7, 7, 1, 20, 16, 235689)}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
    "action": null
  }
]
```

### Failed Records Summary

- **str:** 3 records
