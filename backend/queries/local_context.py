from db.connection import get_connection

#fetches evc records for a given postcode and reference year from the database
def fetch_evc(postcode: str, reference_year: int) -> list[dict]:
    sql = """
        SELECT ec.evc_code, ec.evc_name, ec.conservation_status, pec.overlap_percent
        FROM postcode_evc_context pec
        JOIN evc_class ec ON ec.evc_id = pec.evc_id
        WHERE pec.postcode = %s AND pec.reference_year = %s
        ORDER BY pec.overlap_percent DESC
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (postcode, reference_year))
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

#fetches fauna evidence records for a given postcode from the database
def fetch_fauna_evidence(postcode: str) -> list[dict]:
    sql = """
        SELECT fs.scientific_name, fs.common_name, fs.taxon_group AS category,
               'fauna' AS kind, fo.record_count,
               fo.period_start AS earliest_record_date, fo.latest_record_date
        FROM fauna_occurrence_summary fo
        JOIN fauna_species fs ON fs.fauna_species_id = fo.fauna_species_id
        WHERE fo.postcode = %s
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (postcode,))
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

#fetches flora evidence records for a given postcode from the database
def fetch_flora_evidence(postcode: str) -> list[dict]:
    sql = """
        SELECT ps.scientific_name, ps.common_name, ps.native_status AS category,
               'flora' AS kind, po.record_count,
               po.period_start AS earliest_record_date, po.latest_record_date
        FROM plant_occurrence_summary po
        JOIN plant_species ps ON ps.plant_species_id = po.plant_species_id
        WHERE po.postcode = %s
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (postcode,))
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

#combines fauna and flora evidence for a given postcode, unclassified.
def fetch_species_evidence(postcode: str) -> list[dict]:
    """All species evidence (fauna + flora) for a postcode, unclassified.
    Historical/current/continuous classification happens in context.compare.
    """
    return fetch_fauna_evidence(postcode) + fetch_flora_evidence(postcode)