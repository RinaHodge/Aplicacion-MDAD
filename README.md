# 🎓 Recomendación de asignaturas y titulaciones de la UEx por áreas de conocimiento con Neo4J.

Aplicación web interactiva que ayuda a futuros estudiantes a descubrir qué carrera estudiar en la **Universidad de Extremadura (UEx)**, basándose en sus áreas de conocimiento de interés y la carga lectiva real de cada titulación.

---

## 📋 Descripción

Este sistema conecta con una base de datos de grafos **Neo4j** para analizar las relaciones entre asignaturas, áreas de conocimiento y titulaciones de la UEx. El usuario selecciona sus intereses académicos y la app devuelve las carreras con mayor afinidad, junto con análisis visuales y agrupaciones por similitud mediante **clustering K-Means**.

- **Recomendación personalizada**: Selecciona una o varias áreas de conocimiento y obtén las titulaciones con más asignaturas afines.
- **Visualización de conexiones**: Grafo interactivo que muestra por qué se recomienda cada carrera.
- **Top 10 gráfico**: Gráfico de barras con las titulaciones más relevantes para tus intereses.
- **Estado de extinción**: Indica si cada titulación está vigente, en proceso de extinción o extinta.
- **Clustering K-Means**: Agrupa automáticamente las titulaciones por similitud en su carga lectiva por áreas de conocimiento.

## 📊 Funcionalidades de la aplicación

### Pestaña 1 — Recomendación de titulaciones
1. Selecciona una o varias áreas de conocimiento en el desplegable.
2. Pulsa **Buscar Titulaciones**.
3. Consulta tu match perfecto, el grafo de conexiones y el ranking de titulaciones recomendadas.

### Pestaña 2 — Análisis de Clusters
1. Pulsa **Generar Visualización K-Means**.
2. La app agrupa las titulaciones en **5 clusters** según su distribución de asignaturas por área.
3. Visualiza el tamaño de cada cluster, su perfil de áreas predominantes y las titulaciones que contiene.

---

## 🛠️ Requisitos previos

- Python 3.8 o superior
- [Neo4j Desktop](https://neo4j.com/download/) con una instancia en ejecución
- Los archivos CSV de datos de la UEx cargados en Neo4j (ver sección de configuración)

---

## ⚙️ Configuración de Neo4j

### Parámetros de conexión

Edita las siguientes variables en `app.py` para que coincidan con tu instancia de Neo4j:

```python
URI      = "neo4j://localhost:7687"
USER     = "neo4j"
PASSWORD = "tu_contraseña"
DATABASE = "recomendacionesuex"
```

### Cargar los datos en Neo4j

1. Abre **Neo4j Desktop** y accede a la pestaña **Query** de tu base de datos.
2. Copia el contenido completo del archivo `consultas.txt` y ejecútalo.

Esto realizará, en orden:
- Creación de restricciones de unicidad para nodos `AreaConocimiento`, `Titulacion` y `Asignatura`.
- Creación de índices para acelerar las búsquedas.
- Carga de los CSV (`AreaConocimiento.csv`, `AcademicDegree.csv`, `AsignaturaTitulacion.csv`).
- Creación de las relaciones entre nodos (`PERTENECE_A`, `SE_IMPARTE_EN`).

> ⚠️ Los archivos CSV deben estar ubicados en el directorio `import` de tu instancia Neo4j (Local Instances - (nuestra instancia) - open folder - import).

### Modelo de datos (Grafo)

```
(AreaConocimiento) <-[:PERTENECE_A]- (Asignatura) -[:SE_IMPARTE_EN]-> (Titulacion)
```

| Nodo | Propiedades principales |
|---|---|
| `AreaConocimiento` | `uri`, `nombre`, `codigo` |
| `Titulacion` | `uri`, `nombre`, `codigo`, `ou_cursoExtincion`, `ou_cursoInicioExtincion` |
| `Asignatura` | `codigo`, `nombre`, `creditos` |

---

## 🚀 Instalación y puesta en marcha

### 1. Clonar el repositorio
```bash
git clone https://github.com/RinaHodge/Aplicacion-MDAD.git
cd Aplicacion-MDAD
```

## 2. Crear un entorno virtual (recomendado)
```bash
python -m venv venv
```

## 3. Activar el entorno
### En Windows:
```bash
venv\Scripts\Activate.ps1
```
### En Mac/Linux:
```bash
source venv/bin/activate
```

## 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```

## 5. Ejecutar la aplicación
```bash
streamlit run app.py
```
Para que la aplicación funcione correctamente, asegúrate de que tu instancia de Neo4j esté en ejecución y que los datos estén cargados.

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## 🧩 Estructura del proyecto

```
📁 proyecto/
├── app.py              # Aplicación principal (Streamlit)
├── requirements.txt    # Dependencias de Python
├── consultas.txt       # Script Cypher para cargar datos en Neo4j
└── README.md           # Este archivo
```

---

## 📦 Dependencias

| Librería | Uso |
|---|---|
| `streamlit` | Interfaz web interactiva |
| `neo4j` | Conexión y consultas a la base de datos de grafos |
| `pandas` | Manipulación y análisis de datos |
| `altair` | Gráficos y visualizaciones |
| `streamlit-agraph` | Grafo interactivo de conexiones |
| `scikit-learn` | Clustering K-Means y normalización |
| `matplotlib` | Soporte de visualización |

---




