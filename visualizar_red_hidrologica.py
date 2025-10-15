#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualización de Red Hidrológica del Sistema Laja
Genera visualizaciones de la red de centrales, canales y flujos de caudal
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation, PillowWriter
import os
from cargar_datos_5temporadas import cargar_nombres_centrales

# ============================================================
# CONFIGURACIÓN
# ============================================================

RESULTADOS_DIR = 'resultados'
OUTPUT_DIR = 'graficos/red'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cargar nombres de centrales
archivo_excel = 'Parametros_Finales.xlsx'
nombres_centrales = cargar_nombres_centrales(archivo_excel)

# Nombres de canales y puntos de riego
nombres_canales = {
    1: 'Riezaco',
    2: 'Rietucapel', 
    3: 'Riesaltos',
    4: 'Abanico'
}

# ============================================================
# DEFINIR TOPOLOGÍA DE LA RED
# ============================================================

def crear_topologia_red():
    """
    Define la estructura de la red hidrológica basada en las restricciones del modelo
    Retorna: grafo dirigido, posiciones de nodos, configuración de arcos
    """
    G = nx.DiGraph()
    
    # ============ NODOS ============
    # Lago Laja
    G.add_node('LAGO', tipo='lago', capacidad=None)
    
    # Centrales (16 centrales)
    centrales = [
        ('C1', 'ELTORO'),
        ('C2', 'ABANICO'),
        ('C3', 'ANTUCO'),
        ('C4', 'RIEZACO'),
        ('C5', 'CANECOL'),
        ('C6', 'CANRUCUE'),
        ('C7', 'CLAJRUCUE'),
        ('C8', 'RUCUE'),
        ('C9', 'QUILLECO'),
        ('C10', 'TUCAPEL'),
        ('C11', 'CANAL_LAJA'),
        ('C12', 'RIESALTOS'),
        ('C13', 'LAJA1'),
        ('C14', 'RIETUCAPEL'),
        ('C15', 'ELDIUTO'),
        ('C16', 'LAJA_FILTRACIONES')
    ]
    for node_id, nombre in centrales:
        G.add_node(node_id, tipo='central', nombre=nombre)
    
    # Puntos de afluencia
    afluentes = [
        ('A1', 'Afluente_ElToro'),
        ('A2', 'Afluente_Abanico'),
        ('A3', 'Afluente_Antuco'),
        ('A4', 'Afluente_Tucapel'),
        ('A5', 'Afluente_Canecol'),
        ('A6', 'Afluente_Laja_I')
    ]
    for node_id, nombre in afluentes:
        G.add_node(node_id, tipo='afluente', nombre=nombre)
    
    # Canales de riego (puntos de salida)
    canales = [
        ('J1', 'Riezaco'),
        ('J2', 'Rietucapel'),
        ('J3', 'Riesaltos'),
        ('J4', 'Abanico')
    ]
    for node_id, nombre in canales:
        G.add_node(node_id, tipo='canal', nombre=nombre)
    
    # Nodo sumidero final
    G.add_node('RIO', tipo='rio', nombre='Río_Laja')
    
    # ============ ARCOS (basados en restricciones del modelo) ============
    
    # Lago → Filtraciones + El Toro
    G.add_edge('LAGO', 'C16', tipo='filtracion', var='qf')
    G.add_edge('LAGO', 'C1', tipo='extraccion', var='qe1')
    
    # Filtraciones → Abanico
    G.add_edge('C16', 'C2', tipo='generacion', var='qg16')
    
    # Afluentes a centrales
    G.add_edge('A1', 'C1', tipo='afluente', var='QA1')
    G.add_edge('A2', 'C2', tipo='afluente', var='QA2')
    G.add_edge('A3', 'C3', tipo='afluente', var='QA3')
    G.add_edge('A4', 'C10', tipo='afluente', var='QA4')
    G.add_edge('A5', 'C5', tipo='afluente', var='QA5')
    G.add_edge('A6', 'C13', tipo='afluente', var='QA6')
    
    # El Toro → Antuco
    G.add_edge('C1', 'C3', tipo='generacion', var='qg1')
    
    # Abanico → Antuco + Canal Abanico
    G.add_edge('C2', 'C3', tipo='generacion', var='qg2')
    G.add_edge('C2', 'J4', tipo='vertimiento', var='qv2')
    
    # Antuco → Riezaco (con vertimiento)
    G.add_edge('C3', 'C4', tipo='mixto', var='qg3+qv3')
    G.add_edge('C3', 'C4', tipo='vertimiento', var='qv3')
    
    # Riezaco → Riezaco Canal + Clajrucue
    G.add_edge('C4', 'J1', tipo='canal', var='qp_j1')
    G.add_edge('C4', 'C7', tipo='vertimiento', var='qv4')
    
    # Canecol → Canrucue
    G.add_edge('C5', 'C6', tipo='afluente', var='QA5')
    G.add_edge('C5', 'C10', tipo='generacion', var='qg5')
    G.add_edge('C5', 'C10', tipo='vertimiento', var='qv6+qv7')
    
    # Canrucue → Rucue
    G.add_edge('C6', 'C8', tipo='generacion', var='qg6')
    
    # Clajrucue → Rucue
    G.add_edge('C7', 'C8', tipo='generacion', var='qg7')
    
    # Rucue → Quilleco
    G.add_edge('C8', 'C9', tipo='mixto', var='qg8+qv8')
    
    # Quilleco → Tucapel
    G.add_edge('C9', 'C10', tipo='mixto', var='qg9+qv9')
    
    # Tucapel → Canal Laja
    G.add_edge('C10', 'C11', tipo='mixto', var='qg10+qv10')
    
    # Canal Laja → El Diuto + Laja I
    G.add_edge('C11', 'C15', tipo='generacion', var='qg11')
    G.add_edge('C11', 'C13', tipo='vertimiento', var='qv11')
    G.add_edge('C11', 'J3', tipo='vertimiento', var='qv11_riesaltos')
    
    # El Diuto → Rietucapel
    G.add_edge('C15', 'J2', tipo='mixto', var='qg15+qv15')
    
    # Laja I → Río
    G.add_edge('C13', 'RIO', tipo='salida', var='qg13+qv13')
    
    # Canales → Río (salida final)
    G.add_edge('J1', 'RIO', tipo='riego', var='riego_j1')
    G.add_edge('J2', 'RIO', tipo='riego', var='riego_j2')
    G.add_edge('J3', 'RIO', tipo='riego', var='riego_j3')
    G.add_edge('J4', 'RIO', tipo='riego', var='riego_j4')
    
    # ============ POSICIONES (layout manual para mejor visualización) ============
    pos = {
        # Lago arriba a la izquierda
        'LAGO': (0, 10),
        
        # Afluentes (izquierda)
        'A1': (-2, 9),
        'A2': (-2, 7),
        'A3': (-2, 5),
        'A5': (3, 8),
        'A4': (5, 4),
        'A6': (7, 1),
        
        # Centrales (flujo de arriba hacia abajo, izquierda a derecha)
        'C16': (1, 9),    # Filtraciones
        'C1': (0, 8),     # El Toro
        'C2': (1, 7),     # Abanico
        'C3': (0, 6),     # Antuco
        'C4': (0, 5),     # Riezaco
        'C7': (2, 4),     # Clajrucue
        'C5': (4, 7),     # Canecol
        'C6': (4, 6),     # Canrucue
        'C8': (3, 5),     # Rucue
        'C9': (4, 4),     # Quilleco
        'C10': (5, 3),    # Tucapel
        'C11': (6, 2),    # Canal Laja
        'C15': (7, 2),    # El Diuto
        'C13': (8, 1),    # Laja I
        'C12': (6, 1),    # Riesaltos (solo punto de extracción)
        'C14': (7, 1),    # Rietucapel (solo punto de extracción)
        
        # Canales de riego (derecha)
        'J1': (1, 4),     # Riezaco
        'J2': (8, 2),     # Rietucapel
        'J3': (7, 1.5),   # Riesaltos
        'J4': (2, 7),     # Abanico
        
        # Río (abajo)
        'RIO': (9, 0)
    }
    
    return G, pos


# ============================================================
# CARGAR DATOS DE RESULTADOS
# ============================================================

def cargar_datos_flujos():
    """Carga los datos de caudales desde los CSV de resultados"""
    try:
        # Caudales de generación
        generacion = pd.read_csv(f'{RESULTADOS_DIR}/generacion.csv')
        
        # Vertimientos
        vertimientos = pd.read_csv(f'{RESULTADOS_DIR}/vertimientos.csv')
        
        # Riego (provisiones)
        riego = pd.read_csv(f'{RESULTADOS_DIR}/riego.csv')
        
        # Volúmenes
        volumenes = pd.read_csv(f'{RESULTADOS_DIR}/volumenes_lago.csv')
        
        return {
            'generacion': generacion,
            'vertimientos': vertimientos,
            'riego': riego,
            'volumenes': volumenes
        }
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontraron archivos de resultados en '{RESULTADOS_DIR}/'")
        print(f"   Ejecuta primero: python3 optimizar_laja_5temporadas.py")
        return None


def obtener_flujos_semana(datos, semana, temporada):
    """
    Extrae los caudales de todos los arcos para una semana específica
    Retorna: diccionario con flujos por tipo de arco
    """
    gen = datos['generacion']
    vert = datos['vertimientos']
    riego_data = datos['riego']
    vol = datos['volumenes']
    
    # Filtrar por semana y temporada
    gen_st = gen[(gen['Semana'] == semana) & (gen['Temporada'] == temporada)]
    vert_st = vert[(vert['Semana'] == semana) & (vert['Temporada'] == temporada)]
    riego_st = riego_data[(riego_data['Semana'] == semana) & (riego_data['Temporada'] == temporada)]
    vol_st = vol[(vol['Semana'] == semana) & (vol['Temporada'] == temporada)]
    
    flujos = {}
    
    # Generación por central (qg)
    for _, row in gen_st.iterrows():
        central = int(row['Central'])
        flujos[f'qg{central}'] = row['Caudal_m3s']
    
    # Vertimientos (qv)
    for _, row in vert_st.iterrows():
        central = int(row['Central'])
        flujos[f'qv{central}'] = row['Caudal_m3s']
    
    # Riego (qp)
    for _, row in riego_st.iterrows():
        canal = int(row['Canal'])
        demanda = int(row['Demanda'])
        if demanda == 3:  # Solo nos interesa total por canal
            flujos[f'qp_j{canal}'] = row['Provision_m3s']
    
    # Volumen del lago
    if len(vol_st) > 0:
        flujos['V_lago'] = vol_st.iloc[0]['Volumen_hm3']
    
    return flujos


# ============================================================
# VISUALIZACIÓN
# ============================================================

def visualizar_red_semana(G, pos, flujos, semana, temporada, guardar=True):
    """
    Genera una visualización de la red para una semana específica
    """
    fig, ax = plt.subplots(figsize=(20, 14))
    
    # Configurar colores por tipo de nodo
    colores_nodos = {
        'lago': '#3498db',
        'central': '#e74c3c',
        'afluente': '#2ecc71',
        'canal': '#f39c12',
        'rio': '#95a5a6'
    }
    
    node_colors = [colores_nodos.get(G.nodes[n].get('tipo', 'central'), '#95a5a6') 
                   for n in G.nodes()]
    
    # Tamaños de nodos
    node_sizes = []
    for n in G.nodes():
        tipo = G.nodes[n].get('tipo', 'central')
        if tipo == 'lago':
            node_sizes.append(3000)
        elif tipo == 'central':
            node_sizes.append(2000)
        elif tipo == 'rio':
            node_sizes.append(2500)
        else:
            node_sizes.append(1500)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                          node_size=node_sizes, alpha=0.9, ax=ax)
    
    # Dibujar arcos con grosor proporcional al caudal
    edge_widths = []
    edge_colors = []
    
    for u, v, data in G.edges(data=True):
        var_name = data.get('var', '')
        # Intentar obtener el flujo (simplificado)
        caudal = flujos.get(var_name, 0)
        
        # Normalizar grosor (0.5 - 5.0)
        if caudal > 0:
            width = min(0.5 + (caudal / 50) * 4.5, 5.0)
        else:
            width = 0.3
        
        edge_widths.append(width)
        
        # Color según tipo
        tipo_arco = data.get('tipo', 'generacion')
        if tipo_arco == 'generacion':
            edge_colors.append('#e74c3c')
        elif tipo_arco == 'vertimiento':
            edge_colors.append('#3498db')
        elif tipo_arco == 'afluente':
            edge_colors.append('#2ecc71')
        elif tipo_arco == 'canal':
            edge_colors.append('#f39c12')
        else:
            edge_colors.append('#95a5a6')
    
    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors,
                          alpha=0.6, arrows=True, arrowsize=15, ax=ax,
                          connectionstyle='arc3,rad=0.1')
    
    # Etiquetas de nodos
    labels = {}
    for n in G.nodes():
        nombre = G.nodes[n].get('nombre', n)
        if n.startswith('C') and n != 'C16':
            # Centrales: usar nombre del Excel
            num_central = int(n[1:])
            labels[n] = nombres_centrales.get(num_central, nombre)
        else:
            labels[n] = nombre.replace('_', '\n')
    
    nx.draw_networkx_labels(G, pos, labels, font_size=8, 
                           font_weight='bold', ax=ax)
    
    # Título
    v_lago = flujos.get('V_lago', 0)
    ax.set_title(f'Red Hidrológica Sistema Laja\n'
                f'Temporada {temporada}, Semana {semana} | '
                f'Volumen Lago: {v_lago:,.0f} hm³',
                fontsize=16, fontweight='bold', pad=20)
    
    ax.axis('off')
    plt.tight_layout()
    
    if guardar:
        filename = f'{OUTPUT_DIR}/red_t{temporada}_s{semana:02d}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"  ✓ Guardado: {filename}")
        plt.close()
    else:
        plt.show()


# ============================================================
# GENERAR VISUALIZACIONES
# ============================================================

def generar_pngs_por_temporada(temporada=1):
    """Genera PNGs para todas las semanas de una temporada"""
    print(f"\n📊 Generando visualizaciones de red para temporada {temporada}...")
    
    # Cargar datos
    datos = cargar_datos_flujos()
    if datos is None:
        return
    
    # Crear topología
    G, pos = crear_topologia_red()
    
    # Generar un PNG por semana
    for semana in range(1, 49):
        flujos = obtener_flujos_semana(datos, semana, temporada)
        visualizar_red_semana(G, pos, flujos, semana, temporada, guardar=True)
    
    print(f"\n✅ Completado: 48 imágenes generadas en '{OUTPUT_DIR}/'")
    print(f"\nPuedes crear un GIF con:")
    print(f"  convert -delay 20 -loop 0 {OUTPUT_DIR}/red_t{temporada}_*.png {OUTPUT_DIR}/red_t{temporada}_animacion.gif")


def generar_muestra():
    """Genera visualizaciones de muestra para 4 semanas clave"""
    print("\n📊 Generando visualizaciones de muestra...")
    
    datos = cargar_datos_flujos()
    if datos is None:
        return
    
    G, pos = crear_topologia_red()
    
    semanas_muestra = [1, 12, 24, 36]
    temporada = 1
    
    for semana in semanas_muestra:
        flujos = obtener_flujos_semana(datos, semana, temporada)
        visualizar_red_semana(G, pos, flujos, semana, temporada, guardar=True)
    
    print(f"\n✅ Muestra generada: {len(semanas_muestra)} imágenes en '{OUTPUT_DIR}/'")


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("VISUALIZACIÓN DE RED HIDROLÓGICA - SISTEMA LAJA")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        opcion = sys.argv[1]
        
        if opcion == 'muestra':
            generar_muestra()
        elif opcion == 'temporada':
            temp = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            generar_pngs_por_temporada(temp)
        else:
            print("Opciones: muestra | temporada [1-5]")
    else:
        # Por defecto: generar muestra
        generar_muestra()
