with carts as (
    select * from {{ ref('stg_carts') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

joined_data as (
    select
        carts.cart_id,
        carts.user_id,
        carts.product_id,
        carts.order_date,


        products.product_name,
        products.category,
        products.image_url,

        -- Metrics & Calculations
        carts.quantity,
        products.price as unit_price,

        (carts.quantity * products.price) as total_item_amount,

        carts.extracted_at
    from carts
    -- LEFT JOIN so we don't lose the sale if the product info is missing
    left join products on carts.product_id = products.product_id
)

select * from joined_data