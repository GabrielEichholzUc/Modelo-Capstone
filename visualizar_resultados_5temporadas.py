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
    print(f"✓ Parámetros cargados: V_MIN={V_MIN} hm³, V_MAX={V_MAX} hm³")
except:
    V_MIN = 1400
    V_MAX = 5582
    print(f"⚠ No se pudieron cargar parámetros, usando valores por defecto: V_MIN={V_MIN} hm³, V_MAX={V_MAX} hm³")

# Compatibilidad con código antiguo
V_min = V_MIN
volumenes_uso = None  # Ya no se usa en modelo LaTeX

# Parámetros del modelo
T = list(range(1, 7))  # 6 temporadas
W = list(range(1, 49))  # 48 semanas
U = [1, 2]  # Usos: 1=Riego, 2=Generación
J = [1, 2, 3, 4]  # Canales: 1=RieZaCo, 2=RieTucapel, 3=RieSaltos, 4=Abanico
D = [1, 2, 3]  # Demandantes: 1=Primeros, 2=Segundos, 3=Saltos del Laja

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

# ========== PANEL 2: GENERACIÓN POR CENTRAL ==========
ax2 = fig.add_subplot(gs[1, 0])
gen_por_central = energia_total.groupby('Central')['Energia_GWh'].sum()
centrales_top = gen_por_central.sort_values(ascending=False).head(8)

bars = ax2.barh(range(len(centrales_top)), centrales_top.values, 
                color=plt.cm.viridis(np.linspace(0.3, 0.9, len(centrales_top))))
ax2.set_yticks(range(len(centrales_top)))
ax2.set_yticklabels([f'Central {int(c)}' for c in centrales_top.index], fontsize=9)
ax2.set_xlabel('Generación Total (GWh)', fontweight='bold', fontsize=10)
ax2.set_title('⚡ GENERACIÓN POR CENTRAL', fontweight='bold', fontsize=11)
ax2.grid(True, axis='x', alpha=0.3)

for i, (idx, val) in enumerate(centrales_top.items()):
    ax2.text(val + max(centrales_top.values)*0.01, i, f'{val:.0f}', 
             va='center', fontsize=9, fontweight='bold')

# ========== PANEL 3: RIEGO POR CANAL ==========
ax3 = fig.add_subplot(gs[1, 1])
riego_por_canal = riego.groupby('Canal')['Provisto_m3s'].sum()
canal_nombres = [nombres_canales.get(int(c.split('_')[1]), f'Canal {c}') 
                 if '_' in str(c) else nombres_canales.get(c, f'Canal {c}') 
                 for c in riego_por_canal.index]

bars = ax3.bar(range(len(riego_por_canal)), riego_por_canal.values,
               color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax3.set_xticks(range(len(riego_por_canal)))
ax3.set_xticklabels(canal_nombres, rotation=45, ha='right', fontsize=9)
ax3.set_ylabel('Provisión Total (m³/s)', fontweight='bold', fontsize=10)
ax3.set_title('💧 PROVISIÓN DE RIEGO POR CANAL', fontweight='bold', fontsize=11)
ax3.grid(True, axis='y', alpha=0.3)

for i, val in enumerate(riego_por_canal.values):
    ax3.text(i, val + max(riego_por_canal.values)*0.02, f'{val:.0f}', 
             ha='center', fontsize=9, fontweight='bold')

# ========== PANEL 4: CUMPLIMIENTO DEMANDA (Déficit) ==========
ax4 = fig.add_subplot(gs[1, 2])
# Calcular cumplimiento como (Provisto / Demanda) * 100
riego_canal = riego.groupby('Canal').agg({
    'Provisto_m3s': 'sum',
    'Demanda_m3s': 'sum'
})
riego_canal['Cumplimiento'] = (riego_canal['Provisto_m3s'] / riego_canal['Demanda_m3s']) * 100
riego_canal = riego_canal.fillna(0)

canales_labels = [nombres_canales.get(int(c.split('_')[1]), f'Canal {c}') 
                  if '_' in str(c) else nombres_canales.get(c, f'Canal {c}') 
                  for c in riego_canal.index]

x_pos = np.arange(len(riego_canal))
bars = ax4.bar(x_pos, riego_canal['Cumplimiento'].values, 
               color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'], alpha=0.7)

ax4.axhline(y=100, color='green', linestyle='--', linewidth=2, alpha=0.5, label='100% Cumplimiento')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(canales_labels, rotation=45, ha='right', fontsize=9)
ax4.set_ylabel('Cumplimiento (%)', fontweight='bold', fontsize=10)
ax4.set_title('📈 CUMPLIMIENTO DEMANDA RIEGO', fontweight='bold', fontsize=11)
ax4.set_ylim(0, 110)
ax4.legend(fontsize=8)
ax4.grid(True, axis='y', alpha=0.3)

for i, val in enumerate(riego_canal['Cumplimiento'].values):
    ax4.text(i, val + 2, f'{val:.1f}%', ha='center', fontsize=8, fontweight='bold')

# ========== PANEL 5: ENERGÍA POR TEMPORADA ==========
ax5 = fig.add_subplot(gs[2, 0])
energia_temp = energia_total.groupby('Temporada')['Energia_GWh'].sum()
bars = ax5.bar(energia_temp.index, energia_temp.values, 
               color=colors_temp, alpha=0.8, edgecolor='black', linewidth=1.5)
ax5.set_xlabel('Temporada', fontweight='bold', fontsize=10)
ax5.set_ylabel('Energía Total (GWh)', fontweight='bold', fontsize=10)
ax5.set_title('⚡ ENERGÍA GENERADA POR TEMPORADA', fontweight='bold', fontsize=11)
ax5.set_xticks(T)
ax5.set_xticklabels([f'T{t}' for t in T])
ax5.grid(True, axis='y', alpha=0.3)

for i, (idx, val) in enumerate(energia_temp.items()):
    ax5.text(idx, val + max(energia_temp.values)*0.02, f'{val:.0f}', 
             ha='center', fontsize=9, fontweight='bold')

# ========== PANEL 6: FILTRACIONES (si existen) ==========
ax6 = fig.add_subplot(gs[2, 1])
if filtraciones is not None and len(filtraciones) > 0:
    filt_temp = filtraciones.groupby('Temporada')['Filtracion_m3s'].mean()
    bars = ax6.bar(filt_temp.index, filt_temp.values, 
                   color='#FF6B6B', alpha=0.7, edgecolor='darkred', linewidth=1.5)
    ax6.set_xlabel('Temporada', fontweight='bold', fontsize=10)
    ax6.set_ylabel('Filtración Promedio (m³/s)', fontweight='bold', fontsize=10)
    ax6.set_title('💦 FILTRACIONES PROMEDIO', fontweight='bold', fontsize=11)
    ax6.set_xticks(T)
    ax6.set_xticklabels([f'T{t}' for t in T])
    ax6.grid(True, axis='y', alpha=0.3)
    
    for i, (idx, val) in enumerate(filt_temp.items()):
        ax6.text(idx, val + max(filt_temp.values)*0.02, f'{val:.2f}', 
                 ha='center', fontsize=9, fontweight='bold')
else:
    ax6.text(0.5, 0.5, 'Sin datos de\nfiltraciones', 
             ha='center', va='center', fontsize=14, color='gray',
             transform=ax6.transAxes)
    ax6.set_title('💦 FILTRACIONES', fontweight='bold', fontsize=11)
    ax6.axis('off')

# ========== PANEL 7: ZONAS PHI ACTIVADAS (si existen) ==========
ax7 = fig.add_subplot(gs[2, 2])
if phi_zonas is not None and len(phi_zonas) > 0:
    zonas_activas = phi_zonas[phi_zonas['Phi'] > 0.5].groupby('Zona')['Phi'].count()
    if len(zonas_activas) > 0:
        bars = ax7.bar(zonas_activas.index, zonas_activas.values, 
                       color='#4ECDC4', alpha=0.7, edgecolor='teal', linewidth=1.5)
        ax7.set_xlabel('Zona k', fontweight='bold', fontsize=10)
        ax7.set_ylabel('Veces Activada', fontweight='bold', fontsize=10)
        ax7.set_title('🔵 ZONAS DE VOLUMEN ACTIVAS', fontweight='bold', fontsize=11)
        ax7.grid(True, axis='y', alpha=0.3)
    else:
        ax7.text(0.5, 0.5, 'Ninguna zona\nactivada', 
                 ha='center', va='center', fontsize=14, color='gray',
                 transform=ax7.transAxes)
        ax7.set_title('🔵 ZONAS ACTIVAS', fontweight='bold', fontsize=11)
        ax7.axis('off')
else:
    ax7.text(0.5, 0.5, 'Sin datos de\nzonas φ', 
             ha='center', va='center', fontsize=14, color='gray',
             transform=ax7.transAxes)
    ax7.set_title('🔵 ZONAS ACTIVAS', fontweight='bold', fontsize=11)
    ax7.axis('off')

# ========== PANEL 8: INDICADORES CLAVE ==========
ax8 = fig.add_subplot(gs[3, :])
ax8.axis('off')

# Calcular KPIs
energia_total_val = energia_total['Energia_GWh'].sum()
cumplimiento_promedio = (riego['Provisto_m3s'].sum() / riego['Demanda_m3s'].sum()) * 100
vol_min_violaciones = len(volumenes[volumenes['Volumen_hm3'] < V_MIN])
vol_max_violaciones = len(volumenes[volumenes['Volumen_hm3'] > V_MAX])
riego_total = riego['Provisto_m3s'].sum()
gen_max_central = energia_total.groupby('Central')['Energia_GWh'].sum().max()
central_max_idx = energia_total.groupby('Central')['Energia_GWh'].sum().idxmax()
central_max = f"Central {int(central_max_idx)}"

# Crear tabla de KPIs
kpi_data = [
    ['⚡ ENERGÍA TOTAL', f'{energia_total_val:.2f} GWh', '🏆'],
    ['💧 RIEGO TOTAL', f'{riego_total:.0f} m³/s', '💧'],
    ['📊 CUMPLIMIENTO α', f'{cumplimiento_promedio:.1f}%', '✅' if cumplimiento_promedio >= 95 else '⚠️'],
    ['📉 Violaciones V_MIN', f'{vol_min_violaciones} semanas', '🔴' if vol_min_violaciones > 0 else '✅'],
    ['📈 Violaciones V_MAX', f'{vol_max_violaciones} semanas', '🔴' if vol_max_violaciones > 0 else '✅'],
    ['⭐ Central Top', f'{central_max}: {gen_max_central:.0f} GWh', '🌟']
]

# Dibujar tabla estilizada
table_y = 0.8
for i, (label, value, icon) in enumerate(kpi_data):
    x_pos = (i % 3) / 3 + 0.05
    y_pos = table_y - (i // 3) * 0.35
    
    # Caja de fondo
    box_color = '#E8F4F8' if i % 2 == 0 else '#F0F0F0'
    rect = plt.Rectangle((x_pos, y_pos - 0.12), 0.28, 0.18, 
                         facecolor=box_color, edgecolor='#333', 
                         linewidth=2, transform=ax8.transAxes, 
                         zorder=1, alpha=0.8)
    ax8.add_patch(rect)
    
    # Texto
    ax8.text(x_pos + 0.02, y_pos - 0.02, icon, fontsize=24, 
             transform=ax8.transAxes, va='center', ha='left')
    ax8.text(x_pos + 0.06, y_pos - 0.02, label, fontsize=11, 
             fontweight='bold', transform=ax8.transAxes, va='center', ha='left')
    ax8.text(x_pos + 0.14, y_pos - 0.08, value, fontsize=13, 
             fontweight='bold', color='#1f77b4', transform=ax8.transAxes, 
             va='center', ha='center')

# Título del dashboard
fig.suptitle('🎯 DASHBOARD RESUMEN - MODELO OPTIMIZACIÓN LAGO LAJA', 
             fontsize=16, fontweight='bold', y=0.97)

plt.savefig(f'{output_dir}/0_dashboard_resumen.png', dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✓ Guardado: {output_dir}/0_dashboard_resumen.png")
plt.close()

# ============================================================
# GRÁFICO 1: EVOLUCIÓN V[w,t] - TODAS LAS TEMPORADAS JUNTAS
# ============================================================

print("\n📊 Generando gráfico 1: Volumen lago (todas temporadas agregadas)...")

fig, ax = plt.subplots(figsize=(20, 8))

# Plotear cada temporada una al lado de la otra
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for t in T:
    data_t = volumenes[volumenes['Temporada'] == t]
    # Offset: posicionar cada temporada en su propio bloque de semanas
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    
    ax.plot(semanas, data_t['Volumen_hm3'], 
            linewidth=2, color=colors[t-1], label=f'Temporada {t}', marker='', alpha=0.9)

# Línea horizontal del volumen mínimo
ax.axhline(y=V_MIN, color='red', linestyle='-.', linewidth=2, alpha=0.7, 
           label=f'V_MIN = {V_MIN:.0f} hm³')

# Línea horizontal del volumen máximo
ax.axhline(y=V_MAX, color='orange', linestyle='-.', linewidth=2, alpha=0.7, 
           label=f'V_MAX = {V_MAX:.0f} hm³')

# Líneas verticales para separar temporadas
for t in range(1, 6):
    semana_fin = t * 48
    ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)

# Añadir etiquetas de temporadas en el eje x
ax.set_xticks([24, 72, 120, 168, 216, 264])
ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5', 'T6'], fontsize=11, fontweight='bold')

# Eje x secundario con semanas
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(np.arange(0, 289, 48))
ax2.set_xticklabels([f'{i*48}' for i in range(7)], fontsize=9)
ax2.set_xlabel('Semana Global', fontsize=10)

ax.set_xlabel('Temporadas', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('Evolución del Volumen del Lago Laja - Temporadas Agregadas', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(fontsize=11, loc='best', ncol=5)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/1_volumen_lago_todas_temporadas.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/1_volumen_lago_todas_temporadas.png")
plt.close()

# ============================================================
# GRÁFICO 2: EVOLUCIÓN V[w,t] - TEMPORADAS SEPARADAS (OMITIDO)
# ============================================================

# print("📊 Generando gráfico 2: Volumen lago (temporadas separadas)...")
# Gráfico 2 omitido por solicitud del usuario

# ============================================================
# GRÁFICO 3: ZONAS PHI ACTIVADAS (NUEVO - MODELO LATEX)
# ============================================================

print("📊 Generando gráfico 3: Zonas φ activadas (Modelo LaTeX)...")

if phi_zonas is not None and len(phi_zonas) > 0:
    fig, ax = plt.subplots(figsize=(20, 8))
    
    # Crear scatter plot de zonas activadas
    for t in T:
        data_t = phi_zonas[phi_zonas['Temporada'] == t]
        if len(data_t) == 0:
            continue
        
        x_offset = (t - 1) * 48
        semanas = data_t['Semana'].values + x_offset
        zonas = data_t['Zona'].values
        
        ax.scatter(semanas, zonas, alpha=0.6, s=30, 
                  color=colors[t-1], label=f'Temporada {t}')
    
    # Líneas verticales para separar temporadas
    for t in range(1, 6):
        semana_fin = t * 48
        ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)
    
    ax.set_xticks([24, 72, 120, 168, 216, 264])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5', 'T6'], fontsize=11, fontweight='bold')
    ax.set_xlabel('Temporadas', fontsize=12, fontweight='bold')
    ax.set_ylabel('Zona k', fontsize=12, fontweight='bold')
    ax.set_title('Zonas de Linealización Completas (φ=1) - Modelo LaTeX', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='best', ncol=5)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/3_phi_zonas_activadas.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/3_phi_zonas_activadas.png")
    plt.close()
else:
    print("  ⚠ Saltando gráfico 3: no hay zonas phi activadas (φ siempre 0)")

# Gráfico 4 omitido por solicitud del usuario

# ============================================================
# GRÁFICO 5: DEMANDA VS PROVISIÓN - TODAS LAS TEMPORADAS
# ============================================================

print("📊 Generando gráfico 5: Demanda vs Provisión (todas temporadas agregadas)...")

# Cargar demandas del Excel
try:
    demandas = pd.read_excel('Parametros_Finales.xlsx', sheet_name='QD_d,j,w')
except:
    print("  ⚠ No se pudo cargar QD_d,j,w, usando valores de riego.csv")
    demandas = None

# Agregar alpha al dataframe de riego
riego_alpha = riego.merge(alpha, on=['Semana', 'Temporada'], how='left')
riego_alpha['Alpha'] = riego_alpha['Alpha'].fillna(0)

# Definir qué demandantes mostrar por canal
demandantes_por_canal = {
    1: [1],        # RieZaCo: solo Primeros Regantes
    2: [1, 2],     # RieTucapel: Primeros y Segundos Regantes
    3: [3],        # RieSaltos: solo Saltos del Laja
    4: [1]         # Abanico: solo Primeros Regantes
}

# Crear un gráfico por canal
for j in J:
    canal_nombre = nombres_canales[j]
    data_canal = riego_alpha[riego_alpha['Canal'] == j]
    
    # Obtener demandantes a mostrar para este canal
    demandantes_mostrar = demandantes_por_canal.get(j, D)
    num_demandantes = len(demandantes_mostrar)
    
    fig, axes = plt.subplots(num_demandantes, 1, figsize=(20, 4*num_demandantes), sharex=True)
    
    # Si solo hay un demandante, axes no es un array
    if num_demandantes == 1:
        axes = [axes]
    
    for d_idx, d in enumerate(demandantes_mostrar):
        ax = axes[d_idx]
        data_d = data_canal[data_canal['Demanda'] == d]
        
        if len(data_d) == 0:
            continue
        
        # Plotear cada temporada una al lado de la otra
        colors_demanda = ['#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c']  # Rojo (6 temporadas)
        colors_provision = ['#27ae60', '#2ecc71', '#16a085', '#1abc9c', '#0e6655', '#138d75']  # Verdes (6 temporadas)
        
        for t in T:
            data_t = data_d[data_d['Temporada'] == t]
            if len(data_t) == 0:
                continue
            
            x_offset = (t - 1) * 48
            semanas = data_t['Semana'].values + x_offset
            demanda_vals = data_t['Demanda_m3s'].values
            provision_vals = data_t['Provisto_m3s'].values
            alpha_vals = data_t['Alpha'].values
            
            # Solo mostrar label en primera temporada
            label_d = 'Demanda' if t == 1 else ''
            label_p = f'Provisión T{t}' if True else ''
            
            # Colorear fondo según alpha (solo para Primeros Regantes en canales afectados)
            if j in [1, 2, 4] and d == 1:  # RieZaCo, RieTucapel y Abanico: solo Primeros Regantes
                # Identificar bloques contiguos de alpha=0 y alpha=1
                for i in range(len(semanas)):
                    semana_actual = semanas[i]
                    alpha_actual = alpha_vals[i]
                    
                    # Determinar límites del span
                    if i == len(semanas) - 1:
                        semana_next = semana_actual + 1
                    else:
                        semana_next = semanas[i+1]
                    
                    # Colorear fondo: azul claro si alpha=0 (Tucapel), amarillo si alpha=1 (Abanico)
                    if alpha_actual == 1:
                        # alpha=1 → Abanico activo (amarillo claro)
                        ax.axvspan(semana_actual - 0.5, semana_next - 0.5, 
                                  color='#fff9c4', alpha=0.3, zorder=0)
                    else:
                        # alpha=0 → Tucapel activo (azul claro)
                        ax.axvspan(semana_actual - 0.5, semana_next - 0.5, 
                                  color='#b3e5fc', alpha=0.3, zorder=0)
            
            ax.plot(semanas, demanda_vals, linewidth=1.5, color='red', 
                    label=label_d, linestyle='--', alpha=0.6)
            ax.plot(semanas, provision_vals, linewidth=2, color=colors_provision[t-1], 
                    label=label_p, alpha=0.8)
        
        # Líneas verticales para separar temporadas
        for t in range(1, 6):
            semana_fin = t * 48
            ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)
        
        ax.set_ylabel('Caudal (m³/s)', fontsize=10, fontweight='bold')
        ax.set_title(f'{nombres_demandantes[d]}', fontsize=11, fontweight='bold')
        
        # Agregar leyenda con explicación de colores de fondo (solo para Primeros Regantes)
        if j in [1, 2, 4] and d == 1:
            # Crear parches para la leyenda de alpha y eta
            legend_elements = [
                Patch(facecolor='#ffcdd2', alpha=0.4, label='η=1 (Incumplimiento convenio)'),
                Patch(facecolor='#b3e5fc', alpha=0.3, label='α=0 (Canal Tucapel activo)'),
                Patch(facecolor='#fff9c4', alpha=0.3, label='α=1 (Canal Abanico activo)')
            ]
            
            # Obtener handles de la leyenda existente
            handles, labels = ax.get_legend_handles_labels()
            
            # Combinar ambas leyendas
            ax.legend(handles + legend_elements, labels + ['η=1 (Incumpl.)', 'α=0 (Tucapel)', 'α=1 (Abanico)'],
                     fontsize=9, loc='best', ncol=3)
        else:
            # Para otros demandantes, solo mostrar η si hay incumplimiento
            legend_elements = [
                Patch(facecolor='#ffcdd2', alpha=0.4, label='η=1 (Incumplimiento convenio)')
            ]
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles + legend_elements, labels + ['η=1 (Incumpl.)'],
                     fontsize=9, loc='best', ncol=3)
        ax.grid(True, alpha=0.3)
    
    # Añadir etiquetas de temporadas en el eje x
    axes[-1].set_xticks([24, 72, 120, 168, 216, 264])
    axes[-1].set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5', 'T6'], fontsize=11, fontweight='bold')
    axes[-1].set_xlabel('Temporadas', fontsize=12, fontweight='bold')
    
    plt.suptitle(f'Demanda vs Provisión - Canal {canal_nombre} - Temporadas Agregadas', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/5_demanda_provision_{canal_nombre.lower()}_todas.png', 
                dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/5_demanda_provision_{canal_nombre.lower()}_todas.png")
    plt.close()

# ============================================================
# GRÁFICO 6: DEMANDA VS PROVISIÓN - TEMPORADAS SEPARADAS
# ============================================================

print("📊 Generando gráfico 6: Demanda vs Provisión (por temporada)...")

for j in J:
    canal_nombre = nombres_canales[j]
    data_canal = riego_alpha[riego_alpha['Canal'] == j]
    
    for d in D:
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        axes = axes.flatten()
        
        data_d = data_canal[data_canal['Demanda'] == d]
        
        if len(data_d) == 0:
            plt.close()
            continue
        
        for t in T:
            ax = axes[t - 1]
            data_t = data_d[data_d['Temporada'] == t]
            
            if len(data_t) == 0:
                continue
            
            # Demanda y provisión
            semanas = data_t['Semana'].values
            demanda = data_t['Demanda_m3s'].values
            provision = data_t['Provisto_m3s'].values
            alpha_vals = data_t['Alpha'].values
            eta_vals = data_t['Incumplimiento'].values
            
            # Primero: Colorear fondo ROJO cuando η=1 (incumplimiento de convenio)
            for i in range(len(semanas)):
                semana_actual = semanas[i]
                eta_actual = eta_vals[i]
                
                # Determinar límites del span
                if i == len(semanas) - 1:
                    semana_next = semana_actual + 1
                else:
                    semana_next = semanas[i+1]
                
                # Fondo rojo si η=1 (incumplimiento)
                if eta_actual == 1:
                    ax.axvspan(semana_actual - 0.5, semana_next - 0.5, 
                              color='#ffcdd2', alpha=0.4, zorder=0)
            
            # Segundo: Colorear fondo según alpha (solo para Primeros Regantes en canales afectados)
            if j in [1, 2, 4] and d == 1:  # Solo Primeros Regantes
                for i in range(len(semanas)):
                    semana_actual = semanas[i]
                    alpha_actual = alpha_vals[i]
                    eta_actual = eta_vals[i]
                    
                    # Determinar límites del span
                    if i == len(semanas) - 1:
                        semana_next = semana_actual + 1
                    else:
                        semana_next = semanas[i+1]
                    
                    # Solo colorear si NO hay incumplimiento (para no sobrescribir el rojo)
                    if eta_actual != 1:
                        # Colorear fondo: azul claro si alpha=0 (Tucapel), amarillo si alpha=1 (Abanico)
                        if alpha_actual == 1:
                            # alpha=1 → Abanico activo (amarillo claro)
                            ax.axvspan(semana_actual - 0.5, semana_next - 0.5, 
                                      color='#fff9c4', alpha=0.3, zorder=0)
                        else:
                            # alpha=0 → Tucapel activo (azul claro)
                            ax.axvspan(semana_actual - 0.5, semana_next - 0.5, 
                                      color='#b3e5fc', alpha=0.3, zorder=0)
            
            ax.plot(semanas, demanda, linewidth=2, color='red', 
                    label='Demanda', linestyle='--', alpha=0.7)
            ax.plot(semanas, provision, linewidth=2, color='green', 
                    label='Provisión', marker='o', markersize=2, alpha=0.8)
            
            ax.set_xlabel('Semana', fontsize=10, fontweight='bold')
            ax.set_ylabel('Caudal (m³/s)', fontsize=10, fontweight='bold')
            ax.set_title(f'Temporada {t}', fontsize=11, fontweight='bold')
            
            # Agregar leyenda con explicación de colores de fondo (solo para Primeros Regantes)
            if j in [1, 2, 4] and d == 1:
                # Crear parches para la leyenda de alpha y eta
                legend_elements = [
                    Patch(facecolor='#ffcdd2', alpha=0.4, label='η=1 (Incumpl.)'),
                    Patch(facecolor='#b3e5fc', alpha=0.3, label='α=0 (Tucapel)'),
                    Patch(facecolor='#fff9c4', alpha=0.3, label='α=1 (Abanico)')
                ]
                # Obtener handles de la leyenda existente
                handles, labels = ax.get_legend_handles_labels()
                # Combinar ambas leyendas
                ax.legend(handles + legend_elements, labels + ['η=1', 'α=0', 'α=1'],
                         fontsize=8, loc='best')
            else:
                # Para otros demandantes, solo mostrar η si hay incumplimiento
                legend_elements = [
                    Patch(facecolor='#ffcdd2', alpha=0.4, label='η=1 (Incumpl.)')
                ]
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles + legend_elements, labels + ['η=1'],
                         fontsize=8, loc='best')
            
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 49)
        
        # Ocultar último subplot
        axes[5].axis('off')
        
        # Saltar los gráficos que el usuario no quiere generar
        nombre_grafico = f'6_demanda_provision_{canal_nombre.lower()}_{nombres_demandantes[d].lower().replace(" ", "_")}_separadas.png'
        if nombre_grafico in [
            '6_demanda_provision_abanico_saltos_del_laja_separadas.png',
            '6_demanda_provision_abanico_segundos_regantes_separadas.png',
            '6_demanda_provision_riesaltos_primeros_regantes_separadas.png',
            '6_demanda_provision_riesaltos_segundos_regantes_separadas.png',
            '6_demanda_provision_rietucapel_saltos_del_laja_separadas.png',
            '6_demanda_provision_riezaco_saltos_del_laja_separadas.png',
            '6_demanda_provision_riezaco_segundos_regantes_separadas.png']:
            plt.close()
            continue
        plt.suptitle(f'Demanda vs Provisión - {canal_nombre} - {nombres_demandantes[d]}', 
                     fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/{nombre_grafico}', dpi=300, bbox_inches='tight')
        print(f"  ✓ Guardado: {output_dir}/{nombre_grafico}")
        plt.close()

# ============================================================
# GRÁFICO 7: GENERACIÓN POR CENTRAL Y TEMPORADA (BARRAS)
# ============================================================

print("\n7. Generando gráfico de generación por central...")

# Cargar nombres de centrales desde Excel
from cargar_datos_5temporadas import cargar_parametros_excel, cargar_nombres_centrales

# Cargar nombres de centrales
nombres_centrales = cargar_nombres_centrales()
print(f"  Nombres de centrales cargados: {len(nombres_centrales)} centrales")

# Cargar datos de rendimiento para filtrar centrales con rho > 0
parametros = cargar_parametros_excel()
rho = parametros['rho']  # Diccionario {i: rendimiento}

# Filtrar centrales con rendimiento > 0
centrales_con_rho = [i for i, r in rho.items() if r > 0]
print(f"  Centrales con rendimiento > 0: {centrales_con_rho}")

# Usar directamente las variables GEN_{i,t} del archivo energia_total.csv
# Filtrar solo centrales con rendimiento > 0
energia_filtrada = energia_total[energia_total['Central'].isin(centrales_con_rho)]

# Preparar datos para gráfico de barras agrupadas
centrales = sorted(energia_filtrada['Central'].unique())
temporadas = sorted(energia_filtrada['Temporada'].unique())

# Crear matriz de datos usando GWh
data_matrix = np.zeros((len(centrales), len(temporadas)))
for idx_c, central in enumerate(centrales):
    for idx_t, temp in enumerate(temporadas):
        valor = energia_filtrada[
            (energia_filtrada['Central'] == central) & 
            (energia_filtrada['Temporada'] == temp)
        ]['Energia_GWh'].values
        if len(valor) > 0:
            data_matrix[idx_c, idx_t] = valor[0]

# Crear gráfico de barras agrupadas
fig, ax = plt.subplots(figsize=(16, 8))

x = np.arange(len(centrales))  # Posiciones de las centrales
width = 0.125  # Ancho de cada barra (reducido para 6 temporadas)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for idx_t, temp in enumerate(temporadas):
    offset = width * (idx_t - 2.5)  # Centrar las barras (6 temporadas)
    ax.bar(x + offset, data_matrix[:, idx_t], width, 
           label=f'Temporada {temp}', color=colors[idx_t], alpha=0.85)

ax.set_xlabel('Central', fontsize=12, fontweight='bold')
ax.set_ylabel('Energía Generada (GWh)', fontsize=12, fontweight='bold')
ax.set_title('Energía Generada por Central y Temporada - Variables GEN$_{i,t}$\n(Solo centrales con rendimiento > 0)', 
             fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([nombres_centrales[c] for c in centrales], rotation=45, ha='right')
ax.legend(fontsize=10, loc='best')
ax.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
filename = '7_generacion_por_central_temporada.png'
plt.savefig(f'{output_dir}/{filename}', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/{filename}")
plt.close()

# ============================================================
# GRÁFICO ADICIONAL: FILTRACIONES POR TEMPORADA
# ============================================================

if filtraciones is not None:
    print("\n📊 Generando gráfico de filtraciones...")
    
    # Gráfico 1: Filtraciones por temporada (5 subplots)
    fig, axes = plt.subplots(6, 1, figsize=(18, 24), sharex=True)
    fig.suptitle('Evolución de Filtraciones por Temporada', fontsize=18, fontweight='bold', y=0.995)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for idx, t in enumerate(T):
        ax = axes[idx]
        data_t = filtraciones[filtraciones['Temporada'] == t]
        
        # Plot principal
        ax.plot(data_t['Semana'], data_t['Filtracion_m3s'], 
                linewidth=2.5, color=colors[idx], marker='o', markersize=4, alpha=0.9)
        
        # Sombreado bajo la curva
        ax.fill_between(data_t['Semana'], 0, data_t['Filtracion_m3s'], 
                        alpha=0.2, color=colors[idx])
        
        # Estadísticas
        promedio = data_t['Filtracion_m3s'].mean()
        maximo = data_t['Filtracion_m3s'].max()
        minimo = data_t['Filtracion_m3s'].min()
        
        ax.axhline(y=promedio, color='red', linestyle='--', linewidth=1.5, alpha=0.7, 
                  label=f'Promedio: {promedio:.2f} m³/s')
        
        # Configuración del subplot
        ax.set_ylabel('Filtración (m³/s)', fontsize=12, fontweight='bold')
        ax.set_title(f'Temporada {t} - Min: {minimo:.2f} | Max: {maximo:.2f} | Avg: {promedio:.2f} m³/s', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', fontsize=10)
        
        # Límites
        ax.set_xlim(0.5, 48.5)
        ax.set_ylim(bottom=0)
    
    axes[-1].set_xlabel('Semana', fontsize=12, fontweight='bold')
    plt.tight_layout()
    filename = '8_filtraciones_por_temporada.png'
    plt.savefig(f'{output_dir}/{filename}', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/{filename}")
    plt.close()
    
    # Gráfico 2: Todas las temporadas comparadas
    fig, ax = plt.subplots(figsize=(20, 8))
    
    for t in T:
        data_t = filtraciones[filtraciones['Temporada'] == t]
        x_offset = (t - 1) * 48
        semanas = data_t['Semana'].values + x_offset
        
        ax.plot(semanas, data_t['Filtracion_m3s'], 
                linewidth=2, color=colors[t-1], label=f'Temporada {t}', 
                marker='o', markersize=3, alpha=0.9)
    
    # Separadores verticales entre temporadas
    for t in range(1, 6):
        ax.axvline(x=t*48, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    
    ax.set_xlabel('Semana (Agregada por Temporada)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Filtración (m³/s)', fontsize=12, fontweight='bold')
    ax.set_title('Evolución de Filtraciones - Todas las Temporadas', fontsize=16, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(-2, 242)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    filename = '9_filtraciones_comparadas.png'
    plt.savefig(f'{output_dir}/{filename}', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/{filename}")
    plt.close()
else:
    print("\n⚠ No se generaron gráficos de filtraciones (archivo no encontrado)")

# ============================================================
# GRÁFICO 10: ANÁLISIS DE USO DE VOLÚMENES ASIGNADOS POR TEMPORADA
# ============================================================

print("\n📊 Generando GRÁFICO 10: Análisis de uso de volúmenes VR y VG...")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Crear arrays para almacenar los datos agregados
vr_inicial_list = []
vr_usado_list = []
vr_final_list = []
vg_inicial_list = []
vg_usado_list = []
vg_final_list = []
temporadas_list = []

for t in T:
    # Datos iniciales
    vr_0 = volumenes_uso[volumenes_uso['Temporada'] == t]['VR_0_hm3'].values[0]
    vg_0 = volumenes_uso[volumenes_uso['Temporada'] == t]['VG_0_hm3'].values[0]
    
    # Volúmenes finales (última semana)
    vr_final = vr_vg[(vr_vg['Temporada'] == t) & (vr_vg['Semana'] == 48)]['VR_hm3'].values[0]
    vg_final = vr_vg[(vr_vg['Temporada'] == t) & (vr_vg['Semana'] == 48)]['VG_hm3'].values[0]
    
    # Extracción total de la temporada (suma de qer y qeg en hm³)
    extracciones_t = extracciones_uso[extracciones_uso['Temporada'] == t]
    from cargar_datos_5temporadas import cargar_parametros_excel
    parametros = cargar_parametros_excel()
    FS = parametros['FS']
    
    vr_usado = sum(extracciones_t['qer_m3s'].values[w-1] * FS[w] / 1_000_000 for w in range(1, 49))
    vg_usado = sum(extracciones_t['qeg_m3s'].values[w-1] * FS[w] / 1_000_000 for w in range(1, 49))
    
    vr_inicial_list.append(vr_0)
    vr_usado_list.append(vr_usado)
    vr_final_list.append(vr_final)
    
    vg_inicial_list.append(vg_0)
    vg_usado_list.append(vg_usado)
    vg_final_list.append(vg_final)
    
    temporadas_list.append(f'T{t}')

# --- PANEL 1: RIEGO (VR) ---
ax = axes[0]
x_pos = np.arange(len(T))
width = 0.6

# Barras apiladas
bars_vr_inicial = ax.bar(x_pos, vr_inicial_list, width, label='VR Inicial', color='#3498db', alpha=0.9)
bars_vr_usado = ax.bar(x_pos, vr_usado_list, width, label='VR Usado', color='#e74c3c', alpha=0.9)
bars_vr_final = ax.bar(x_pos, vr_final_list, width, bottom=[vr_inicial_list[i] + vr_usado_list[i] for i in range(len(T))],
                       label='VR Final (Sobrante)', color='#2ecc71', alpha=0.9)

# Etiquetas en las barras
for i, (inicial, usado, final) in enumerate(zip(vr_inicial_list, vr_usado_list, vr_final_list)):
    porcentaje_usado = (usado / inicial * 100) if inicial > 0 else 0
    ax.text(i, inicial/2, f'{inicial:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    ax.text(i, inicial + usado/2, f'{usado:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    if final > 0.1:
        ax.text(i, inicial + usado + final/2, f'{final:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.set_xlabel('Temporada', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('RIEGO: Inicial vs Usado vs Final', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(temporadas_list)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

# --- PANEL 2: GENERACIÓN (VG) ---
ax = axes[1]

# Barras apiladas
bars_vg_inicial = ax.bar(x_pos, vg_inicial_list, width, label='VG Inicial', color='#3498db', alpha=0.9)
bars_vg_usado = ax.bar(x_pos, vg_usado_list, width, label='VG Usado', color='#e74c3c', alpha=0.9)
bars_vg_final = ax.bar(x_pos, vg_final_list, width, bottom=[vg_inicial_list[i] + vg_usado_list[i] for i in range(len(T))],
                       label='VG Final (Sobrante)', color='#2ecc71', alpha=0.9)

# Etiquetas en las barras
for i, (inicial, usado, final) in enumerate(zip(vg_inicial_list, vg_usado_list, vg_final_list)):
    porcentaje_usado = (usado / inicial * 100) if inicial > 0 else 0
    ax.text(i, inicial/2, f'{inicial:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    ax.text(i, inicial + usado/2, f'{usado:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    if final > 0.1:
        ax.text(i, inicial + usado + final/2, f'{final:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.set_xlabel('Temporada', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('GENERACIÓN: Inicial vs Usado vs Final', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(temporadas_list)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Análisis de Uso de Volúmenes Asignados por Temporada', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
filename = '10_analisis_uso_volumenes.png'
plt.savefig(f'{output_dir}/{filename}', dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✓ Guardado: {output_dir}/{filename}")
plt.close()

# ============================================================
# RESUMEN
# ============================================================

print("\n" + "="*70)
print("✅ VISUALIZACIÓN COMPLETADA")
print("="*70)
print(f"\nGráficos generados en carpeta: {output_dir}/")
print("\nGráficos generados:")
print("  0. Dashboard resumen")
print("  1. Volumen lago - Todas las temporadas juntas")
print("  2. Volumen lago - Por temporada (6 gráficos)")
print("  3. Volúmenes por uso - Todas las temporadas juntas")
print("  4. Volúmenes por uso - Por temporada (2 usos × 6 temporadas)")
print("  5. Demanda vs Provisión - Por canal, todas las temporadas")
print("  6. Demanda vs Provisión - Por canal, demandante y temporada")
print("  7. Generación por central y temporada (barras agrupadas)")
print("  8. Zonas de linealización activadas (phi)")
print("  9. Filtraciones comparadas")
print("  10. Análisis de uso de volúmenes VR y VG")
if filtraciones is not None:
    print("  8. Filtraciones por temporada (5 gráficos)")
    print("  9. Filtraciones - Todas las temporadas comparadas")
print("\n" + "="*70)
