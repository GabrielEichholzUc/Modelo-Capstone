"""
Script para mostrar resumen completo de resultados del Modelo LaTeX
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import os

print("\n" + "="*80)
print("RESUMEN COMPLETO DE RESULTADOS - MODELO LATEX")
print("="*80 + "\n")

# ============================================================
# 1. CARGAR DATOS
# ============================================================

volumenes = pd.read_csv('resultados/volumenes_lago.csv')
riego = pd.read_csv('resultados/riego.csv')
alpha = pd.read_csv('resultados/decision_alpha.csv')
beta = pd.read_csv('resultados/decision_beta.csv')
delta = pd.read_csv('resultados/decision_delta.csv')
generacion = pd.read_csv('resultados/generacion.csv')
energia_total = pd.read_csv('resultados/energia_total.csv')
vertimientos = pd.read_csv('resultados/vertimientos.csv')

try:
    phi_zonas = pd.read_csv('resultados/phi_zonas.csv')
except:
    phi_zonas = None

# ============================================================
# 2. ESTADÍSTICAS GENERALES
# ============================================================

print("📊 ESTADÍSTICAS GENERALES")
print("-" * 80)

# Energía
energia_total_5t = energia_total['Energia_GWh'].sum()
print(f"\n🔋 GENERACIÓN ELÉCTRICA:")
print(f"   Total 5 temporadas: {energia_total_5t:,.2f} GWh")
print(f"   Promedio por temporada: {energia_total_5t/5:,.2f} GWh")

for t in sorted(energia_total['Temporada'].unique()):
    energia_t = energia_total[energia_total['Temporada']==t]['Energia_GWh'].sum()
    print(f"   Temporada {t}: {energia_t:,.2f} GWh")

# Principales generadores
print(f"\n🏭 TOP 5 CENTRALES (5 temporadas):")
energia_por_central = energia_total.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False)
for i, (central, energia) in enumerate(energia_por_central.head(5).items(), 1):
    porc = (energia / energia_total_5t) * 100
    print(f"   {i}. Central {central}: {energia:,.2f} GWh ({porc:.1f}%)")

# Volúmenes
print(f"\n💧 VOLÚMENES DEL LAGO:")
print(f"   Inicial: {volumenes.iloc[0]['Volumen_hm3']:.2f} hm³")
print(f"   Final: {volumenes.iloc[-1]['Volumen_hm3']:.2f} hm³")
print(f"   Mínimo: {volumenes['Volumen_hm3'].min():.2f} hm³ (Sem {volumenes.loc[volumenes['Volumen_hm3'].idxmin(), 'Semana']}, T{volumenes.loc[volumenes['Volumen_hm3'].idxmin(), 'Temporada']})")
print(f"   Máximo: {volumenes['Volumen_hm3'].max():.2f} hm³ (Sem {volumenes.loc[volumenes['Volumen_hm3'].idxmax(), 'Semana']}, T{volumenes.loc[volumenes['Volumen_hm3'].idxmax(), 'Temporada']})")
print(f"   Promedio: {volumenes['Volumen_hm3'].mean():.2f} hm³")

# Riego
print(f"\n🌾 CUMPLIMIENTO DE RIEGO:")
incumplimientos = riego[riego['Incumplimiento'] > 0.5]
print(f"   Incumplimientos de convenio: {len(incumplimientos)} / {len(riego)} provisiones")
if len(incumplimientos) > 0:
    print(f"   Porcentaje de cumplimiento: {(1 - len(incumplimientos)/len(riego))*100:.2f}%")
    print(f"\n   Detalles de incumplimientos:")
    for _, row in incumplimientos.head(10).iterrows():
        canal_map = {1: 'RieZaCo', 2: 'RieTucapel', 3: 'RieSaltos', 4: 'Abanico'}
        demanda_map = {1: 'Primeros', 2: 'Segundos', 3: 'Saltos'}
        print(f"      - Sem {int(row['Semana'])}, T{int(row['Temporada'])}: {demanda_map[int(row['Demanda'])]} en {canal_map[int(row['Canal'])]}, Déficit: {row['Deficit_m3s']:.2f} m³/s")
else:
    print(f"   ✅ Cumplimiento perfecto: 100%")

# Déficit total
deficit_total = riego['Deficit_m3s'].sum()
demanda_total = riego['Demanda_m3s'].sum()
print(f"   Déficit total acumulado: {deficit_total:.2f} m³/s")
print(f"   Demanda total acumulada: {demanda_total:.2f} m³/s")
if demanda_total > 0:
    print(f"   Tasa de satisfacción: {(1 - deficit_total/demanda_total)*100:.4f}%")

# Penalizaciones
print(f"\n⚠️  PENALIZACIONES:")
betas_activos = beta[beta['Beta'] > 0.5]
deltas_activos = delta[delta['Delta'] > 0.5]
print(f"   Violaciones V_MIN (β=1): {len(betas_activos)}")
print(f"   Violaciones V_MAX (δ=1): {len(deltas_activos)}")

if len(betas_activos) > 0:
    print(f"   Semanas con β=1:")
    for _, row in betas_activos.iterrows():
        print(f"      - Sem {int(row['Semana'])}, T{int(row['Temporada'])}")

if len(deltas_activos) > 0:
    print(f"   Semanas con δ=1:")
    for _, row in deltas_activos.iterrows():
        print(f"      - Sem {int(row['Semana'])}, T{int(row['Temporada'])}")

# Alpha (Abanico vs Tucapel)
print(f"\n🔀 DECISIÓN ABANICO vs TUCAPEL (α):")
alphas_abanico = alpha[alpha['Alpha'] > 0.5]
alphas_tucapel = alpha[alpha['Alpha'] < 0.5]
print(f"   Abanico (α=1): {len(alphas_abanico)} semanas ({len(alphas_abanico)/len(alpha)*100:.1f}%)")
print(f"   Tucapel (α=0): {len(alphas_tucapel)} semanas ({len(alphas_tucapel)/len(alpha)*100:.1f}%)")

# Vertimientos
print(f"\n🌊 VERTIMIENTOS:")
vert_positivos = vertimientos[vertimientos['Caudal_m3s'] > 0.01]
if len(vert_positivos) > 0:
    print(f"   Total registros con vertimiento: {len(vert_positivos)}")
    print(f"   Caudal máximo vertido: {vert_positivos['Caudal_m3s'].max():.2f} m³/s")
    print(f"   Principales centrales con vertimiento:")
    vert_por_central = vert_positivos.groupby('Central')['Caudal_m3s'].sum().sort_values(ascending=False)
    for central, caudal in vert_por_central.head(5).items():
        print(f"      Central {central}: {caudal:.2f} m³/s acumulado")
else:
    print(f"   ✅ Sin vertimientos significativos")

# Zonas phi
if phi_zonas is not None and len(phi_zonas) > 0:
    print(f"\n🎯 ZONAS DE LINEALIZACIÓN (φ=1):")
    print(f"   Total activaciones: {len(phi_zonas)}")
    zonas_usadas = sorted(phi_zonas['Zona'].unique())
    print(f"   Zonas utilizadas: {len(zonas_usadas)} zonas")
    print(f"   Rango: Zona {min(zonas_usadas)} - Zona {max(zonas_usadas)}")
    
    # Zonas más frecuentes
    zonas_freq = phi_zonas['Zona'].value_counts().head(5)
    print(f"   Zonas más frecuentes:")
    for zona, freq in zonas_freq.items():
        print(f"      Zona {zona}: {freq} activaciones")

print("\n" + "="*80)
print("GRÁFICOS GENERADOS EN CARPETA 'graficos/':")
print("="*80)

# Listar gráficos
graficos_dir = 'graficos'
if os.path.exists(graficos_dir):
    archivos = [f for f in os.listdir(graficos_dir) if f.endswith('.png')]
    archivos.sort()
    print(f"\nTotal: {len(archivos)} gráficos")
    for i, archivo in enumerate(archivos, 1):
        print(f"  {i:2d}. {archivo}")
else:
    print("⚠️  Carpeta 'graficos/' no encontrada")

print("\n" + "="*80)
print("ARCHIVOS CSV GENERADOS EN CARPETA 'resultados/':")
print("="*80)

resultados_dir = 'resultados'
if os.path.exists(resultados_dir):
    archivos_csv = [f for f in os.listdir(resultados_dir) if f.endswith('.csv')]
    archivos_csv.sort()
    print(f"\nTotal: {len(archivos_csv)} archivos CSV")
    for i, archivo in enumerate(archivos_csv, 1):
        ruta = os.path.join(resultados_dir, archivo)
        df_temp = pd.read_csv(ruta)
        print(f"  {i:2d}. {archivo:<40} ({len(df_temp)} registros)")
else:
    print("⚠️  Carpeta 'resultados/' no encontrada")

print("\n" + "="*80)
print("✅ ANÁLISIS COMPLETADO")
print("="*80 + "\n")

# ============================================================
# 3. GRÁFICO RESUMEN EN DASHBOARD
# ============================================================

print("📊 Generando dashboard resumen...")

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Panel 1: Volumen del lago
ax1 = fig.add_subplot(gs[0, :2])
for t in range(1, 6):
    data_t = volumenes[volumenes['Temporada'] == t]
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    ax1.plot(semanas, data_t['Volumen_hm3'], linewidth=2, label=f'T{t}')

ax1.axhline(y=1400, color='red', linestyle='--', alpha=0.7, label='V_MIN')
ax1.axhline(y=5582, color='orange', linestyle='--', alpha=0.7, label='V_MAX')
ax1.set_xlabel('Semana Global', fontweight='bold')
ax1.set_ylabel('Volumen (hm³)', fontweight='bold')
ax1.set_title('Evolución Volumen del Lago', fontsize=13, fontweight='bold')
ax1.legend(ncol=7, fontsize=9)
ax1.grid(alpha=0.3)

# Panel 2: Energía por temporada
ax2 = fig.add_subplot(gs[0, 2])
energia_por_temp = energia_total.groupby('Temporada')['Energia_GWh'].sum()
colors_temp = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
ax2.bar(energia_por_temp.index, energia_por_temp.values, color=colors_temp, alpha=0.8)
ax2.set_xlabel('Temporada', fontweight='bold')
ax2.set_ylabel('Energía (GWh)', fontweight='bold')
ax2.set_title('Generación por Temporada', fontsize=13, fontweight='bold')
ax2.set_xticks([1, 2, 3, 4, 5])
ax2.grid(alpha=0.3, axis='y')
for i, v in enumerate(energia_por_temp.values):
    ax2.text(i+1, v + 100, f'{v:,.0f}', ha='center', fontsize=9, fontweight='bold')

# Panel 3: Top 5 centrales
ax3 = fig.add_subplot(gs[1, :2])
top5_centrales = energia_total.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False).head(10)
ax3.barh(range(len(top5_centrales)), top5_centrales.values, color='steelblue', alpha=0.8)
ax3.set_yticks(range(len(top5_centrales)))
ax3.set_yticklabels([f'Central {int(c)}' for c in top5_centrales.index])
ax3.set_xlabel('Energía Total (GWh)', fontweight='bold')
ax3.set_title('Top 10 Centrales - 5 Temporadas', fontsize=13, fontweight='bold')
ax3.grid(alpha=0.3, axis='x')
for i, v in enumerate(top5_centrales.values):
    ax3.text(v + 50, i, f'{v:,.0f}', va='center', fontsize=9, fontweight='bold')

# Panel 4: Cumplimiento de riego
ax4 = fig.add_subplot(gs[1, 2])
total_provisiones = len(riego)
cumplimientos = total_provisiones - len(incumplimientos)
datos_pie = [cumplimientos, len(incumplimientos)]
labels_pie = ['Cumplido', 'Incumplido']
colors_pie = ['#2ecc71', '#e74c3c']
explode = (0, 0.1) if len(incumplimientos) > 0 else (0, 0)
ax4.pie(datos_pie, labels=labels_pie, autopct='%1.1f%%', colors=colors_pie, 
        explode=explode, startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
ax4.set_title('Cumplimiento de Convenio', fontsize=13, fontweight='bold')

# Panel 5: Decisión Alpha
ax5 = fig.add_subplot(gs[2, 0])
abanico_count = len(alphas_abanico)
tucapel_count = len(alphas_tucapel)
ax5.bar(['Abanico\n(α=1)', 'Tucapel\n(α=0)'], [abanico_count, tucapel_count], 
        color=['#3498db', '#e67e22'], alpha=0.8)
ax5.set_ylabel('Semanas', fontweight='bold')
ax5.set_title('Decisión Abanico vs Tucapel', fontsize=13, fontweight='bold')
ax5.grid(alpha=0.3, axis='y')
for i, v in enumerate([abanico_count, tucapel_count]):
    ax5.text(i, v + 2, f'{v}', ha='center', fontsize=10, fontweight='bold')

# Panel 6: Penalizaciones
ax6 = fig.add_subplot(gs[2, 1])
pen_data = [len(betas_activos), len(deltas_activos)]
pen_labels = ['V_MIN\n(β)', 'V_MAX\n(δ)']
pen_colors = ['#e74c3c', '#f39c12']
ax6.bar(pen_labels, pen_data, color=pen_colors, alpha=0.8)
ax6.set_ylabel('Ocurrencias', fontweight='bold')
ax6.set_title('Penalizaciones', fontsize=13, fontweight='bold')
ax6.grid(alpha=0.3, axis='y')
for i, v in enumerate(pen_data):
    if v > 0:
        ax6.text(i, v + 0.5, f'{v}', ha='center', fontsize=10, fontweight='bold')

# Panel 7: Estadísticas del volumen
ax7 = fig.add_subplot(gs[2, 2])
ax7.axis('off')
stats_text = f"""
ESTADÍSTICAS DEL LAGO

Volumen Inicial:   {volumenes.iloc[0]['Volumen_hm3']:,.0f} hm³
Volumen Final:     {volumenes.iloc[-1]['Volumen_hm3']:,.0f} hm³

Volumen Mínimo:    {volumenes['Volumen_hm3'].min():,.0f} hm³
Volumen Máximo:    {volumenes['Volumen_hm3'].max():,.0f} hm³
Volumen Promedio:  {volumenes['Volumen_hm3'].mean():,.0f} hm³

GENERACIÓN TOTAL

5 Temporadas:      {energia_total_5t:,.0f} GWh
Promedio/Temp:     {energia_total_5t/5:,.0f} GWh

CUMPLIMIENTO

Riego:             {(1 - len(incumplimientos)/len(riego))*100:.2f}%
Penalizaciones:    {len(betas_activos) + len(deltas_activos)}
"""
ax7.text(0.05, 0.95, stats_text, transform=ax7.transAxes, fontsize=11,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.suptitle('DASHBOARD RESUMEN - MODELO LATEX (5 TEMPORADAS)', 
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig('graficos/0_dashboard_resumen.png', dpi=300, bbox_inches='tight')
print(f"✅ Dashboard guardado: graficos/0_dashboard_resumen.png")
plt.close()

print("\n" + "="*80)
print("✅ PROCESO COMPLETADO")
print("="*80 + "\n")
