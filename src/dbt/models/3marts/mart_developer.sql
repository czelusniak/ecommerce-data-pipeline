with transform as (
select
    id,
    name,
    description,
    count(*) as qtd_developer
from 
    {{ ref('stg_prepped_developer') }}
group by
    id,name,description
)
select * from transform