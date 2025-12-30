with source as (
    select * from {{ source('ecommerce_source', 'carts') }}
),

flattened as (
    select
        -- Simple columns
        id as cart_id,
        userid as user_id,
        date as order_date,
        
        -- THE MAGIC PART: 
        -- parse_json converts the string string "[...]" into a real JSON object
        -- value:productId extracts the ID from the JSON
        f.value:productId::int as product_id,
        f.value:quantity::int as quantity
        
    from source,
    -- LATERAL FLATTEN explodes the array. 
    -- If a cart has 3 products, this row will turn into 3 rows.
    lateral flatten(input => parse_json(source.products)) f
)

select * from flattened