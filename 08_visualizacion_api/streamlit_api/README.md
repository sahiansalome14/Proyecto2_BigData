# Punto 8 (parte 2): Aplicación Streamlit con API Gateway y Lambda

Aplicación interactiva para consultar exoplanetas. El frontend (Streamlit) no lee el Parquet: pide todo por HTTP a **API Gateway**, que invoca una **Lambda** que lee `s3://exoplanets-data-lake-225180590593-us-east-1/trusted/exoplanets/` con Boto3 y PyArrow.

## Flujo de la aplicación

1. **Streamlit** solicita información mediante `api_client.py`.
2. **API Gateway** recibe la petición HTTP y la envía a Lambda.
3. **AWS Lambda** ejecuta nuestro `handler.py`.
4. `handler.py` consulta S3, procesa los datos y prepara una respuesta JSON.
5. **Lambda** devuelve la respuesta a API Gateway.
6. **API Gateway** devuelve la respuesta a Streamlit.

### Qué hace cada servicio

| Servicio | Qué hace | Dónde se configura |
|---|---|---|
| **API Gateway** | Es la puerta de entrada pública: expone las URLs (`GET /planets`, `GET /statistics/size`) y reenvía cada petición a la Lambda. No contiene lógica. | Pasos del apartado 4 (API, integración, rutas, permiso y stage). |
| **AWS Lambda** | Ejecuta `handler.py`: valida los parámetros, lee los Parquet de S3, filtra o cuenta y responde JSON. | Paso 3 (creación de la función). |

## Archivos

| Archivo | Función |
|---|---|
| `app.py` | Interfaz Streamlit: búsqueda, filtro por tamaño, checkbox "similares a la Tierra", tabla y gráfico de barras (Plotly). |
| `api_client.py` | Funciones que llaman a la API por HTTP (`requests`). La URL se toma de la variable `API_URL`. |
| `lambda/handler.py` | Backend: una sola Lambda con los endpoints. |
| `lambda/requirements.txt`, `requirements.txt` | Dependencias de Lambda y de Streamlit. |

## Endpoints

| Endpoint | Descripción |
|---|---|
| `GET /planets?q=Kepler-22` | Busca por nombre (contiene el texto, sin distinguir mayúsculas). |
| `GET /planets?size_category=Super-Tierra` | Filtra por categoría de tamaño. |
| `GET /planets?earth_like=true` | Solo planetas con `is_earth_similar = true`. |
| `GET /planets?sort=sy_dist` | Ordena de menor a mayor distancia (sin nulos); se usa para los sistemas más cercanos. |
| `GET /statistics/size` | Cantidad de planetas por categoría de tamaño. |

Los tres filtros de `/planets` se pueden combinar. Responde JSON, valida `earth_like` (`true`/`false`) y la longitud de los parámetros (400 si son inválidos), y devuelve como máximo 200 registros (`total` indica cuántos coinciden).

## Despliegue de AWS Lambda y API Gateway

La función Lambda consulta los datos de exoplanetas en Amazon S3 y se expone mediante una API HTTP de Amazon API Gateway.

### 1. Requisitos previos

- Cuenta de AWS Academy con acceso a los servicios necesarios.
- AWS CLI instalado y configurado, con credenciales temporales activas.
- Python 3.12 y `pip` para empaquetar las dependencias compatibles con Lambda (no hace falta Docker).
- Archivo `lambda_deployment.zip` generado previamente (contiene `handler.py` y las dependencias, incluido PyArrow). Si no existe o cambiaste `handler.py`, se genera así:

```bash
# Desde la carpeta streamlit_api
pip install -r lambda/requirements.txt \
  --target package \
  --platform manylinux2014_x86_64 \
  --python-version 3.12 \
  --only-binary=:all:

# 2. Copiar el código de la Lambda a la raíz del paquete
cp lambda/handler.py package/handler.py          # PowerShell: Copy-Item lambda\handler.py package\handler.py

# 3. Comprimir el contenido de package/ (handler.py debe quedar en la raíz del zip)
python -c "import os,zipfile; z=zipfile.ZipFile('lambda_deployment.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f),'package')) for r,_,fs in os.walk('package') for f in fs]; z.close()"
```


Para actualizar una Lambda ya creada con el zip nuevo:

```bash
aws lambda update-function-code \
  --function-name ExoplanetsQueryFunction \
  --zip-file fileb://lambda_deployment.zip \
  --region us-east-1
```

```bash
aws --version
aws sts get-caller-identity
aws configure get region
```


### 2. Variables de entorno de la Lambda

Crear el archivo `lambda-env.json`:

```json
{
  "Variables": {
    "S3_BUCKET": "NOMBRE_DEL_BUCKET",
    "S3_PREFIX": "trusted/exoplanets/"
  }
}
```

Reemplazar `NOMBRE_DEL_BUCKET` por el bucket del proyecto.

### 3. Creación de AWS Lambda

```bash
aws lambda create-function \
  --function-name ExoplanetsQueryFunction \
  --runtime python3.12 \
  --architectures x86_64 \
  --role ARN_DEL_ROL_IAM \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda_deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment file://lambda-env.json \
  --region us-east-1
```

Qué significa cada parámetro:

| Parte | Qué significa | Por qué |
|---|---|---|
| `--function-name` | Nombre de la función | Se usa en los comandos siguientes (`add-permission`, `get-function-configuration`). |
| `--runtime python3.12` | Versión de Python | PyArrow del zip está compilado para Python 3.12. |
| `--architectures x86_64` | Tipo de procesador | PyArrow del zip está compilado para x86_64. |
| `--role` | Rol IAM (`LabRole` en Academy) | Permite leer el bucket S3 y escribir logs en CloudWatch. |
| `--handler handler.lambda_handler` | Archivo `handler.py`, función `lambda_handler` | Indica a AWS qué función ejecutar en cada petición. |
| `--zip-file fileb://lambda_deployment.zip` | El código empaquetado | Contiene `handler.py` y PyArrow. |
| `--timeout 30` | Máximo 30 segundos por ejecución | La primera llamada lee todos los Parquet de S3. |
| `--memory-size 512` | 512 MB de RAM | Los planetas se mantienen en memoria. |
| `--environment file://lambda-env.json` | Carga las variables del paso 2 | `S3_BUCKET` y `S3_PREFIX`. |
| `--region us-east-1` | Región de AWS | Debe ser la misma en todos los comandos. |

> Los comandos están en varias líneas con `\` (Bash). En PowerShell se usa el acento grave `` ` `` al final de cada línea en lugar de `\`.

`ARN_DEL_ROL_IAM` es el ARN de un rol que permita a Lambda leer el bucket S3 y escribir en CloudWatch (en Academy, `LabRole`). Verificar la función (estado esperado: `Active`):

```bash
aws lambda get-function-configuration --function-name ExoplanetsQueryFunction --region us-east-1
```

### 4. Creación de API Gateway

API Gateway es la puerta de entrada pública de la aplicación: expone una URL (`https://<API_ID>.execute-api.us-east-1.amazonaws.com`) y reenvía cada petición a la Lambda. No contiene lógica, solo enruta: recibe la petición, la envía a la Lambda y devuelve su respuesta JSON.

Crear la API HTTP y guardar el `ApiId` como `API_ID`:

```bash
aws apigatewayv2 create-api --name ExoplanetsHttpApi --protocol-type HTTP --region us-east-1
```

Crear la integración con Lambda y guardar el `IntegrationId` como `INTEGRATION_ID`:

```bash
aws apigatewayv2 create-integration \
  --api-id API_ID \
  --integration-type AWS_PROXY \
  --integration-uri ARN_DE_LAMBDA \
  --payload-format-version 2.0 \
  --region us-east-1
```

`AWS_PROXY` pasa la petición tal cual a la Lambda y devuelve su respuesta; `2.0` es el formato de evento que lee `handler.py`.

Crear las rutas:

```bash
aws apigatewayv2 create-route \
  --api-id API_ID \
  --route-key "GET /planets" \
  --target "integrations/INTEGRATION_ID" \
  --region us-east-1

aws apigatewayv2 create-route \
  --api-id API_ID \
  --route-key "GET /statistics/size" \
  --target "integrations/INTEGRATION_ID" \
  --region us-east-1
```

Cada ruta es una URL pública que apunta a la integración (la Lambda).

Permitir que API Gateway invoque la Lambda:

```bash
aws lambda add-permission \
  --function-name ExoplanetsQueryFunction \
  --statement-id AllowApiGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "ARN_DE_API/*/GET/*" \
  --region us-east-1
```

Sin este permiso, nadie puede invocar la Lambda y la API responde error 500.

Crear el stage con despliegue automático:

```bash
aws apigatewayv2 create-stage \
  --api-id API_ID \
  --stage-name '$default' \
  --auto-deploy \
  --region us-east-1
```

El stage publica la API; con `--auto-deploy` cada cambio se publica automáticamente.

Los identificadores (`API_ID`, `INTEGRATION_ID` y ARN) se obtienen de las respuestas de los comandos anteriores. Los comandos sirven en Bash o PowerShell adaptando los saltos de línea.

## Configuración de Streamlit para consumir la API

Una vez desplegadas Lambda y API Gateway, Streamlit consume los endpoints publicados.

### 1. Configurar la variable de entorno

`API_URL` es la dirección base de API Gateway. Debe definirse en la misma terminal desde la que se ejecutará Streamlit.

**PowerShell (Windows):**

```powershell
$env:API_URL = "https://8pdd9pi79k.execute-api.us-east-1.amazonaws.com"
```

**Bash (Linux/macOS):**

```bash
export API_URL="https://8pdd9pi79k.execute-api.us-east-1.amazonaws.com"
```

### 2. Instalar las dependencias

Desde la carpeta `streamlit_api`, con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

### 3. Ejecutar Streamlit

```bash
streamlit run app.py
```

Disponible en `http://localhost:8501`.

### 4. Funcionamiento de la aplicación

Streamlit consume la API mediante solicitudes HTTP con `requests`:

- Búsqueda de exoplanetas por nombre.
- Filtrado por categoría de tamaño.
- Selección de planetas similares a la Tierra.
- Resultados en una tabla.
- Gráfico de distribución de planetas por categoría de tamaño.
- Los 10 exoplanetas de mayor radio, como círculos proporcionales al radio, con su masa .
- Gráfico de barras horizontales con los 10 sistemas planetarios más cercanos a la Tierra.
