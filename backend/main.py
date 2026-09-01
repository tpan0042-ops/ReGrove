from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}


@app.get("/plants")
def get_plants():
    # Connect to the local PostgreSQL database.
    connection = psycopg2.connect(
        host="localhost",
        port="5433",
        database="regrove",
        user="regrove",
        password="regrove_local"
    )

    # Read the sample plant data.
    cursor = connection.cursor()

    cursor.execute("""
        SELECT plant_species_id, scientific_name, common_name, native_status
        FROM plant_species
    """)

    rows = cursor.fetchall()

    plants = []

    for row in rows:
        plant = {
            "plant_species_id": row[0],
            "scientific_name": row[1],
            "common_name": row[2],
            "native_status": row[3]
        }

        plants.append(plant)

    cursor.close()
    connection.close()

    return plants


@app.get("/local-species/{postcode}")
def get_local_species(postcode: str):
    # Connect to the local PostgreSQL database.
    connection = psycopg2.connect(
        host="localhost",
        port="5433",
        database="regrove",
        user="regrove",
        password="regrove_local"
    )

    cursor = connection.cursor()

    # Find plant species linked to the postcode's bioregion.
    cursor.execute("""
        SELECT
            ps.plant_species_id,
            ps.scientific_name,
            ps.common_name,
            ps.native_status,
            lps.suitability_status,
            lps.evidence_summary
        FROM postcode_bioregion pb
        JOIN local_plant_suitability lps
            ON pb.bioregion_id = lps.bioregion_id
        JOIN plant_species ps
            ON lps.plant_species_id = ps.plant_species_id
        WHERE pb.postcode = %s
        ORDER BY ps.plant_species_id
    """, (postcode,))

    rows = cursor.fetchall()

    species = []

    for row in rows:
        species.append({
            "plant_species_id": row[0],
            "scientific_name": row[1],
            "common_name": row[2],
            "native_status": row[3],
            "suitability_status": row[4],
            "evidence_summary": row[5]
        })

    # Find vegetation context linked to the postcode.
    cursor.execute("""
        SELECT
            ec.evc_code,
            ec.evc_name,
            ec.conservation_status,
            pec.reference_year,
            pec.overlap_percent
        FROM postcode_evc_context pec
        JOIN evc_class ec
            ON pec.evc_id = ec.evc_id
        WHERE pec.postcode = %s
        ORDER BY pec.overlap_percent DESC
    """, (postcode,))

    vegetation_rows = cursor.fetchall()

    vegetation = []

    for row in vegetation_rows:
        vegetation.append({
            "evc_code": row[0],
            "evc_name": row[1],
            "conservation_status": row[2],
            "reference_year": row[3],
            "overlap_percent": float(row[4])
        })

    cursor.close()
    connection.close()

    return {
        "postcode": postcode,
        "species": species,
        "vegetation": vegetation
    }