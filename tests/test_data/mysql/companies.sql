INSERT INTO companies (company_id, name, address, tel, is_deleted, deleted_at, created_at, updated_at) VALUES (101, 'Test Company', 'Tokyo', '03-1234-5678', 0, NULL, NOW(), NOW());
INSERT INTO companies (company_id, name, address, tel, is_deleted, deleted_at, created_at, updated_at) VALUES (102, 'Deleted Company', 'Osaka', '06-1234-5678', 1, '2023-01-01 00:00:00', NOW(), NOW());
