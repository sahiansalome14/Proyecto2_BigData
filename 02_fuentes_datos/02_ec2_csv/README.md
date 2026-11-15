# 02. Fuente de datos: Archivos CSV en Amazon EC2

## 1. Descripción del caso de estudio

Esta segunda fuente de datos simula un entorno de almacenamiento basado en archivos dentro de una infraestructura empresarial o servidor local (*on-premises*), materializado en la nube mediante una instancia **Amazon EC2**.

En este servidor se almacena el **catálogo de exoplanetas confirmados** en formato CSV, obtenido desde el [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/). Este catálogo contiene la identificación única de cada planeta, la vinculación con su estrella anfitriona y los metadatos de descubrimiento (método, año y observatorio/telescopio).

Posteriormente, en la fase de ingesta (Punto 3), estos archivos serán transferidos automáticamente desde la instancia EC2 hacia la zona *Raw* del Data Lake en Amazon S3.

---

## 2. Arquitectura implementada

```text
       NASA Exoplanet Archive (TAP API)
                      |
                      | HTTP GET / CSV
                      v
             +------------------+
             |    Amazon EC2    |
             | Amazon Linux 2023|
             |                  |
             |  download_csv.sh |
             |        |         |
             |        v         |
             | ~/data/          |
             | exoplanetas_     |
             | catalogo.csv     |
             +------------------+
                      |
      (Punto 3: Ingesta hacia S3 Raw)
                      v
              Amazon S3 (Data Lake)
```

---

## 3. Configuración de la infraestructura en AWS

### 3.1. Región y entorno
- **Región:** US East (N. Virginia) `us-east-1`
- **Entorno:** AWS Academy Learner Lab / Cuenta AWS

### 3.2. Parámetros de la instancia Amazon EC2

Se creó una instancia virtual en el servicio **Amazon EC2** con las siguientes especificaciones:

| Parámetro | Valor configurado | Justificación |
|---|---|---|
| **Nombre** | `ec2-exoplanets-files` | Identificador estándar del recurso |
| **AMI** | Amazon Linux 2023 AMI (HVM, SSD) | Sistema operativo ligero y optimizado para AWS |
| **Arquitectura** | 64 bits (x86) | Compatibilidad estándar de herramientas y CLI |
| **Tipo de instancia** | `t2.micro` o `t3.micro` | Incluida en la capa gratuita / AWS Learner Lab (1 vCPU, 1 GiB RAM) |
| **Par de claves (Key pair)** | `vockey` o `exoplanets-key.pem` | Acceso seguro mediante SSH |
| **VPC** | VPC por defecto (o la misma de RDS) | Facilita la red interna y comunicación |
| **Subred** | Subred pública con IP pública asignada | Permite conexión SSH y salida a Internet |
| **Almacenamiento** | 8 GiB gp3 | Capacidad suficiente para el sistema y archivos CSV |

### 3.3. Configuración del Grupo de Seguridad (Security Group)

Se asignó un Security Group denominado `sg-ec2-files` con la siguiente regla de entrada:

| Tipo | Protocolo | Puerto | Origen | Descripción |
|---|---|---|---|---|
| **SSH** | TCP | 22 | `0.0.0.0/0` (o Mi IP) | Conexión remota por terminal SSH |

*Reglas de salida:* Por defecto permite todo el tráfico saliente (`0.0.0.0/0`), lo que permite descargar datos desde el API de NASA y conectarse con S3.

---

## 4. Despliegue y ejecución paso a paso

### 4.1. Conexión SSH a la instancia EC2

Desde la máquina local (o terminal de Windows PowerShell/WSL):

```bash
# Asignar permisos seguros a la clave privada (en Linux/Mac)
chmod 400 labsuser.pem  # o tu-llave.pem

# Conectarse a la instancia
ssh -i labsuser.pem ec2-user@<IP_PUBLICA_EC2>
```

### 4.2. Preparación del entorno en EC2

Una vez dentro de la instancia:

```bash
# Actualizar paquetes e instalar utilitarios necesarios
sudo dnf update -y
sudo dnf install -y curl wget

# Crear el directorio donde residirán los archivos de datos
mkdir -p ~/data
mkdir -p ~/scripts
```

### 4.3. Clonación o creación del script `download_csv.sh`

Se copia o crea el script `download_csv.sh` en la carpeta `~/scripts/`:

```bash
cat << 'EOF' > ~/scripts/download_csv.sh
#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-$HOME/data}"
OUTPUT_FILE="$DATA_DIR/exoplanetas_catalogo.csv"

echo "   Descarga de Catálogo de Exoplanetas Confirmados en EC2        "
echo "[1/4] Creando directorio de datos: $DATA_DIR"
mkdir -p "$DATA_DIR"

TAP_URL="https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
QUERY="SELECT pl_name, hostname, discoverymethod, disc_year, disc_facility FROM ps WHERE default_flag = 1 AND pl_name IS NOT NULL ORDER BY pl_name"

echo "[2/4] Consultando NASA Exoplanet Archive TAP..."
curl -sS -G "$TAP_URL" \
    --data-urlencode "query=$QUERY" \
    --data-urlencode "format=csv" \
    -o "$OUTPUT_FILE"

echo "[3/4] Validando archivo generado en: $OUTPUT_FILE"
if [ ! -s "$OUTPUT_FILE" ]; then
    echo "ERROR: El archivo descargado está vacío."
    exit 1
fi

TOTAL_LINES=$(wc -l < "$OUTPUT_FILE")
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo "   Descarga completada exitosamente                              "
echo "Ruta del archivo: $OUTPUT_FILE"
echo "Tamaño en disco:  $FILE_SIZE"
echo "Total de líneas:  $TOTAL_LINES (incluyendo cabecera)"
echo ""
echo "Primeras 5 líneas:"
head -n 5 "$OUTPUT_FILE"
EOF

# Dar permisos de ejecución
chmod +x ~/scripts/download_csv.sh
```

### 4.4. Ejecución del script

```bash
~/scripts/download_csv.sh
```

### 4.5. Verificación de los datos descargados

```bash
# Verificar ubicación y tamaño
ls -lh ~/data/exoplanetas_catalogo.csv

# Verificar conteo de registros
wc -l ~/data/exoplanetas_catalogo.csv

# Visualizar la cabecera y primeras filas
head -n 5 ~/data/exoplanetas_catalogo.csv
```

---

## 5. Diccionario de datos de la fuente CSV

El archivo generado `exoplanetas_catalogo.csv` contiene las siguientes columnas:

| Campo | Tipo de dato | Descripción | Rol en el proyecto |
|---|---|---|---|
| `pl_name` | String / Varchar | Nombre oficial del exoplaneta | **Clave de unión** con los parámetros de la API |
| `hostname` | String / Varchar | Nombre de la estrella anfitriona | **Clave foránea** con la tabla `stars` de RDS |
| `discoverymethod` | String | Método astronómico utilizado para descubrir el planeta (Transit, Radial Velocity, Microlensing, etc.) | Variable analítica |
| `disc_year` | Integer | Año de confirmación del descubrimiento | Variable analítica |
| `disc_facility` | String | Observatorio, telescopio o misión responsable (Kepler, TESS, etc.) | Metadato complementario |

---
