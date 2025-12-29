SELECT
  BOOKING_DATE,
  HOTEL,
  COUNT(ID) as count_bookings
FROM {{ ref('int_prepped_data') }}
GROUP BY
  BOOKING_DATE,
  HOTEL