from fastapi import FastAPI
import psycopg2

app = FastAPI()


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