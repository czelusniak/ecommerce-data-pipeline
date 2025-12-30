with 

source as (

    select * from {{ source('ecommerce_source', 'products') }}

),

renamed as (

    select
        product_id,
        title,
        price,
        category,
        description,
        extracted_at
    from source
)

select * from renamed