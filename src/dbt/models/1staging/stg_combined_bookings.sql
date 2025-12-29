SELECT 
    id,
    booking_reference,
    hotel,
    TO_DATE(REPLACE(REPLACE(booking_date, '–', '-'), '—', '-')) as booking_date,
    cost
FROM {{ref('bookings_1')}}
UNION ALL
SELECT 
    id,
    booking_reference,
    hotel,
    TO_DATE(REPLACE(REPLACE(booking_date, '–', '-'), '—', '-')) as booking_date,
    cost
FROM {{ref('bookings_2')}}
