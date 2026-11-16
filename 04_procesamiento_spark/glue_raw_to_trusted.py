import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType

# Inicialización del contexto Glue y Spark
args = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_BUCKET"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Sanitizar el nombre del bucket para remover llaves, corchetes, comillas o espacios accidentales
raw_bucket_param = args.get("S3_BUCKET", "")
bucket = raw_bucket_param.strip().replace("{", "").replace("}", "").replace("<", "").replace(">", "").replace('"', "").replace("'", "")
raw_base = f"s3://{bucket}/raw"
trusted_base = f"s3://{bucket}/trusted"

print(f"Iniciando Job AWS Glue: Procesamiento RAW -> TRUSTED (Silver)")
print(f"Bucket: s3://{bucket}")

# 1. Lectura de las 3 fuentes en la zona raw
print("[1/5] Leyendo datos originales de la zona RAW...")

# 1.1. Fuente RDS MariaDB (Tablas stars y planetary_systems)
df_stars_raw = spark.read.option("header", "true").csv(f"{raw_base}/rds/stars/")
df_systems_raw = spark.read.option("header", "true").csv(f"{raw_base}/rds/planetary_systems/")

# 1.2. Fuente EC2 (Catálogo CSV)
df_catalog_raw = spark.read.option("header", "true").csv(f"{raw_base}/ec2_csv/")

# 1.3. Fuente NASA API (Parámetros físicos y orbitales JSON)
df_api_raw = spark.read.option("multiline", "true").json(f"{raw_base}/nasa_api/")

print(f"  • Registros stars (RDS):             {df_stars_raw.count():,}")
print(f"  • Registros planetary_systems (RDS): {df_systems_raw.count():,}")
print(f"  • Registros catálogo (EC2):          {df_catalog_raw.count():,}")
print(f"  • Registros parámetros API (NASA):   {df_api_raw.count():,}")

# 2. Limipieza, estandarización y casteo de tipos 
print("[2/5] Limpiando, tipando y estandarizando campos...")

# Limpieza RDS
df_stars = df_stars_raw.select(
    F.col("star_id").cast(IntegerType()).alias("star_id"),
    F.trim(F.col("hostname")).alias("hostname")
).filter(F.col("hostname").isNotNull()).dropDuplicates(["hostname"])

df_systems = df_systems_raw.select(
    F.col("system_id").cast(IntegerType()).alias("system_id"),
    F.col("star_id").cast(IntegerType()).alias("star_id"),
    F.col("sy_dist").cast(DoubleType()).alias("sy_dist"),
    F.col("sy_pnum").cast(IntegerType()).alias("sy_pnum")
).dropDuplicates(["star_id"])

# Enlazar estrellas con sistemas planetarios
df_rds_joined = df_stars.join(df_systems, on="star_id", how="inner").select(
    "hostname", "sy_dist", "sy_pnum"
)

# Limpieza Catálogo EC2
df_catalog = df_catalog_raw.select(
    F.trim(F.col("pl_name")).alias("pl_name"),
    F.trim(F.col("hostname")).alias("hostname"),
    F.trim(F.col("discoverymethod")).alias("discoverymethod"),
    F.col("disc_year").cast(IntegerType()).alias("disc_year"),
    F.trim(F.col("disc_facility")).alias("disc_facility")
).filter(F.col("pl_name").isNotNull()).dropDuplicates(["pl_name"])

# Limpieza API NASA
df_api = df_api_raw.select(
    F.trim(F.col("pl_name")).alias("pl_name"),
    F.col("pl_rade").cast(DoubleType()).alias("pl_rade"),
    F.col("pl_bmasse").cast(DoubleType()).alias("pl_bmasse"),
    F.col("pl_orbper").cast(DoubleType()).alias("pl_orbper")
).filter(F.col("pl_name").isNotNull()).dropDuplicates(["pl_name"])

# 3. Integración heterogenea mediante JOINs
print("[3/5] Integrando las tres fuentes de datos (Catálogo + API + RDS)...")

# Join 1: Catálogo EC2 con Parámetros físicos API (clave: pl_name)
df_planets = df_catalog.join(df_api, on="pl_name", how="left")

# Join 2: Planetas integrados con Dimensión Estelar RDS (clave: hostname)
df_integrated = df_planets.join(df_rds_joined, on="hostname", how="left")

# 4. Aplicación de reglas de negocio y enriquecimiento de datos
print("[4/5] Aplicando clasificaciones astronómicas y reglas de negocio...")

df_enriched = df_integrated.withColumn(
    # Clasificación SDET de la NASA por radio planetario (Kopparapu et al. 2018)
    "size_category",
    F.when(F.col("pl_rade").isNull(), F.lit("No determinado"))
     .when((F.col("pl_rade") >= 0.5) & (F.col("pl_rade") <= 1.0), F.lit("Similar a la Tierra"))
     .when((F.col("pl_rade") > 1.0) & (F.col("pl_rade") <= 1.75), F.lit("Super-Tierra"))
     .when((F.col("pl_rade") > 1.75) & (F.col("pl_rade") <= 3.5), F.lit("Subneptuniano"))
     .when((F.col("pl_rade") > 3.5) & (F.col("pl_rade") <= 6.0), F.lit("Neptuniano"))
     .when((F.col("pl_rade") > 6.0) & (F.col("pl_rade") <= 14.3), F.lit("Gigante gaseoso"))
     .otherwise(F.lit("Otro / No clasificado"))
).withColumn(
    # Criterio específico de tamaño similar a la Tierra: 0.8 <= R <= 1.25
    "is_earth_similar",
    F.when((F.col("pl_rade") >= 0.8) & (F.col("pl_rade") <= 1.25), F.lit(True)).otherwise(F.lit(False))
).withColumn(
    # Criterio de sistema múltiple: 2 o más planetas confirmados
    "is_multiplanet_system",
    F.when(F.col("sy_pnum") >= 2, F.lit(True)).otherwise(F.lit(False))
)

# Reorganizar columnas principales del análisis
df_final = df_enriched.select(
    "pl_name",
    "hostname",
    "pl_rade",
    "pl_bmasse",
    "pl_orbper",
    "sy_dist",
    "sy_pnum",
    "discoverymethod",
    "disc_year",
    "disc_facility",
    "size_category",
    "is_earth_similar",
    "is_multiplanet_system"
)

total_trusted = df_final.count()
print(f"Total registros consolidados en Trusted: {total_trusted:,}")

# 5. Escritura de los datos limpios y enriquecidos en formato Parquet en la zona Trusted
target_path = f"{trusted_base}/exoplanets/"
print(f"[5/5] Escribiendo datos limpios en formato Parquet en: {target_path}")

df_final.write \
    .mode("overwrite") \
    .format("parquet") \
    .save(target_path)

print("Job AWS Glue completado exitosamente.")
print(f"Destino Parquet: {target_path}")

job.commit()
