"""
Visualizador de Resultados de Optimización - Caso Base con VG/VR por Tramos
==========================================================================

Este script visualiza los resultados generados por optimizar_caso_base.py,
incluyendo análisis específicos de los volúmenes VG/VR calculados usando
las reglas por tramos implementadas.

Gráficos generados:
1. Evolución de volúmenes del lago con análisis VG/VR
2. Comparación de volúmenes por uso vs. límites calculados por tramos
3. Análisis de extracciones vs. volúmenes disponibles
4. Distribución de generación con restricciones VG
5. Análisis de déficits de riego vs. volúmenes VR disponibles
6. Rendimiento del sistema bajo las nuevas reglas por tramos
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from preprocesar_volumenes_uso import calcular_VG_VR_por_tramos
from cargar_datos_5temporadas import cargar_parametros_excel, cargar_nombres_centrales

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10

# Colores consistentes
COLORS = {
    'VG': '#e74c3c',      # Rojo para generación
    'VR': '#3498db',      # Azul para riego
    'total': '#2ecc71',   # Verde para total
    'limite': '#f39c12',  # Naranja para límites
    'deficit': '#e67e22', # Naranja oscuro para déficits
    'volumen': '#9b59b6', # Púrpura para volúmenes lago
    'meta': '#34495e'     # Gris para metas/umbrales
}

def verificar_carpeta_resultados(carpeta="resultados_caso_base"):
    """
    Verifica que existan los archivos de resultados necesarios
    """
    archivos_necesarios = [
        "volumenes_lago.csv",
        "volumenes_por_uso.csv", 
        "extracciones_por_uso.csv",
        "riego.csv",
        "energia_total.csv",
        "generacion.csv"
    ]
    
    archivos_encontrados = []
    archivos_faltantes = []
    
    for archivo in archivos_necesarios:
        ruta_archivo = os.path.join(carpeta, archivo)
        if os.path.exists(ruta_archivo):
            archivos_encontrados.append(archivo)
        else:
            archivos_faltantes.append(archivo)
    
    return archivos_encontrados, archivos_faltantes

def cargar_datos_resultados(carpeta="resultados_caso_base"):
    """
    Carga todos los archivos de resultados en un diccionario
    """
    print(f"\n📂 Cargando resultados desde: {carpeta}/")
    
    # Verificar archivos
    encontrados, faltantes = verificar_carpeta_resultados(carpeta)
    
    if faltantes:
        print(f"⚠️  Archivos faltantes: {faltantes}")
        print("   Ejecuta primero: python optimizar_caso_base.py")
        return None
    
    # Cargar datos
    datos = {}
    try:
        datos['volumenes_lago'] = pd.read_csv(f"{carpeta}/volumenes_lago.csv")
        datos['volumenes_uso'] = pd.read_csv(f"{carpeta}/volumenes_por_uso.csv")
        datos['extracciones_uso'] = pd.read_csv(f"{carpeta}/extracciones_por_uso.csv")
        datos['riego'] = pd.read_csv(f"{carpeta}/riego.csv")
        datos['energia'] = pd.read_csv(f"{carpeta}/energia_total.csv")
        datos['generacion'] = pd.read_csv(f"{carpeta}/generacion.csv")
        
        # Archivos opcionales
        if os.path.exists(f"{carpeta}/holguras_volumen.csv"):
            datos['holguras'] = pd.read_csv(f"{carpeta}/holguras_volumen.csv")
        else:
            datos['holguras'] = pd.DataFrame()  # Vacío si no hay violaciones
            
        if os.path.exists(f"{carpeta}/decision_alpha.csv"):
            datos['alpha'] = pd.read_csv(f"{carpeta}/decision_alpha.csv")
        else:
            datos['alpha'] = pd.DataFrame()
        
        print(f"✅ {len(encontrados)} archivos cargados exitosamente")
        
        # Mostrar estadísticas básicas
        print(f"   • Volúmenes lago: {len(datos['volumenes_lago'])} registros")
        print(f"   • Volúmenes por uso: {len(datos['volumenes_uso'])} registros") 
        print(f"   • Extracciones: {len(datos['extracciones_uso'])} registros")
        print(f"   • Datos de riego: {len(datos['riego'])} registros")
        print(f"   • Energía generada: {len(datos['energia'])} registros")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return None

def calcular_limites_VG_VR_optimizacion(datos_volumenes, parametros):
    """
    Calcula los límites VG/VR por tramos para cada semana usando los volúmenes 
    de la optimización y los parámetros del modelo
    """
    print("\n🔍 Calculando límites VG/VR por tramos para resultados de optimización...")
    
    # Obtener parámetros especiales (pueden venir de configuración)
    V_mixto = parametros.get('V_mixto', 0.0)
    T_TRANS = parametros.get('T_TRANS', 0) 
    VG_INI = parametros.get('VG_INI', 800.0)
    VR_INI = parametros.get('VR_INI', 1200.0)
    
    limites_calculados = []
    
    # Agrupar por temporada para cálculos secuenciales
    for t in sorted(datos_volumenes['Temporada'].unique()):
        datos_temp = datos_volumenes[datos_volumenes['Temporada'] == t].copy()
        datos_temp = datos_temp.sort_values('Semana')
        
        # Volumen inicial de la temporada (primera semana)
        V_rini_k = datos_temp['Volumen_hm3'].iloc[0]
        
        # Valores previos si existen
        if t > 1:
            # Buscar temporada anterior
            datos_prev = datos_volumenes[datos_volumenes['Temporada'] == t-1]
            if len(datos_prev) > 0:
                V_rini_k_minus1 = datos_prev['Volumen_hm3'].iloc[0]
                # Buscar VG previo (simplificado: usar límite calculado anterior)
                VG_prev = 800.0  # Simplificación, podría mejorarse
            else:
                V_rini_k_minus1 = None
                VG_prev = None
        else:
            V_rini_k_minus1 = None 
            VG_prev = None
        
        # Calcular límites para esta temporada
        VG_limite, VR_limite = calcular_VG_VR_por_tramos(
            V_rini_k=V_rini_k,
            V_rini_k_minus1=V_rini_k_minus1, 
            V_mixto=V_mixto,
            t=t,
            T_TRANS=T_TRANS,
            k=t,
            VG_prev=VG_prev,
            VG_INI=VG_INI if t == 1 else None,
            VR_INI=VR_INI if t == 1 else None
        )
        
        # Si devuelve None (caso k=1), usar valores iniciales
        if VG_limite is None:
            VG_limite = VG_INI if t == 1 else 0
        if VR_limite is None:
            VR_limite = VR_INI if t == 1 else 0
        
        # Agregar límites a todas las semanas de esta temporada
        for _, row in datos_temp.iterrows():
            limites_calculados.append({
                'Semana': row['Semana'],
                'Temporada': row['Temporada'],
                'Volumen_hm3': row['Volumen_hm3'],
                'V_rini_k': V_rini_k,
                'VG_limite': VG_limite,
                'VR_limite': VR_limite,
                'Total_limite': VG_limite + VR_limite
            })
    
    df_limites = pd.DataFrame(limites_calculados)
    print(f"   ✅ Límites calculados para {len(df_limites)} semanas")
    
    return df_limites

def crear_visualizador_optimizacion(carpeta_resultados="resultados_caso_base", 
                                   carpeta_graficos="graficos_optimizacion_VG_VR"):
    """
    Función principal para crear visualizaciones de los resultados de optimización
    """
    
    print("="*80)
    print("VISUALIZADOR DE RESULTADOS - OPTIMIZACIÓN CON VG/VR POR TRAMOS")
    print("="*80)
    
    # Crear carpeta de salida
    os.makedirs(carpeta_graficos, exist_ok=True)
    
    # 1. Cargar datos
    datos = cargar_datos_resultados(carpeta_resultados)
    if datos is None:
        return
    
    # 2. Cargar parámetros del modelo
    try:
        parametros = cargar_parametros_excel()
        nombres_centrales = cargar_nombres_centrales()
        print("✅ Parámetros del modelo cargados")
    except Exception as e:
        print(f"⚠️  Error cargando parámetros: {e}")
        parametros = {}
        nombres_centrales = {}
    
    # 3. Calcular límites VG/VR por tramos
    df_limites = calcular_limites_VG_VR_optimizacion(datos['volumenes_lago'], parametros)
    
    # =============================================================
    # GRÁFICO 1: VOLÚMENES DEL LAGO CON LÍMITES VG/VR
    # =============================================================
    
    print("\n📈 Generando Gráfico 1: Volúmenes del lago con análisis VG/VR...")
    
    fig, axes = plt.subplots(3, 1, figsize=(18, 15))
    
    # Preparar datos con offset para mostrar temporadas juntas
    datos_plot = datos['volumenes_lago'].copy()
    datos_plot['Semana_Global'] = (datos_plot['Temporada'] - 1) * 48 + datos_plot['Semana']
    
    limites_plot = df_limites.copy()
    limites_plot['Semana_Global'] = (limites_plot['Temporada'] - 1) * 48 + limites_plot['Semana']
    
    # Gráfico 1.1: Volumen del lago
    ax = axes[0]
    ax.plot(datos_plot['Semana_Global'], datos_plot['Volumen_hm3'], 
            color=COLORS['volumen'], linewidth=2.5, label='Volumen del Lago')
    
    # Líneas de referencia
    V_min = parametros.get('V_min', 1400)
    V_MAX = parametros.get('V_MAX', 5600)
    ax.axhline(y=V_min, color='red', linestyle='--', alpha=0.7, label=f'V_min = {V_min} hm³')
    ax.axhline(y=V_MAX, color='orange', linestyle='--', alpha=0.7, label=f'V_MAX = {V_MAX} hm³')
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Evolución del Volumen del Lago Laja - Optimización', fontweight='bold', fontsize=14)
    ax.set_ylabel('Volumen (hm³)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Gráfico 1.2: Límites VG y VR calculados por tramos
    ax = axes[1]
    ax.plot(limites_plot['Semana_Global'], limites_plot['VG_limite'], 
            color=COLORS['VG'], linewidth=2.5, label='Límite VG (Generación)', marker='o', markersize=3)
    ax.plot(limites_plot['Semana_Global'], limites_plot['VR_limite'], 
            color=COLORS['VR'], linewidth=2.5, label='Límite VR (Riego)', marker='s', markersize=3)
    ax.plot(limites_plot['Semana_Global'], limites_plot['Total_limite'], 
            color=COLORS['total'], linewidth=2, label='Total Extraíble (VG+VR)', linestyle='--')
    
    # Límite VG = 1200
    ax.axhline(y=1200, color='red', linestyle='-', alpha=0.8, label='Límite VG = 1200 hm³')
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Límites VG/VR Calculados por Tramos', fontweight='bold', fontsize=14)
    ax.set_ylabel('Volumen Límite (hm³)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Gráfico 1.3: Volúmenes por uso utilizados en optimización
    ax = axes[2]
    
    # Procesar datos de volúmenes por uso
    vol_uso = datos['volumenes_uso'].copy()
    vol_uso['Semana_Global'] = (vol_uso['Temporada'] - 1) * 48 + vol_uso['Semana']
    
    # Separar por uso
    vol_generacion = vol_uso[vol_uso['Uso'] == 2]  # u=2 es generación
    vol_riego = vol_uso[vol_uso['Uso'] == 1]       # u=1 es riego
    
    if len(vol_generacion) > 0:
        ax.plot(vol_generacion['Semana_Global'], vol_generacion['Volumen_hm3'], 
                color=COLORS['VG'], linewidth=2, label='Volumen Usado - Generación', alpha=0.8)
    
    if len(vol_riego) > 0:
        ax.plot(vol_riego['Semana_Global'], vol_riego['Volumen_hm3'], 
                color=COLORS['VR'], linewidth=2, label='Volumen Usado - Riego', alpha=0.8)
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Volúmenes por Uso Utilizados en la Optimización', fontweight='bold', fontsize=14)
    ax.set_xlabel('Semana Global')
    ax.set_ylabel('Volumen Utilizado (hm³)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Configurar ejes x para todos los subplots
    for ax in axes:
        ax.set_xticks([24, 72, 120, 168, 216])
        ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'], fontweight='bold')
        ax.set_xlim(0, 240)
    
    plt.tight_layout()
    plt.savefig(f'{carpeta_graficos}/1_volumenes_lago_VG_VR.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Guardado: {carpeta_graficos}/1_volumenes_lago_VG_VR.png")
    plt.close()
    
    # =============================================================
    # GRÁFICO 2: ANÁLISIS DE EXTRACCIONES VS LÍMITES
    # =============================================================
    
    print("📈 Generando Gráfico 2: Análisis extracciones vs límites...")
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()
    
    # Preparar datos de extracciones
    extracciones = datos['extracciones_uso'].copy()
    extracciones['Semana_Global'] = (extracciones['Temporada'] - 1) * 48 + extracciones['Semana']
    
    # Merge con límites
    merged_data = pd.merge(extracciones, limites_plot, on=['Semana', 'Temporada'], how='left')
    
    # Gráfico 2.1: Extracciones vs Límites VG
    ax = axes[0]
    ext_gen = merged_data[merged_data['Uso'] == 2]  # Generación
    if len(ext_gen) > 0:
        ax.scatter(ext_gen['VG_limite'], ext_gen['Caudal_m3s'], 
                  color=COLORS['VG'], alpha=0.6, s=30, label='Extracciones Generación')
        
        # Línea de referencia (y=x)
        max_val = max(ext_gen['VG_limite'].max(), ext_gen['Caudal_m3s'].max())
        ax.plot([0, max_val], [0, max_val], '--', color='gray', alpha=0.5, label='Límite = Extracción')
    
    ax.set_title('Extracciones vs Límites VG (Generación)', fontweight='bold')
    ax.set_xlabel('Límite VG (hm³)')
    ax.set_ylabel('Extracción Generación (m³/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Gráfico 2.2: Extracciones vs Límites VR  
    ax = axes[1]
    ext_riego = merged_data[merged_data['Uso'] == 1]  # Riego
    if len(ext_riego) > 0:
        ax.scatter(ext_riego['VR_limite'], ext_riego['Caudal_m3s'], 
                  color=COLORS['VR'], alpha=0.6, s=30, label='Extracciones Riego')
        
        # Línea de referencia
        max_val = max(ext_riego['VR_limite'].max(), ext_riego['Caudal_m3s'].max())
        ax.plot([0, max_val], [0, max_val], '--', color='gray', alpha=0.5, label='Límite = Extracción')
    
    ax.set_title('Extracciones vs Límites VR (Riego)', fontweight='bold')
    ax.set_xlabel('Límite VR (hm³)')
    ax.set_ylabel('Extracción Riego (m³/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Gráfico 2.3: Evolución temporal de extracciones
    ax = axes[2]
    if len(ext_gen) > 0:
        ax.plot(ext_gen['Semana_Global_x'], ext_gen['Caudal_m3s'], 
               color=COLORS['VG'], linewidth=2, label='Extracción Generación')
    if len(ext_riego) > 0:
        ax.plot(ext_riego['Semana_Global_x'], ext_riego['Caudal_m3s'], 
               color=COLORS['VR'], linewidth=2, label='Extracción Riego')
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Evolución Temporal de Extracciones', fontweight='bold')
    ax.set_xlabel('Semana Global')
    ax.set_ylabel('Extracción (m³/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xticks([24, 72, 120, 168, 216])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'])
    
    # Gráfico 2.4: Utilización de límites (%)
    ax = axes[3]
    
    # Calcular porcentaje de utilización
    if len(ext_gen) > 0 and len(ext_riego) > 0:
        # Simplificado: asumir conversión aproximada m³/s a hm³ por semana
        factor_conversion = 0.6048  # (7 días * 24 h * 3600 s) / 1e6
        
        ext_gen_conv = ext_gen['Caudal_m3s'] * factor_conversion
        ext_riego_conv = ext_riego['Caudal_m3s'] * factor_conversion
        
        util_gen = (ext_gen_conv / ext_gen['VG_limite'] * 100).fillna(0)
        util_riego = (ext_riego_conv / ext_riego['VR_limite'] * 100).fillna(0)
        
        ax.plot(ext_gen['Semana_Global_x'], util_gen, 
               color=COLORS['VG'], linewidth=2, label='Utilización VG (%)', marker='o', markersize=3)
        ax.plot(ext_riego['Semana_Global_x'], util_riego, 
               color=COLORS['VR'], linewidth=2, label='Utilización VR (%)', marker='s', markersize=3)
        
        ax.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='100% Utilización')
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Utilización de Límites VG/VR (%)', fontweight='bold')
    ax.set_xlabel('Semana Global')
    ax.set_ylabel('Utilización (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xticks([24, 72, 120, 168, 216])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'])
    
    plt.tight_layout()
    plt.savefig(f'{carpeta_graficos}/2_extracciones_vs_limites.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Guardado: {carpeta_graficos}/2_extracciones_vs_limites.png")
    plt.close()
    
    # =============================================================
    # GRÁFICO 3: ANÁLISIS DE RIEGO Y DÉFICITS
    # =============================================================
    
    print("📈 Generando Gráfico 3: Análisis de riego y déficits...")
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()
    
    # Preparar datos de riego
    riego = datos['riego'].copy()
    riego['Semana_Global'] = (riego['Temporada'] - 1) * 48 + riego['Semana']
    
    # Merge con límites VR
    riego_merged = pd.merge(riego, limites_plot[['Semana', 'Temporada', 'VR_limite']], 
                           on=['Semana', 'Temporada'], how='left')
    
    # Gráfico 3.1: Déficits por temporada
    ax = axes[0]
    deficit_por_temp = riego.groupby('Temporada')['Deficit_m3s'].sum()
    colores_temp = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
    
    bars = ax.bar(deficit_por_temp.index, deficit_por_temp.values, 
                  color=colores_temp[:len(deficit_por_temp)], alpha=0.8)
    ax.set_title('Déficit Total de Riego por Temporada', fontweight='bold')
    ax.set_xlabel('Temporada')
    ax.set_ylabel('Déficit Total (m³/s)')
    ax.grid(True, axis='y', alpha=0.3)
    
    # Añadir valores sobre las barras
    for bar, val in zip(bars, deficit_por_temp.values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + val*0.01, 
                   f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Gráfico 3.2: Evolución de déficits vs límites VR
    ax = axes[1]
    
    # Solo mostrar semanas con déficit > 0
    deficit_weeks = riego_merged[riego_merged['Deficit_m3s'] > 0.01]
    if len(deficit_weeks) > 0:
        scatter = ax.scatter(deficit_weeks['VR_limite'], deficit_weeks['Deficit_m3s'], 
                           c=deficit_weeks['Temporada'], cmap='viridis', 
                           s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
        plt.colorbar(scatter, ax=ax, label='Temporada')
        
        ax.set_title('Déficits vs Límites VR Disponibles', fontweight='bold')
        ax.set_xlabel('Límite VR (hm³)')
        ax.set_ylabel('Déficit (m³/s)')
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No hay déficits de riego\nen la optimización', 
               ha='center', va='center', transform=ax.transAxes, 
               fontsize=14, fontweight='bold', color='green')
        ax.set_title('Análisis de Déficits de Riego', fontweight='bold')
    
    # Gráfico 3.3: Provisión vs Demanda por canal (agregado)
    ax = axes[2]
    
    provision_canal = riego.groupby('Canal')['Provisto_m3s'].sum()
    demanda_canal = riego.groupby('Canal')['Demanda_m3s'].sum()
    
    x = np.arange(len(provision_canal))
    width = 0.35
    
    ax.bar(x - width/2, demanda_canal.values, width, label='Demanda', 
           color=COLORS['limite'], alpha=0.8)
    ax.bar(x + width/2, provision_canal.values, width, label='Provisión', 
           color=COLORS['VR'], alpha=0.8)
    
    ax.set_title('Demanda vs Provisión por Canal (Acumulado)', fontweight='bold')
    ax.set_xlabel('Canal')
    ax.set_ylabel('Caudal Acumulado (m³/s)')
    ax.set_xticks(x)
    ax.set_xticklabels([f'Canal {i}' for i in provision_canal.index])
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)
    
    # Gráfico 3.4: Evolución temporal demanda vs provisión (total)
    ax = axes[3]
    
    # Agrupar por semana global
    demanda_temporal = riego.groupby('Semana_Global')['Demanda_m3s'].sum()
    provision_temporal = riego.groupby('Semana_Global')['Provisto_m3s'].sum()
    
    ax.plot(demanda_temporal.index, demanda_temporal.values, 
           color=COLORS['limite'], linewidth=2, label='Demanda Total', linestyle='--')
    ax.plot(provision_temporal.index, provision_temporal.values, 
           color=COLORS['VR'], linewidth=2, label='Provisión Total')
    
    # Sombrear áreas con déficit
    deficit_temporal = demanda_temporal - provision_temporal
    deficit_areas = deficit_temporal > 0.01
    if deficit_areas.any():
        ax.fill_between(deficit_temporal.index, demanda_temporal.values, 
                       provision_temporal.values, where=deficit_areas,
                       alpha=0.3, color='red', label='Déficit')
    
    # Separadores de temporadas
    for t in range(1, 5):
        ax.axvline(x=t*48, color='gray', linestyle='-', alpha=0.3, linewidth=1)
    
    ax.set_title('Evolución Temporal: Demanda vs Provisión Total', fontweight='bold')
    ax.set_xlabel('Semana Global')
    ax.set_ylabel('Caudal (m³/s)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xticks([24, 72, 120, 168, 216])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'])
    
    plt.tight_layout()
    plt.savefig(f'{carpeta_graficos}/3_analisis_riego_deficits.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Guardado: {carpeta_graficos}/3_analisis_riego_deficits.png")
    plt.close()
    
    # =============================================================
    # GRÁFICO 4: ANÁLISIS DE GENERACIÓN ELÉCTRICA
    # =============================================================
    
    print("📈 Generando Gráfico 4: Análisis de generación eléctrica...")
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()
    
    # Preparar datos de energía
    energia = datos['energia'].copy()
    
    # Gráfico 4.1: Energía por temporada
    ax = axes[0]
    energia_temp = energia.groupby('Temporada')['Energia_GWh'].sum()
    
    bars = ax.bar(energia_temp.index, energia_temp.values, 
                  color=colores_temp[:len(energia_temp)], alpha=0.8)
    ax.set_title('Energía Generada por Temporada', fontweight='bold')
    ax.set_xlabel('Temporada')
    ax.set_ylabel('Energía (GWh)')
    ax.grid(True, axis='y', alpha=0.3)
    
    # Añadir valores sobre las barras
    for bar, val in zip(bars, energia_temp.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + val*0.01, 
               f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Gráfico 4.2: Top 8 centrales por energía total
    ax = axes[1]
    energia_central = energia.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False).head(8)
    
    # Usar nombres de centrales si están disponibles
    nombres_display = []
    for central in energia_central.index:
        if central in nombres_centrales:
            nombres_display.append(f"{nombres_centrales[central][:15]}")
        else:
            nombres_display.append(f"Central {central}")
    
    bars = ax.barh(range(len(energia_central)), energia_central.values, color=COLORS['VG'], alpha=0.8)
    ax.set_title('Top 8 Centrales por Energía Generada', fontweight='bold')
    ax.set_xlabel('Energía Total (GWh)')
    ax.set_yticks(range(len(energia_central)))
    ax.set_yticklabels(nombres_display)
    ax.grid(True, axis='x', alpha=0.3)
    
    # Añadir valores al final de las barras
    for i, (bar, val) in enumerate(zip(bars, energia_central.values)):
        ax.text(bar.get_width() + val*0.01, bar.get_y() + bar.get_height()/2, 
               f'{val:.1f}', ha='left', va='center', fontweight='bold')
    
    # Gráfico 4.3: Distribución de generación por central y temporada
    ax = axes[2]
    
    # Crear matriz para heatmap
    centrales_top = energia_central.head(6).index  # Top 6 para visualización
    matriz_energia = []
    temporadas = sorted(energia['Temporada'].unique())
    
    for central in centrales_top:
        fila = []
        for temp in temporadas:
            val = energia[(energia['Central'] == central) & 
                         (energia['Temporada'] == temp)]['Energia_GWh'].sum()
            fila.append(val)
        matriz_energia.append(fila)
    
    im = ax.imshow(matriz_energia, cmap='YlOrRd', aspect='auto')
    
    # Configurar etiquetas
    ax.set_xticks(range(len(temporadas)))
    ax.set_xticklabels([f'T{t}' for t in temporadas])
    ax.set_yticks(range(len(centrales_top)))
    ax.set_yticklabels([nombres_centrales.get(c, f'C{c}')[:15] for c in centrales_top])
    
    # Añadir valores en las celdas
    for i in range(len(centrales_top)):
        for j in range(len(temporadas)):
            val = matriz_energia[i][j]
            color = 'white' if val > np.max(matriz_energia) * 0.5 else 'black'
            ax.text(j, i, f'{val:.1f}', ha='center', va='center', 
                   color=color, fontweight='bold', fontsize=9)
    
    ax.set_title('Energía por Central y Temporada (Top 6)', fontweight='bold')
    ax.set_xlabel('Temporada')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Energía (GWh)')
    
    # Gráfico 4.4: Relación VG límite vs Energía generada por temporada
    ax = axes[3]
    
    # Calcular VG límite promedio por temporada
    vg_limite_temp = df_limites.groupby('Temporada')['VG_limite'].mean()
    
    # Hacer scatter plot
    scatter = ax.scatter(vg_limite_temp.values, energia_temp.values, 
                        c=vg_limite_temp.index, cmap='viridis', s=100, 
                        alpha=0.8, edgecolors='black', linewidth=2)
    
    # Añadir etiquetas de temporada
    for i, (vg, energia_val, temp) in enumerate(zip(vg_limite_temp.values, 
                                                   energia_temp.values, 
                                                   vg_limite_temp.index)):
        ax.annotate(f'T{temp}', (vg, energia_val), xytext=(5, 5), 
                   textcoords='offset points', fontweight='bold')
    
    ax.set_title('Límite VG vs Energía Generada por Temporada', fontweight='bold')
    ax.set_xlabel('Límite VG Promedio (hm³)')
    ax.set_ylabel('Energía Total (GWh)')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{carpeta_graficos}/4_analisis_generacion_electrica.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Guardado: {carpeta_graficos}/4_analisis_generacion_electrica.png")
    plt.close()
    
    # =============================================================
    # RESUMEN DE ESTADÍSTICAS
    # =============================================================
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE ESTADÍSTICAS")
    print("="*80)
    
    # Estadísticas generales
    total_energia = energia['Energia_GWh'].sum()
    total_deficit = riego['Deficit_m3s'].sum()
    num_violaciones = len(datos['holguras']) if len(datos['holguras']) > 0 else 0
    
    print(f"\n⚡ GENERACIÓN:")
    print(f"   • Energía total generada: {total_energia:,.2f} GWh")
    print(f"   • Energía promedio/temporada: {total_energia/5:,.2f} GWh")
    
    print(f"\n💧 RIEGO:")
    print(f"   • Déficit total: {total_deficit:,.2f} m³/s acumulado")
    print(f"   • Semanas con déficit: {(riego['Deficit_m3s'] > 0.01).sum()}")
    
    print(f"\n📊 VOLÚMENES:")
    vol_inicial = datos['volumenes_lago']['Volumen_hm3'].iloc[0]
    vol_final = datos['volumenes_lago']['Volumen_hm3'].iloc[-1]
    vol_min = datos['volumenes_lago']['Volumen_hm3'].min()
    vol_max = datos['volumenes_lago']['Volumen_hm3'].max()
    
    print(f"   • Volumen inicial: {vol_inicial:,.2f} hm³")
    print(f"   • Volumen final: {vol_final:,.2f} hm³")
    print(f"   • Volumen mínimo alcanzado: {vol_min:,.2f} hm³")
    print(f"   • Volumen máximo alcanzado: {vol_max:,.2f} hm³")
    
    print(f"\n🚫 RESTRICCIONES:")
    print(f"   • Violaciones volumen mínimo: {num_violaciones}")
    
    # Estadísticas de límites VG/VR
    print(f"\n📏 LÍMITES VG/VR:")
    vg_promedio = df_limites['VG_limite'].mean()
    vr_promedio = df_limites['VR_limite'].mean()
    casos_limite_vg = (df_limites['VG_limite'] >= 1199).sum()
    
    print(f"   • VG límite promedio: {vg_promedio:,.2f} hm³")
    print(f"   • VR límite promedio: {vr_promedio:,.2f} hm³")
    print(f"   • Casos donde VG alcanza límite 1200: {casos_limite_vg}")
    
    print(f"\n📁 ARCHIVOS GENERADOS:")
    print(f"   • Carpeta: {carpeta_graficos}/")
    print("   • 4 gráficos principales de análisis")
    print("   • Análisis completo de optimización con VG/VR por tramos")
    
    print("\n" + "="*80)
    print("✅ VISUALIZACIÓN DE OPTIMIZACIÓN COMPLETADA")
    print("="*80)

def crear_datos_demo():
    """
    Crea datos de demostración para mostrar el funcionamiento del visualizador
    cuando no hay resultados reales de optimización disponibles
    """
    print("\n🔧 MODO DEMOSTRACIÓN - Generando datos sintéticos...")
    
    carpeta_demo = "resultados_demo"
    os.makedirs(carpeta_demo, exist_ok=True)
    
    # Parámetros de la demo
    temporadas = [1, 2, 3, 4, 5]
    semanas = list(range(1, 49))  # 48 semanas
    
    # 1. Volúmenes del lago (simulados)
    np.random.seed(42)  # Para reproducibilidad
    volumenes_lago = []
    
    for t in temporadas:
        vol_inicial = 4500 + np.random.normal(0, 500)  # Volumen inicial por temporada
        for w in semanas:
            # Variación semanal realista
            variacion = np.sin((w-1) * 2 * np.pi / 48) * 300 + np.random.normal(0, 100)
            volumen = max(1400, vol_inicial + variacion)  # No bajar de V_min
            volumenes_lago.append({
                'Semana': w,
                'Temporada': t,
                'Volumen_hm3': volumen
            })
    
    pd.DataFrame(volumenes_lago).to_csv(f"{carpeta_demo}/volumenes_lago.csv", index=False)
    
    # 2. Volúmenes por uso
    volumenes_uso = []
    for t in temporadas:
        for w in semanas:
            # VG y VR simulados basados en reglas por tramos
            V_base = 4000 + np.random.normal(0, 800)
            
            if V_base <= 1200:
                VG = 0.05 * V_base + 20
                VR = 570 + 10
            elif V_base <= 1370:
                VG = min(60 + 0.05 * (V_base - 1200), 1200)
                VR = 600 + 0.40 * (V_base - 1200)
            else:
                VG = min(68.5 + 0.40 * (V_base - 1370), 1200)
                VR = 668 + 0.40 * (V_base - 1370)
            
            volumenes_uso.append({'Semana': w, 'Temporada': t, 'Uso': 1, 'Volumen_hm3': VR})
            volumenes_uso.append({'Semana': w, 'Temporada': t, 'Uso': 2, 'Volumen_hm3': VG})
    
    pd.DataFrame(volumenes_uso).to_csv(f"{carpeta_demo}/volumenes_por_uso.csv", index=False)
    
    # 3. Extracciones por uso
    extracciones = []
    for t in temporadas:
        for w in semanas:
            # Extracciones como fracción de los volúmenes disponibles
            factor_uso = 0.3 + np.random.uniform(0, 0.4)  # 30-70% de uso
            
            VG_disp = volumenes_uso[(t-1)*48*2 + (w-1)*2 + 1]['Volumen_hm3']  # Aproximado
            VR_disp = volumenes_uso[(t-1)*48*2 + (w-1)*2]['Volumen_hm3']
            
            ext_gen = VG_disp * factor_uso * 0.1  # Conversión a m³/s aproximada
            ext_riego = VR_disp * factor_uso * 0.08
            
            extracciones.append({'Semana': w, 'Temporada': t, 'Uso': 1, 'Caudal_m3s': ext_riego})
            extracciones.append({'Semana': w, 'Temporada': t, 'Uso': 2, 'Caudal_m3s': ext_gen})
    
    pd.DataFrame(extracciones).to_csv(f"{carpeta_demo}/extracciones_por_uso.csv", index=False)
    
    # 4. Datos de riego
    riego = []
    canales = [1, 2, 3, 4]
    demandantes = [1, 2, 3]
    
    for t in temporadas:
        for w in semanas:
            for j in canales:
                for d in demandantes:
                    # Saltar combinaciones no válidas
                    if (j == 3 and d in [1, 2]) or (j == 4 and d in [2, 3]):
                        continue
                        
                    demanda = 5 + np.random.uniform(0, 10)  # 5-15 m³/s
                    provisto = min(demanda, demanda * (0.8 + np.random.uniform(0, 0.2)))
                    deficit = max(0, demanda - provisto)
                    
                    riego.append({
                        'Semana': w, 'Temporada': t, 'Canal': j, 'Demanda': d,
                        'Demanda_m3s': demanda, 'Provisto_m3s': provisto, 
                        'Deficit_m3s': deficit, 'Incumplimiento': 1 if deficit > 0.1 else 0
                    })
    
    pd.DataFrame(riego).to_csv(f"{carpeta_demo}/riego.csv", index=False)
    
    # 5. Energía generada
    energia = []
    centrales = list(range(1, 17))  # 16 centrales
    
    for t in temporadas:
        for i in centrales:
            # Energía basada en rendimiento simulado
            if i <= 10:  # Primeras 10 centrales más activas
                energia_base = 20 + np.random.uniform(0, 50)
            else:
                energia_base = np.random.uniform(0, 15)
                
            energia.append({
                'Central': i,
                'Temporada': t,
                'Energia_GWh': energia_base
            })
    
    pd.DataFrame(energia).to_csv(f"{carpeta_demo}/energia_total.csv", index=False)
    
    # 6. Generación por central/semana (simplificado)
    generacion = []
    for t in temporadas:
        for w in semanas:
            for i in centrales[:8]:  # Solo primeras 8 centrales
                caudal = np.random.uniform(0, 100)
                generacion.append({
                    'Semana': w, 'Temporada': t, 'Central': i, 'Caudal_m3s': caudal
                })
    
    pd.DataFrame(generacion).to_csv(f"{carpeta_demo}/generacion.csv", index=False)
    
    print(f"✅ Datos de demostración creados en: {carpeta_demo}/")
    return carpeta_demo

def main():
    """Función principal"""
    carpeta_resultados = "resultados_caso_base"
    
    # Verificar si existen resultados reales
    encontrados, faltantes = verificar_carpeta_resultados(carpeta_resultados)
    
    if len(faltantes) > 3:  # Si faltan muchos archivos
        print("\n" + "="*80)
        print("⚠️  ARCHIVOS DE OPTIMIZACIÓN NO ENCONTRADOS")
        print("="*80)
        print(f"Archivos faltantes: {faltantes}")
        print("\n🔧 Ejecutando modo demostración con datos sintéticos...")
        
        carpeta_resultados = crear_datos_demo()
    
    # Ejecutar visualizador
    crear_visualizador_optimizacion(
        carpeta_resultados=carpeta_resultados,
        carpeta_graficos=f"graficos_optimizacion_{carpeta_resultados.split('_')[-1]}"
    )

if __name__ == "__main__":
    main()