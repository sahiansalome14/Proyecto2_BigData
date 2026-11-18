"""Analisis descriptivo de exoplanetas con PySpark sobre datos trusted en S3."""

import argparse

from pyspark.sql import SparkSession, functions as F


def parse_args():
    parser = argparse.ArgumentParser(description="Analisis descriptivo de exoplanetas")
    
    parser.add_argument("--analytic_path", required=True, help="Prefijo S3 de salida para resultados")
    parser.add_argument("--metadata_db", required=True, help="Nombre de base de datos donde se almacena tabla con metadata (Catalog)")  
    parser.add_argument("--metadata_table",required=True, help="Nombre de tabla con metadata")   

    args = parser.parse_args()

    if not args.analytic_path.startswith("s3://"):
        parser.error("Las rutas deben comenzar por s3://")

    return args


def main():
    args = parse_args()

    analytic_path = args.analytic_path.rstrip("/")
    metadata_db = args.metadata_db
    metadata_table = args.metadata_table
    
    spark = (SparkSession.builder
                .appName("exoplanets-analisis-descriptivo")
                .enableHiveSupport()
                .getOrCreate()
            )
    df = None

    try:
        
        df = spark.table(f"{metadata_db}.{metadata_table}").cache()
        df.createOrReplaceTempView("exoplanets")

        # Consulta 1: Distribución de exoplanetas por categoría de tamaño.
            # Pregunta: ¿Qué tipos de planetas predominan entre los exoplanetas confirmados y cuáles son sus valores promedio de radio, masa y periodo orbital?
        q1 = spark.sql("""
            SELECT size_category,
                   COUNT(*) AS planetas,
                   ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS porcentaje,
                   ROUND(AVG(pl_rade), 2) AS radio_promedio_re,
                   ROUND(AVG(pl_bmasse), 2) AS masa_promedio_me,
                   ROUND(AVG(pl_orbper), 2) AS periodo_promedio_dias
            FROM exoplanets
            GROUP BY size_category
            ORDER BY planetas DESC
        """)

        # Consulta 2: descubrimientos por decada y método de detección
            # Pregunta: ¿Cómo ha evolucionado el número de descubrimientos y qué métodos han dominado en cada década?
        q2 = (
            df.filter(F.col("disc_year").isNotNull())
            .withColumn("decada", (F.floor(F.col("disc_year") / 10) * 10).cast("int"))
            .groupBy("decada", "discoverymethod")
            .agg(F.count("*").alias("planetas"))
            .orderBy("decada", F.desc("planetas"))
        )

        # Consulta 3: sistemas multiplanetarios con mayor diversidad de tamaños
            # Pregunta: ¿Qué estrellas albergan más planetas y cuántas categorías de tamaño distintas presentan sus sistemas?
            # La diversidad cuenta solo categorías determinadas (se excluyen No determinado y Otro / No clasificado).
        q3 = spark.sql("""
            SELECT hostname,
                   COUNT(*) AS planetas,
                   COUNT(DISTINCT CASE
                       WHEN size_category NOT IN ('No determinado', 'Otro / No clasificado')
                       THEN size_category END) AS categorias_de_tamano,
                   ROUND(MIN(pl_rade), 2) AS radio_min_re,
                   ROUND(MAX(pl_rade), 2) AS radio_max_re,
                   ROUND(MAX(sy_dist), 2) AS distancia_pc
            FROM exoplanets
            WHERE hostname IS NOT NULL
            GROUP BY hostname
            HAVING COUNT(*) >= 2
            ORDER BY planetas DESC, categorias_de_tamano DESC, hostname
            LIMIT 10
        """)

        # Consulta 4: sistemas planetarios más cercanos a la Tierra
            # Pregunta: ¿Cuáles son los sistemas con planetas confirmados más cercanos a la Tierra y cuántos de sus planetas tienen tamaño similar al terrestre?
            # sy_dist está en parsecs; se convierte a años luz (1 pc ≈ 3,26156 al).
        q4 = (
            df.filter(F.col("sy_dist").isNotNull() & F.col("hostname").isNotNull())
            .groupBy("hostname")
            .agg(
                F.max("sy_dist").alias("distancia_pc"),
                F.count("*").alias("planetas"),
                F.sum(F.col("is_earth_similar").cast("int")).alias("planetas_similares_tierra"),
                F.concat_ws(", ", F.sort_array(F.collect_set("size_category"))).alias("categorias"),
            )
            .withColumn("distancia_al", F.round(F.col("distancia_pc") * 3.26156, 2))
            .withColumn("distancia_pc", F.round("distancia_pc", 2))
            .orderBy("distancia_pc", "hostname")
            .limit(10)
        )

        # Consulta 5: mediana de periodos orbitales y masas.
            # Pregunta: ¿Cómo cambian el periodo orbital y la masa según el tamaño del planeta? Se usan medianas (percentile_approx) porque las distribuciones tienen valores extremos.
        q5 = spark.sql("""
            SELECT size_category,
                   COUNT(*) AS planetas,
                   COUNT(pl_orbper) AS con_periodo,
                   ROUND(percentile_approx(pl_orbper, 0.5), 2) AS periodo_mediana_dias,
                   ROUND(MIN(pl_orbper), 2) AS periodo_min_dias,
                   ROUND(MAX(pl_orbper), 2) AS periodo_max_dias,
                   ROUND(percentile_approx(pl_bmasse, 0.5), 2) AS masa_mediana_me
            FROM exoplanets
            GROUP BY size_category
            ORDER BY periodo_mediana_dias
        """)

        resultados = {
            "q1_distribucion_tamano": q1,
            "q2_descubrimientos_decada_metodo": q2,
            "q3_sistemas_multiplanetarios": q3,
            "q4_sistemas_cercanos": q4,
            "q5_caracteristicas_por_categoria": q5,
        }

        for nombre, resultado in resultados.items():
            print(f"\n===== {nombre} =====", flush=True)

            resultado.show(40, truncate=False) # para logs de emr

            destino = f"{analytic_path}/{nombre}/"

            resultado.coalesce(1).write.mode("overwrite").option("header",True).csv(destino) # coalesce porque son datos pequeños

            print(f"Guardado: {destino}", flush=True)

        print("Analisis finalizado correctamente.", flush=True)
    finally:
        if df is not None:
            df.unpersist()
        spark.stop()


if __name__ == "__main__":
    main()
