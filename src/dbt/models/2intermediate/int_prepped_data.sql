SELECT A.ID 
    , FIRST_NAME
    , LAST_NAME
    , birthdate
    , BOOKING_REFERENCE
    , HOTEL
    , CAST(B.BOOKING_DATE AS DATE) as BOOKING_DATE
    , COST
FROM {{ref('stg_customer')}}  A
JOIN {{ref('stg_combined_bookings')}} B
on A.ID = B.ID