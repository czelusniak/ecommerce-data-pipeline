with 

source as (

    select * from {{ source('ecommerce_source', 'products') }}

),

renamed as (

    select
        id as product_id,
        title as product_name,
        price::decimal(10,2) as price,
        category,
        description,
        image as image_url,
        
        -- 1:1 relationship
        TRY_PARSE_JSON(rating):rate::decimal(3,1) as rating_score,
        TRY_PARSE_JSON(rating):count::int as rating_count,

        extracted_at
    from source
)

select * from renamed