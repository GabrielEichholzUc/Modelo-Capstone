#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulación Monte Carlo para Generación de Escenarios de Afluentes
==================================================================

Este script genera escenarios sintéticos de caudales afluentes basados en
datos históricos usando simulación Monte Carlo.

Método:
1. Lee datos históricos de caudales por afluente, semana y año
2. Para cada afluente y semana, calcula estadísticas (media, desviación estándar)
3. Genera N escenarios aleatorios usando distribuciones empíricas o paramétricas
4. Guarda los escenarios en el formato del modelo (5 temporadas × 48 semanas × 6 afluentes)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️  Warning: scipy no disponible. Test K-S se omitirá.")

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Obtener la ruta absoluta al directorio raíz del proyecto
import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

ARCHIVO_EXCEL = PROJECT_ROOT / 'Parametros_Nuevos.xlsx'
HOJA_HISTORICOS = 'Caudales historicos'
OUTPUT_DIR = SCRIPT_DIR / 'escenarios_montecarlo'
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_ESCENARIOS = 100  # Número de escenarios a generar
SEED = 42  # Semilla para reproducibilidad
METODO = 'bootstrap'  # Opciones: 'empirico', 'normal', 'lognormal', 'bootstrap'

np.random.seed(SEED)

print("=" * 70)
print("SIMULACIÓN MONTE CARLO - ESCENARIOS DE AFLUENTES")
print("=" * 70)

# ============================================================
# CARGAR DATOS HISTÓRICOS
# ============================================================

print("\n📂 Cargando datos históricos...")

df_historicos = pd.read_excel(ARCHIVO_EXCEL, sheet_name=HOJA_HISTORICOS)

# Adaptación: Este archivo tiene columnas 'CENTRAL', 'AÑO' y fechas
# Necesitamos crear columnas 'a' (afluente) y transformar a formato numérico

# Mapeo de nombres de centrales a índices de afluentes
centrales_a_afluente = {
    'ELTORO': 1,
    'ABANICO': 2,
    'ANTUCO': 3,
    'TUCAPEL': 4,
    'CANECOL': 5,
    'LAJA_I': 6
}

# Crear columna 'a' (índice de afluente)
if 'a' in df_historicos.columns:
    # Si 'a' ya existe, usarla directamente
    pass
elif 'CENTRAL' in df_historicos.columns:
    df_historicos['a'] = df_historicos['CENTRAL'].map(centrales_a_afluente)
elif 'Central' in df_historicos.columns:
    df_historicos['a'] = df_historicos['Central'].map(centrales_a_afluente)
else:
    print("⚠️  Columna 'a' o 'CENTRAL' no encontrada")

# Renombrar 'AÑO' a 'Año' si es necesario
if 'AÑO' in df_historicos.columns:
    df_historicos = df_historicos.rename(columns={'AÑO': 'Año'})

# Identificar columnas de semanas - pueden ser números o texto con fechas
# Primero buscar columnas con nombres de meses (formato 'abr 1', 'may 8', etc.)
import re
meses = ['abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar']
semanas_cols = [col for col in df_historicos.columns 
                if isinstance(col, str) and any(mes in col.lower() for mes in meses)]

if semanas_cols:
    # Renombrar estas columnas a números 1-48
    rename_dict = {col: idx + 1 for idx, col in enumerate(semanas_cols[:48])}
    df_historicos = df_historicos.rename(columns=rename_dict)
    semanas = list(range(1, min(49, len(semanas_cols) + 1)))
else:
    # Si no hay columnas con meses, buscar columnas numéricas
    semanas_cols = [col for col in df_historicos.columns if isinstance(col, int)]
    if semanas_cols:
        semanas = sorted(semanas_cols)
    else:
        semanas = []
        print("⚠️  No se encontraron columnas de semanas")

print(f"  ✓ Datos cargados: {len(df_historicos)} registros")
print(f"  Afluentes únicos: {sorted(df_historicos['a'].dropna().unique())}")
print(f"  Años históricos: {len(df_historicos['Año'].unique())} años")
print(f"  Semanas disponibles: {len(semanas)}")

# ============================================================
# TRANSFORMAR A FORMATO LARGO
# ============================================================

print("\n🔄 Transformando datos a formato largo...")

# Convertir a formato largo (tidy data)
# Mantener solo columnas relevantes
columnas_id = ['a', 'Año']
if 'CENTRAL' in df_historicos.columns:
    columnas_id.append('CENTRAL')
elif 'Central' in df_historicos.columns:
    columnas_id.append('Central')

# Filtrar solo las columnas que existen
columnas_id = [col for col in columnas_id if col in df_historicos.columns]

df_long = df_historicos.melt(
    id_vars=columnas_id,
    value_vars=semanas,
    var_name='Semana',
    value_name='Caudal_m3s'
)

# Filtrar filas donde 'a' no sea NaN (afluentes válidos)
df_long = df_long[df_long['a'].notna()].copy()
df_long['a'] = df_long['a'].astype(int)

print(f"  ✓ Datos transformados: {len(df_long)} observaciones")
print(f"  Ejemplo:\n{df_long.head(3)}")

# ============================================================
# DEFINIR ESTACIONES HIDROLÓGICAS
# ============================================================

def asignar_estacion(semana):
    """
    Asigna la estación hidrológica según la semana (12 semanas por estación)
    
    Año hidrológico en Chile comienza en abril:
    - Otoño (ABR-JUN): semanas 1-12
    - Invierno (JUL-SEP): semanas 13-24  
    - Primavera (OCT-DIC): semanas 25-36
    - Verano (ENE-MAR): semanas 37-48
    """
    if 1 <= semana <= 12:
        return 'Otoño'
    elif 13 <= semana <= 24:
        return 'Invierno'
    elif 25 <= semana <= 36:
        return 'Primavera'
    elif 37 <= semana <= 48:
        return 'Verano'
    else:
        return None

print("\n📊 Calculando estadísticas por afluente, estación y semana...")

# Agregar columna de estación
df_long['Estacion'] = df_long['Semana'].apply(asignar_estacion)

# Agrupar por afluente y semana (mantener stats por semana para backward compatibility)
stats_df = df_long.groupby(['a', 'Semana'])['Caudal_m3s'].agg([
    ('media', 'mean'),
    ('std', 'std'),
    ('min', 'min'),
    ('max', 'max'),
    ('q25', lambda x: x.quantile(0.25)),
    ('q50', lambda x: x.quantile(0.50)),
    ('q75', lambda x: x.quantile(0.75)),
    ('n_obs', 'count')
]).reset_index()
stats_df['Estacion'] = stats_df['Semana'].apply(asignar_estacion)

# Calcular estadísticas por estación (para bootstrap estacional)
stats_estacion_df = df_long.groupby(['a', 'Estacion'])['Caudal_m3s'].agg([
    ('media', 'mean'),
    ('std', 'std'),
    ('min', 'min'),
    ('max', 'max'),
    ('n_obs', 'count')
]).reset_index()

print(f"  ✓ Estadísticas calculadas para {len(stats_df)} combinaciones afluente-semana")
print(f"  ✓ Estadísticas estacionales calculadas para {len(stats_estacion_df)} combinaciones afluente-estación")
print(f"\n  Resumen por afluente:")
for a in sorted(stats_df['a'].unique()):
    stats_a = stats_df[stats_df['a'] == a]
    print(f"    Afluente {a}: media={stats_a['media'].mean():.2f} m³/s, "
          f"std={stats_a['std'].mean():.2f} m³/s")

# ============================================================
# FUNCIÓN PARA GENERAR ESCENARIOS
# ============================================================

def generar_escenario_montecarlo(df_historicos, stats_df, stats_estacion_df, metodo='empirico'):
    """
    Genera un escenario sintético de caudales para 6 temporadas
    
    Parámetros:
    -----------
    df_historicos : DataFrame con datos históricos en formato largo
    stats_df : DataFrame con estadísticas por afluente y semana
    stats_estacion_df : DataFrame con estadísticas por afluente y estación
    metodo : str, método de muestreo ('empirico', 'normal', 'lognormal', 'bootstrap')
    
    Retorna:
    --------
    dict : Diccionario con QA[a, w, t] para cada afluente, semana y temporada
    """
    escenario = {}
    
    for a in range(1, 7):  # 6 afluentes
        for w in range(1, 49):  # 48 semanas
            # Determinar estación de esta semana
            estacion = asignar_estacion(w)
            
            for t in range(1, 7):  # 6 temporadas
                
                # Obtener datos históricos para este afluente y semana
                datos_hist = df_long[(df_long['a'] == a) & (df_long['Semana'] == w)]['Caudal_m3s'].values
                
                # Para bootstrap estacional: obtener datos de toda la estación
                datos_hist_estacion = df_long[(df_long['a'] == a) & (df_long['Estacion'] == estacion)]['Caudal_m3s'].values
                
                if len(datos_hist) == 0:
                    # Si no hay datos, usar 0
                    escenario[(a, w, t)] = 0.0
                    continue
                
                # Generar valor según el método
                if metodo == 'empirico':
                    # Muestreo directo de datos históricos (bootstrap simple)
                    valor = np.random.choice(datos_hist)
                
                elif metodo == 'normal':
                    # Distribución normal con media y std empíricos
                    stats_row = stats_df[(stats_df['a'] == a) & (stats_df['Semana'] == w)]
                    if len(stats_row) > 0:
                        mu = stats_row['media'].values[0]
                        sigma = stats_row['std'].values[0]
                        if pd.isna(sigma) or sigma == 0:
                            sigma = mu * 0.1  # 10% de CV si no hay std
                        valor = np.random.normal(mu, sigma)
                        valor = max(0, valor)  # No negativos
                    else:
                        valor = 0.0
                
                elif metodo == 'lognormal':
                    # Distribución lognormal (apropiada para caudales)
                    datos_positivos = datos_hist[datos_hist > 0]
                    if len(datos_positivos) > 0:
                        mu_log = np.log(datos_positivos).mean()
                        sigma_log = np.log(datos_positivos).std()
                        if pd.isna(sigma_log) or sigma_log == 0:
                            sigma_log = 0.5
                        valor = np.random.lognormal(mu_log, sigma_log)
                    else:
                        valor = 0.0
                
                elif metodo == 'bootstrap':
                    # Bootstrap estacional con perturbación gaussiana
                    # Muestrear de toda la estación (no solo la semana específica)
                    if len(datos_hist_estacion) > 0:
                        valor_base = np.random.choice(datos_hist_estacion)
                    else:
                        valor_base = np.random.choice(datos_hist) if len(datos_hist) > 0 else 0.0
                    
                    # Usar estadísticas estacionales para la perturbación
                    stats_row = stats_estacion_df[(stats_estacion_df['a'] == a) & (stats_estacion_df['Estacion'] == estacion)]
                    if len(stats_row) > 0:
                        sigma = stats_row['std'].values[0] * 0.3  # 30% de la std estacional como ruido
                        if not pd.isna(sigma) and sigma > 0:
                            perturbacion = np.random.normal(0, sigma)
                            valor = valor_base + perturbacion
                            valor = max(0, valor)
                        else:
                            valor = valor_base
                    else:
                        valor = valor_base
                
                else:
                    raise ValueError(f"Método desconocido: {metodo}")
                
                escenario[(a, w, t)] = valor
    
    return escenario


# ============================================================
# GENERAR MÚLTIPLES ESCENARIOS
# ============================================================

print(f"\n🎲 Generando {NUM_ESCENARIOS} escenarios usando método '{METODO}'...")
if METODO == 'bootstrap':
    print(f"  → Usando bootstrap estacional (12 semanas por estación)")
    print(f"     • Otoño (ABR-JUN): semanas 1-12")
    print(f"     • Invierno (JUL-SEP): semanas 13-24")
    print(f"     • Primavera (OCT-DIC): semanas 25-36")
    print(f"     • Verano (ENE-MAR): semanas 37-48")

escenarios = []
for n in range(NUM_ESCENARIOS):
    if (n + 1) % 20 == 0:
        print(f"  → Generado escenario {n + 1}/{NUM_ESCENARIOS}...")
    escenario = generar_escenario_montecarlo(df_long, stats_df, stats_estacion_df, metodo=METODO)
    escenarios.append(escenario)

print(f"  ✓ {len(escenarios)} escenarios generados")

# ============================================================
# ORDENAR ESCENARIOS POR CAUDAL TOTAL (PESIMISTA → OPTIMISTA)
# ============================================================

print(f"\n📊 Ordenando escenarios por caudal total (pesimista → optimista)...")

# Calcular caudal total promedio para cada escenario
caudales_totales = []
for n, escenario in enumerate(escenarios):
    caudal_total = sum(escenario.values()) / len(escenario)  # Promedio de todos los valores
    caudales_totales.append((n, caudal_total, escenario))

# Ordenar de menor a mayor (pesimista a optimista)
caudales_totales.sort(key=lambda x: x[1])

# Reordenar escenarios
escenarios_ordenados = [item[2] for item in caudales_totales]
caudales_promedio = [item[1] for item in caudales_totales]

print(f"  ✓ Escenarios ordenados")
print(f"    Escenario #1 (más pesimista): {caudales_promedio[0]:.2f} m³/s promedio")
print(f"    Escenario #{len(escenarios)} (más optimista): {caudales_promedio[-1]:.2f} m³/s promedio")
print(f"    Escenario promedio (mediana): {caudales_promedio[len(escenarios)//2]:.2f} m³/s promedio")

# ============================================================
# GUARDAR ESCENARIOS EN FORMATO EXCEL
# ============================================================

print(f"\n💾 Guardando escenarios ordenados en formato Excel...")

# Seleccionar 10 escenarios representativos distribuidos uniformemente
# (percentiles: 5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
indices_seleccionados = [int(NUM_ESCENARIOS * p / 100) for p in [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]]

for idx, n in enumerate(indices_seleccionados):
    escenario = escenarios_ordenados[n]
    
    # Crear DataFrame para este escenario en el formato del modelo
    datos_escenario = []
    
    for t in range(1, 6):  # 5 temporadas
        for a in range(1, 7):  # 6 afluentes
            fila = {'Afluente': a, 'Temporada': t}
            for w in range(1, 49):  # 48 semanas
                fila[f'Semana_{w}'] = escenario[(a, w, t)]
            datos_escenario.append(fila)
    
    df_escenario = pd.DataFrame(datos_escenario)
    
    # Guardar con número de escenario original (del 1 al 100)
    output_file = f'{OUTPUT_DIR}/escenario_{n+1:03d}.xlsx'
    df_escenario.to_excel(output_file, index=False)
    if idx == 0:
        print(f"  ✓ Guardando 10 escenarios representativos...")
    if idx == 9:
        print(f"  ✓ Guardados escenarios: #{indices_seleccionados[0]+1}, #{indices_seleccionados[4]+1}, #{indices_seleccionados[-1]+1}, etc.")

# Guardar todos los escenarios en un solo archivo
print(f"\n💾 Guardando todos los escenarios en un archivo consolidado...")

with pd.ExcelWriter(f'{OUTPUT_DIR}/todos_escenarios.xlsx') as writer:
    for n, escenario in enumerate(escenarios_ordenados):  # TODOS los escenarios (100)
        datos_escenario = []
        for t in range(1, 7):
            for a in range(1, 7):
                fila = {'Afluente': a, 'Temporada': t}
                for w in range(1, 49):
                    fila[f'S{w}'] = escenario[(a, w, t)]
                datos_escenario.append(fila)
        df_escenario = pd.DataFrame(datos_escenario)
        df_escenario.to_excel(writer, sheet_name=f'Escenario_{n+1}', index=False)
        
        # Mostrar progreso cada 10 escenarios
        if (n + 1) % 10 == 0:
            print(f"  ✓ Guardados {n+1}/{NUM_ESCENARIOS} escenarios...")

print(f"  ✓ Guardado: {OUTPUT_DIR}/todos_escenarios.xlsx (todos los {NUM_ESCENARIOS} escenarios)")

# ============================================================
# ANÁLISIS Y VISUALIZACIÓN
# ============================================================

print(f"\n📊 Generando análisis estadístico...")

# Comparar distribuciones: históricos vs. simulados
# Ejemplo: Afluente 1, Semana 10, Temporada 1

a_ejemplo = 1
w_ejemplo = 10
t_ejemplo = 1

# Datos históricos
datos_hist_ejemplo = df_long[(df_long['a'] == a_ejemplo) & 
                              (df_long['Semana'] == w_ejemplo)]['Caudal_m3s'].values

# Datos simulados (usar escenarios ordenados)
datos_sim_ejemplo = [escenario[(a_ejemplo, w_ejemplo, t_ejemplo)] 
                     for escenario in escenarios_ordenados]

# Crear gráfico de comparación
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

afluentes_ejemplo = [1, 2, 3, 4, 5, 6]
semana_ej = 10

for idx, a in enumerate(afluentes_ejemplo):
    ax = axes[idx // 3, idx % 3]
    
    # Datos históricos para este afluente
    datos_hist = df_long[(df_long['a'] == a) & 
                          (df_long['Semana'] == semana_ej)]['Caudal_m3s'].values
    
    # Datos simulados para este afluente (ordenados)
    datos_sim = [escenario[(a, semana_ej, 1)] for escenario in escenarios_ordenados]
    
    # Histogramas
    ax.hist(datos_hist, bins=15, alpha=0.5, label='Históricos', 
            color='blue', density=True, edgecolor='black')
    ax.hist(datos_sim, bins=15, alpha=0.5, label=f'Simulados ({METODO})', 
            color='red', density=True, edgecolor='black')
    
    ax.set_xlabel('Caudal (m³/s)', fontweight='bold')
    ax.set_ylabel('Densidad', fontweight='bold')
    ax.set_title(f'Afluente {a} - Semana {semana_ej}', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.suptitle(f'Comparación Datos Históricos vs. Simulados Monte Carlo\n'
             f'Método: {METODO.upper()} | {NUM_ESCENARIOS} escenarios',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/comparacion_historicos_simulados.png', 
            dpi=300, bbox_inches='tight')
print(f"  ✓ Gráfico guardado: {OUTPUT_DIR}/comparacion_historicos_simulados.png")
plt.close()

# ============================================================
# ESTADÍSTICAS DE VALIDACIÓN
# ============================================================

print(f"\n📈 Validación estadística:")

for a in range(1, 7):
    # Calcular estadísticas para semana 10 como ejemplo
    w = 10
    datos_hist = df_long[(df_long['a'] == a) & (df_long['Semana'] == w)]['Caudal_m3s'].values
    datos_sim = [escenario[(a, w, 1)] for escenario in escenarios_ordenados]
    
    if len(datos_hist) > 0:
        print(f"\n  Afluente {a} (Semana {w}):")
        print(f"    Históricos: media={np.mean(datos_hist):.2f}, std={np.std(datos_hist):.2f}")
        print(f"    Simulados:  media={np.mean(datos_sim):.2f}, std={np.std(datos_sim):.2f}")
        
        # Test de Kolmogorov-Smirnov (si scipy disponible)
        if SCIPY_AVAILABLE:
            ks_stat, ks_pval = stats.ks_2samp(datos_hist, datos_sim)
            print(f"    Test K-S: estadístico={ks_stat:.4f}, p-valor={ks_pval:.4f}")

# ============================================================
# GUARDAR ESCENARIO PROMEDIO PARA USO EN MODELO
# ============================================================

print(f"\n💾 Creando escenario promedio para usar en el modelo...")

escenario_promedio = {}
for a in range(1, 7):
    for w in range(1, 49):
        for t in range(1, 7):
            valores = [escenario[(a, w, t)] for escenario in escenarios_ordenados]
            escenario_promedio[(a, w, t)] = np.mean(valores)

# Guardar en formato compatible con el modelo
datos_promedio = []
for t in range(1, 7):
    for a in range(1, 7):
        fila = {'Afluente': a, 'Temporada': t}
        for w in range(1, 49):
            fila[w] = escenario_promedio[(a, w, t)]
        datos_promedio.append(fila)

df_promedio = pd.DataFrame(datos_promedio)
df_promedio.to_excel(f'{OUTPUT_DIR}/escenario_promedio.xlsx', index=False)
print(f"  ✓ Guardado: {OUTPUT_DIR}/escenario_promedio.xlsx")

# ============================================================
# RESUMEN FINAL
# ============================================================

print("\n" + "=" * 70)
print("✅ SIMULACIÓN COMPLETADA")
print("=" * 70)
print(f"\nArchivos generados:")
print(f"  📁 Directorio: {OUTPUT_DIR}/")
print(f"  📄 10 escenarios representativos en archivos separados (de {NUM_ESCENARIOS} generados)")
print(f"     ├─ escenario_{indices_seleccionados[0]+1:03d}.xlsx: MÁS PESIMISTA (caudal promedio: {caudales_promedio[indices_seleccionados[0]]:.2f} m³/s)")
print(f"     ├─ escenario_{indices_seleccionados[4]+1:03d}.xlsx: MEDIO")
print(f"     └─ escenario_{indices_seleccionados[-1]+1:03d}.xlsx: MÁS OPTIMISTA (caudal promedio: {caudales_promedio[indices_seleccionados[-1]]:.2f} m³/s)")
print(f"  📄 todos_escenarios.xlsx (consolidado con TODOS los {NUM_ESCENARIOS} escenarios, ordenados)")
print(f"  📄 escenario_promedio.xlsx (promedio de todos, para usar en el modelo)")
print(f"  📊 comparacion_historicos_simulados.png (validación visual)")
print(f"\n📊 Ordenamiento de escenarios:")
print(f"  Escenario #1 (más pesimista):   {caudales_promedio[0]:.2f} m³/s promedio")
print(f"  Escenario #50 (mediano):        {caudales_promedio[49]:.2f} m³/s promedio")
print(f"  Escenario #100 (más optimista): {caudales_promedio[-1]:.2f} m³/s promedio")
print(f"\nParámetros usados:")
print(f"  Método: {METODO}")
print(f"  Escenarios: {NUM_ESCENARIOS}")
print(f"  Semilla: {SEED}")
print(f"  Afluentes: 6")
print(f"  Semanas: 48")
print(f"  Temporadas: 5")
print("\n" + "=" * 70)
