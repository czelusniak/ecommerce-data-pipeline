with source as (
    select * from {{ source('ecommerce_source', 'carts') }}
),

flattened as (
    select
        -- Simple columns
        id as cart_id,
        userid as user_id,
        date::date as order_date,
        
        -- 1:N relationship
        f.value:productId::int as product_id,
        f.value:quantity::int as quantity,
        extracted_at
        
    from source,
    -- THE EXPLOSION (LATERAL FLATTEN)
    -- 'FLATTEN' takes the array found in 'products' and creates a new row for every item inside it..
    -- If a cart has 3 products, this row will turn into 3 rows.
    lateral flatten(input => TRY_PARSE_JSON(source.products)) as f
)

select * from flattened