with users as (
    select
        -- "user" is a reserved word in PostgreSQL, quoting ensures correct resolution
        ("user".id)::text   as user_id,
        "user".email        as email,
        "user".full_name    as full_name,
        "user".is_active    as is_active,
        "user".is_superuser as is_superuser
    from public."user"
)

select * from users;