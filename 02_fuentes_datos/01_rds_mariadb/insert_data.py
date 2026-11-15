import os
import csv
import io
import requests
import pymysql

# 1. Consultar datos oficiales del NASA Exoplanet Archive
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

QUERY = """
SELECT hostname, MAX(sy_dist) AS sy_dist,
       MAX(sy_pnum) AS sy_pnum
FROM ps
WHERE default_flag = 1
AND hostname IS NOT NULL
GROUP BY hostname
ORDER BY hostname
"""

response = requests.get(
    TAP_URL,
    params={"query": QUERY, "format": "csv"},
    timeout=120
)
response.raise_for_status()

reader = csv.DictReader(io.StringIO(response.text))
records = list(reader)

if not records:
    raise RuntimeError("NASA no devolvió registros.")

print(f"Registros recibidos: {len(records)}")

# 2. Conectar con AWS RDS MariaDB
connection = pymysql.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ.get("DB_NAME", "exoplanets_db"),
    port=int(os.environ.get("DB_PORT", "3306")),
    charset="utf8mb4"
)

# 3. Insertar estrellas y sistemas planetarios
try:
    with connection.cursor() as cursor:
        for record in records:
            hostname = record["hostname"].strip()

            if not hostname:
                continue

            sy_dist = record["sy_dist"] or None
            sy_pnum = record["sy_pnum"] or None

            cursor.execute(
                """
                INSERT IGNORE INTO stars (hostname)
                VALUES (%s)
                """,
                (hostname,)
            )

            cursor.execute(
                "SELECT star_id FROM stars WHERE hostname = %s",
                (hostname,)
            )

            star_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO planetary_systems
                    (star_id, sy_dist, sy_pnum)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    sy_dist = VALUES(sy_dist),
                    sy_pnum = VALUES(sy_pnum)
                """,
                (star_id, sy_dist, sy_pnum)
            )

    connection.commit()
    print("Carga de datos completada correctamente.")

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM stars")
        print("Estrellas registradas:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM planetary_systems")
        print("Sistemas registrados:", cursor.fetchone()[0])

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
