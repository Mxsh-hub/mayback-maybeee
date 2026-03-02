BEGIN;

REVOKE ALL ON TABLE public.transactions FROM PUBLIC;
REVOKE ALL ON TABLE public.transaction_classifications FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.transactions TO authenticated;
GRANT SELECT ON TABLE public.transaction_classifications TO authenticated;

GRANT ALL ON TABLE public.transactions TO service_role;
GRANT ALL ON TABLE public.transaction_classifications TO service_role;

GRANT USAGE, SELECT ON SEQUENCE public.transactions_id_seq TO authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.transaction_classifications_id_seq TO service_role;

ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions FORCE ROW LEVEL SECURITY;

ALTER TABLE public.transaction_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_classifications FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS transactions_service_role_all ON public.transactions;
DROP POLICY IF EXISTS transactions_authenticated_select_own ON public.transactions;
DROP POLICY IF EXISTS transactions_authenticated_insert_own ON public.transactions;
DROP POLICY IF EXISTS transactions_authenticated_update_own ON public.transactions;
DROP POLICY IF EXISTS transactions_authenticated_delete_own ON public.transactions;

CREATE POLICY transactions_service_role_all
ON public.transactions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY transactions_authenticated_select_own
ON public.transactions
FOR SELECT
TO authenticated
USING (
    user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
);

CREATE POLICY transactions_authenticated_insert_own
ON public.transactions
FOR INSERT
TO authenticated
WITH CHECK (
    user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
);

CREATE POLICY transactions_authenticated_update_own
ON public.transactions
FOR UPDATE
TO authenticated
USING (
    user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
)
WITH CHECK (
    user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
);

CREATE POLICY transactions_authenticated_delete_own
ON public.transactions
FOR DELETE
TO authenticated
USING (
    user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
);

DROP POLICY IF EXISTS classifications_service_role_all ON public.transaction_classifications;
DROP POLICY IF EXISTS classifications_authenticated_select_own ON public.transaction_classifications;

CREATE POLICY classifications_service_role_all
ON public.transaction_classifications
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY classifications_authenticated_select_own
ON public.transaction_classifications
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.transactions t
        WHERE t.id = transaction_classifications.transaction_id
          AND t.user_id = COALESCE(auth.jwt() ->> 'user_id', auth.jwt() ->> 'sub')
    )
);

COMMIT;
