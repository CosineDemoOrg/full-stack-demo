with users as (
    select * from {{ ref('users') }}
),
items as (
    select * from {{ ref('items') }}
),
item_counts as (
    select
        user_id,
        count(*) as item_count
    from items
    group by user_id
)

select
    u.user_id,
    u.email,
    u.full_name,
    u.is_active,
    u.is_superuser,
    coalesce(ic.item_count, 0) as item_count
from users u
left join item_counts ic on ic.user_id = u.user_id;