-- 1. Create User
CREATE OR REPLACE FUNCTION public.create_dashboard_user(
    p_email text,
    p_encrypted_password text,
    p_first_name text,
    p_last_name text,
    p_role text,
    p_tenant_id uuid DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = dashboard, public
AS $$
DECLARE
    new_id bigint;
BEGIN
    INSERT INTO dashboard.users (email, encrypted_password, first_name, last_name, role, tenant_id)
    VALUES (p_email, p_encrypted_password, p_first_name, p_last_name, p_role, p_tenant_id)
    RETURNING id INTO new_id;
    
    RETURN json_build_object('success', true, 'id', new_id);
EXCEPTION 
    WHEN unique_violation THEN
        RETURN json_build_object('success', false, 'message', 'Email already exists');
    WHEN OTHERS THEN
        RETURN json_build_object('success', false, 'message', SQLERRM);
END;
$$;

-- 2. Get All Users
CREATE OR REPLACE FUNCTION public.get_all_dashboard_users()
RETURNS TABLE (
    id bigint,
    email varchar,
    first_name varchar,
    last_name varchar,
    role varchar,
    tenant_id uuid,
    created_at timestamp
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = dashboard, public
AS $$
BEGIN
    RETURN QUERY 
    SELECT u.id, u.email, u.first_name, u.last_name, u.role, u.tenant_id, u.created_at
    FROM dashboard.users u
    ORDER BY u.created_at DESC;
END;
$$;

-- 3. Delete User
CREATE OR REPLACE FUNCTION public.delete_dashboard_user(p_user_id bigint)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = dashboard, public
AS $$
BEGIN
    DELETE FROM dashboard.users WHERE id = p_user_id;
    RETURN FOUND;
END;
$$;

-- 4. Get User By Email
CREATE OR REPLACE FUNCTION public.get_dashboard_user_by_email(user_email text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN (
        SELECT row_to_json(u)
        FROM dashboard.users u
        WHERE u.email = user_email
        AND u.active = true
        LIMIT 1
    );
END;
$$;
