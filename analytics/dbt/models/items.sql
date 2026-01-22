with items as (
    select
        item.id::text         as item_id,
        item.owner_id::text   as user_id,
        item.title            as title,
        item.description      as description
    from public.item as item
)

select * from items;