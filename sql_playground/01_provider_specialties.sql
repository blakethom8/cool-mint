-- Query to list all specialties and count of providers
SELECT 
    primary_specialty,
    COUNT(*) as provider_count
FROM provider
GROUP BY primary_specialty
ORDER BY provider_count DESC; 