## Evidencias 

1. **Captura del Bucket S3 en la Consola de AWS:**
   - Vista de las carpetas `raw/`, `trusted/`, `gold/`.
2. **Captura del contenido de la zona `raw/`:**
   - Mostrando las subcarpetas `rds/`, `ec2_csv/` y `nasa_api/`.
3. **Captura de la terminal con la ejecución exitosa:**
   - Salida del comando `python ingest_to_s3.py` mostrando el cuadro de resumen y tiempos.
4. **Captura del comando de validación:**
   - Salida de `aws s3 ls s3://<bucket>/raw/ --recursive`.