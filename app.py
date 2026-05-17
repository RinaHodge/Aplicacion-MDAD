import streamlit as st
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from streamlit_agraph import agraph, Node, Edge, Config
import pandas as pd
import altair as alt

from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


# -----------------------------------------
# CONFIGURACIÓN DE CONEXIÓN A NEO4J
# -----------------------------------------
URI = "neo4j://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"  
DATABASE = "recomendacionesuex"

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_query(query, params=None):
    driver = get_driver()
    with driver.session(database=DATABASE) as session:
        result = session.run(query, params)
        return pd.DataFrame([record.data() for record in result])

# -----------------------------------------
# FUNCIONES DE BASE DE DATOS
# -----------------------------------------
def obtener_areas():
    """Obtiene todas las áreas de conocimiento disponibles"""
    query = "MATCH (a:AreaConocimiento) RETURN a.nombre AS area ORDER BY area"
    df = run_query(query)
    if not df.empty:
        areas = [str(a).strip() for a in df['area'].tolist() if pd.notna(a)]
        etiquetas_no_deseadas = {"select all", "seleccionar todo"}
        return [a for a in areas if a.lower() not in etiquetas_no_deseadas]
    return []

def recomendar_titulaciones(areas_seleccionadas):
    """Busca las titulaciones asociadas a las áreas elegidas y calcula su estado de extinción"""
    query = """
    MATCH (a:AreaConocimiento)<-[:PERTENECE_A]-(asig:Asignatura)-[:SE_IMPARTE_EN]->(t:Titulacion)
    WHERE a.nombre IN $areas
    WITH t, asig,
         CASE
             WHEN t.ou_cursoExtincion IS NOT NULL AND toString(t.ou_cursoExtincion) <> "" 
             THEN toInteger(left(trim(toString(t.ou_cursoExtincion)), 4))
             ELSE NULL
         END AS anio_extincion,
         CASE
             WHEN t.ou_cursoInicioExtincion IS NOT NULL AND toString(t.ou_cursoInicioExtincion) <> "" 
             THEN toInteger(left(trim(toString(t.ou_cursoInicioExtincion)), 4))
             ELSE NULL
         END AS anio_inicio_extincion
    RETURN t.nombre AS Titulacion, 
            count(asig) AS `Numero Asignaturas`, 
            sum(coalesce(toFloat(replace(asig.creditos, ',', '.')), 0.0)) AS `Creditos Totales`,
            CASE
                WHEN anio_extincion IS NOT NULL AND anio_extincion <= date().year THEN "EXTINTA"
                WHEN anio_extincion IS NOT NULL OR anio_inicio_extincion IS NOT NULL THEN "EN PROCESO"
                ELSE "VIGENTE"
            END AS `Extincion`
        ORDER BY `Numero Asignaturas` DESC
        LIMIT 15
    """
    return run_query(query, {"areas": areas_seleccionadas})

def KMeans_clustering():
    """Realiza el algoritmo de KMeans para agrupar titulaciones similares según su carga lectiva en áreas de conocimiento"""
    query = """
    MATCH (a:AreaConocimiento)<-[:PERTENECE_A]-(asig:Asignatura)-[:SE_IMPARTE_EN]->(t:Titulacion)
    RETURN t.nombre AS Titulacion, a.nombre AS Area, count(asig) AS NumAsignaturas
    """
    df = run_query(query)
    
    if df.empty:
        st.warning("No se han encontrado datos para el clustering.")
        return None
    
    # Pasar a formato de matriz para KMeans
    pivot_df = df.pivot_table(index='Titulacion', columns='Area', values='NumAsignaturas', fill_value=0)
    X_norm = normalize(pivot_df.values)
    
    k = 5              # Número de clusters 
    kmeans = KMeans(n_clusters=k, random_state=23)
    pivot_df['Cluster'] = kmeans.fit_predict(X_norm)
    
    return pivot_df.reset_index(), k
# -----------------------------------------
# INTERFAZ DE LA APLICACIÓN
# -----------------------------------------
st.set_page_config(page_title="Recomendador UEx", page_icon="🎓", layout="wide")

st.title("🎓 Descubre tu Titulación Ideal en la UEx")
tab_principal, tab_clustering = st.tabs(["Recomendación de carreras", "Análisis de Clusters"])

with tab_principal:
    st.markdown("Selecciona las áreas de conocimiento que más te atraen y te recomendaremos qué estudiar en base a la carga lectiva real de cada carrera.")

    try:
        # Cargar las áreas de conocimiento disponibles
        lista_areas = obtener_areas()
        
        if not lista_areas:
            st.warning("No se han encontrado áreas. Asegúrate de haber cargado los CSV en Neo4j.")
        else:
            # Selector múltiple para el usuario
            st.subheader("Selecciona tus áreas de interés")
            areas_elegidas = st.multiselect(
                "Puedes elegir una o varias (Ej: Informática, Matemáticas, Derecho...):", 
                options=lista_areas,
                placeholder="Haz clic para seleccionar áreas..."
            )
            
        # Búsqueda y resultados
            if st.button("🔍 Buscar Titulaciones", type="primary", disabled=len(areas_elegidas)==0):
                with st.spinner('Analizando tus conexiones neuronales... 🧠'):
                    df_resultados = recomendar_titulaciones(areas_elegidas)
                    
                    if df_resultados.empty:
                        st.warning("Vaya... No hemos encontrado titulaciones con esa combinación. ¡Prueba con otras áreas!")
                    else:
                        
                        df_resultados = df_resultados.sort_values(
                            by="Numero Asignaturas",
                            ascending=False
                        )
                        
                        st.success("¡Análisis completado! Aquí tienes tu futuro académico:")
                        
                        # --- Destacar el mejor resultado encontrado ---
                        top_titulacion = df_resultados.iloc[0]
                        
                        st.markdown("### 🏆 Tu Match Perfecto")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"**{top_titulacion['Titulacion']}**")
                        with col2:
                            st.metric(label="Asignaturas Afines", value=int(top_titulacion['Numero Asignaturas']))
                        with col3:
                            st.metric(label="Créditos Totales", value=int(top_titulacion['Creditos Totales']))
                        
                        # Mostrar el grafo de conexiones                    
                        with st.expander("Ver el mapa de tus conexiones (Por qué te recomendamos esto)"):

                            nodos = []
                            aristas = []

                            # Nodo central: titulación recomendada
                            top_titulacion_nombre = str(top_titulacion["Titulacion"])
                            top_node_id = f"tit_{top_titulacion_nombre}"
                            nodos.append(Node(id=top_node_id,label=top_titulacion_nombre,color="#3b82f6",size=25,))

                            # Nodos de interés seleccionados y enlaces hacia la titulación top
                            for interes in sorted(set(areas_elegidas)):
                                interes_nombre = str(interes)
                                area_node_id = f"area_{interes_nombre}"
                                nodos.append(Node(id=area_node_id,label=interes_nombre,color="#f97316",size=15,))
                                aristas.append(Edge(source=area_node_id,target=top_node_id,label="Interés",))

                            config = Config(width=700, 
                                            height=400, 
                                            directed=True,
                                            nodeHighlightBehavior=True, 
                                            highlightColor="#F7A7A6",
                                            collapsible=False)

                            # Mostrar el grafo
                            agraph(nodes=nodos, edges=aristas, config=config)
                        
                        st.divider() # Línea separadora 

                        # --- Gráfico de barras con los resultados obtenidos ---
                        st.markdown("### 📊 Top Titulaciones Recomendadas")
                        chart = (
                            alt.Chart(df_resultados.head(10)) # Mostramos solo el Top 10 para no saturar
                            .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5) # Bordes redondeados
                            .encode(
                                x=alt.X("Titulacion:N", sort="-y", title="", axis=alt.Axis(labelAngle=-45, labelLimit=300)),
                                y=alt.Y("Numero Asignaturas:Q", title="Nº de Asignaturas"),
                                color=alt.Color("Numero Asignaturas:Q", scale=alt.Scale(scheme="tealblues"), legend=None),  # el color depende del número de asignaturas coincidentes
                                tooltip=["Titulacion", "Numero Asignaturas", "Creditos Totales", "Extincion"]
                            )
                            .properties(height=400)
                            .configure_view(strokeWidth=0)
                        )
                        st.altair_chart(chart, width="stretch")
                        
                        # --- Desplegable con todos los resultados encontrados ---
                        with st.expander("Ver tabla de datos detallada"):
                            st.dataframe(df_resultados, width="stretch", hide_index=True)
    except Neo4jError as e:
        st.error("❌ Error de consulta en Neo4j. Revisa tipos de datos o sintaxis de Cypher.")
        st.exception(e)
    except Exception as e:
        st.error("❌ Error inesperado en la aplicación.")
        st.exception(e)

with tab_clustering:
    st.header("Agrupación de carreras mediante KMeans (clusteing)")
    
    if st.button("📊 Generar Visualización K-Means", type="primary", key="btn_kmeans"):
        with st.spinner("Procesando datos y agrupando..."):
            
            resultado = KMeans_clustering()
            
            if resultado is not None:
                df_clusters, k = resultado
                
                #Identificar eje X y eje Y para el gráfico
                columnas_areas = [col for col in df_clusters.columns if col not in ['Titulacion', 'Cluster']]
                
                varianzas = df_clusters[columnas_areas].var().sort_values(ascending=False)

                atributo1 = varianzas.index[0]
                atributo2 = varianzas.index[1]
                
                # --- Visualización con matplotlib ---
                fig, ax = plt.subplots(figsize=(10, 7))
                
                scatter = ax.scatter(
                    df_clusters[atributo1], 
                    df_clusters[atributo2], 
                    c=df_clusters['Cluster'], 
                    cmap='viridis', 
                    s=50 
                )
                
                ax.set_title("K-Means con " + str(k) + " clústeres")
                ax.set_xlabel(f'Área: {atributo1}')
                ax.set_ylabel(f'Área: {atributo2}')
                
                st.pyplot(fig)
                
                st.success("Gráfico generado correctamente.")
                
                # Opcional: Mostrar los grupos en una tabla debajo
                with st.expander("Ver tabla de Titulaciones y sus Grupos"):
                    st.dataframe(df_clusters[['Titulacion', 'Cluster']].sort_values('Cluster'), hide_index=True)
            else:
                st.error("Hubo un problema al generar los datos del clustering.")

    