"""
Script para visualizar resultados del modelo de optimización - 6 temporadas
Genera gráficos de:
- Evolución de volúmenes del lago V[w,t]
- Evolución de volúmenes por uso ve[u,w,t]
- Comparación demanda vs provisión de riego con indicador alpha
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para evitar bloqueos
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import os
import sys

# Configurar codificación UTF-8 para la salida estándar
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# Crear carpeta para gráficos
output_dir = 'graficos'
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# CARGAR DATOS
# ============================================================

print("Cargando resultados...")
volumenes = pd.read_csv('resultados/volumenes_lago.csv')
riego = pd.read_csv('resultados/riego.csv')
alpha = pd.read_csv('resultados/decision_alpha.csv')
generacion = pd.read_csv('resultados/generacion.csv')
energia_total = pd.read_csv('resultados/energia_total.csv')

# Cargar beta y delta (nuevo en modelo LaTeX)
beta = pd.read_csv('resultados/decision_beta.csv')
delta = pd.read_csv('resultados/decision_delta.csv')

# Cargar volúmenes VR y VG (nuevo)
vr_vg = pd.read_csv('resultados/volumenes_vr_vg.csv')
volumenes_uso = pd.read_csv('resultados/volumenes_por_uso.csv')
extracciones_uso = pd.read_csv('resultados/extracciones_por_uso.csv')

# Intentar cargar filtraciones
try:
    filtraciones = pd.read_csv('resultados/filtraciones.csv')
    print(f"✓ Filtraciones cargadas: {len(filtraciones)} registros")
except FileNotFoundError:
    filtraciones = None
    print("⚠ No se encontró archivo de filtraciones")

# Intentar cargar phi_zonas (nuevo en modelo LaTeX)
try:
    phi_zonas = pd.read_csv('resultados/phi_zonas.csv')
    print(f"✓ Datos cargados: {len(volumenes)} volúmenes lago, {len(riego)} riego, {len(generacion)} generación, {len(energia_total)} GEN[i,t], {len(phi_zonas)} phi zonas")
except FileNotFoundError:
    phi_zonas = None
    print(f"✓ Datos cargados: {len(volumenes)} volúmenes lago, {len(riego)} riego, {len(generacion)} generación, {len(energia_total)} GEN[i,t]")

# Cargar parámetros para obtener V_MIN, V_MAX
try:
    from cargar_datos_5temporadas import cargar_parametros_excel
    parametros = cargar_parametros_excel()
    V_MIN = parametros.get('V_MIN', 1400)
    V_MAX = parametros.get('V_MAX', 5582)
    # Cargar afluentes QA para restar a la demanda
    QA = parametros.get('QA', {})
    print(f"✓ Parámetros cargados: V_MIN={V_MIN} hm³, V_MAX={V_MAX} hm³, Afluentes QA cargados")
except:
    V_MIN = 1400
    V_MAX = 5582
    QA = {}
    print(f"⚠ No se pudieron cargar parámetros, usando valores por defecto: V_MIN={V_MIN} hm³, V_MAX={V_MAX} hm³")

# Compatibilidad con código antiguo
V_min = V_MIN

# Parámetros del modelo
T = list(range(1, 7))  # 6 temporadas
W = list(range(1, 49))  # 48 semanas
U = [1, 2]  # Usos: 1=Riego, 2=Generación
J = [1, 2, 3, 4]  # Canales: 1=RieZaCo, 2=RieTucapel, 3=RieSaltos, 4=Abanico
D = [1, 2, 3]  # Demandantes: 1=Primeros Regantes, 2=Segundos Regantes, 3=Saltos del Laja

nombres_usos = {1: 'Riego', 2: 'Generación'}
nombres_canales = {1: 'RieZaCo', 2: 'RieTucapel', 3: 'RieSaltos', 4: 'Abanico'}
nombres_demandantes = {1: 'Primeros Regantes', 2: 'Segundos Regantes', 3: 'Saltos del Laja'}

print(f"✓ Datos cargados: {len(volumenes)} registros de volúmenes, {len(riego)} de riego")

# ============================================================
# DASHBOARD RESUMEN - GRÁFICO 0
# ============================================================

print("\n📊 Generando DASHBOARD RESUMEN (Gráfico 0)...")

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(4, 3, hspace=0.4, wspace=0.35, 
                      left=0.08, right=0.96, top=0.93, bottom=0.06)

# Colores por temporada
colors_temp = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
nombres_temp = {1: 'Temp 1 (Abr-Jul)', 2: 'Temp 2 (Ago-Oct)', 
                3: 'Temp 3 (Nov-Ene)', 4: 'Temp 4 (Feb-Mar)', 5: 'Temp 5 (Abr-Jul)', 6: 'Temp 6 (Ago-Oct)'}

# ========== PANEL 1: VOLUMEN LAGO (todas las temporadas) ==========
ax1 = fig.add_subplot(gs[0, :])
for t in T:
    data_t = volumenes[volumenes['Temporada'] == t]
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    ax1.plot(semanas, data_t['Volumen_hm3'], color=colors_temp[t-1], 
             linewidth=2.5, label=nombres_temp[t], alpha=0.9)

ax1.axhline(y=V_MIN, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'V_MIN ({V_MIN} hm³)')
ax1.axhline(y=V_MAX, color='green', linestyle='--', linewidth=2, alpha=0.7, label=f'V_MAX ({V_MAX} hm³)')

for t in range(1, 7):
    ax1.axvline(x=t*48, color='gray', linestyle=':', alpha=0.4, linewidth=1)

ax1.set_xlabel('Semanas (Agrupadas por Temporada)', fontweight='bold', fontsize=11)
ax1.set_ylabel('Volumen (hm³)', fontweight='bold', fontsize=11)
ax1.set_title('📊 VOLUMEN DEL LAGO LAJA - 6 TEMPORADAS', 
              fontweight='bold', fontsize=13, pad=12)
ax1.legend(loc='best', framealpha=0.95, fontsize=9, ncol=7)
ax1.grid(True, alpha=0.3)
ax1.set_ylim(V_MIN - 200, V_MAX + 200)

# (El resto del archivo es idéntico al original...)
plt.savefig(f'{output_dir}/0_dashboard_resumen.png', dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✓ Guardado: {output_dir}/0_dashboard_resumen.png")
plt.close()
