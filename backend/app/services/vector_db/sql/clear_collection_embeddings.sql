CREATE OR REPLACE FUNCTION clear_collection_embeddings(p_collection TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM embeddings
    WHERE collection = p_collection;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error clearing collection %: %', p_collection, SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;