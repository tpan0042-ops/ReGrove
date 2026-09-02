from db.connection import get_connection

#helper to perform postcode validation
def postcode_exists(postcode: str) -> bool:
    sql = """
        SELECT 1 FROM postcode WHERE postcode = %s
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (postcode,))
        return bool(cur.fetchone())