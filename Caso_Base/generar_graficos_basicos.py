"""
Script simplificado para visualizar resultados principales del caso base
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Crear carpeta para gráficos
os.makedirs('graficos', exist_ok=True)

# Parámetros
V_MIN = 1400
V_MAX = 5582
colors_temp = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

print("Cargando datos...")
volumenes = pd.read_csv('resultados/volumenes_lago.csv')
energia = pd.read_csv('resultados/energia_total.csv')
riego = pd.read_csv('resultados/riego.csv')
filtraciones = pd.read_csv('resultados/filtraciones.csv')

# ========== GRÁFICO 1: EVOLUCIÓN DEL VOLUMEN DEL LAGO ==========
print("\n📊 Generando gráfico de volumen del lago...")
plt.figure(figsize=(16, 6))

for t in range(1, 7):
    data_t = volumenes[volumenes['Temporada'] == t]
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    plt.plot(semanas, data_t['Volumen_hm3'], color=colors_temp[t-1], 
             linewidth=2, label=f'Temporada {t}', alpha=0.85)

plt.axhline(y=V_MIN, color='red', linestyle='--', linewidth=2, 
            alpha=0.7, label=f'V_MIN ({V_MIN} hm³)')
plt.axhline(y=V_MAX, color='green', linestyle='--', linewidth=2, 
            alpha=0.7, label=f'V_MAX ({V_MAX} hm³)')

# Líneas separadoras de temporadas
for t in range(1, 6):
    plt.axvline(x=t*48, color='gray', linestyle=':', alpha=0.4, linewidth=1)

plt.xlabel('Semanas (Total: 288 semanas)', fontweight='bold', fontsize=12)
plt.ylabel('Volumen (hm³)', fontweight='bold', fontsize=12)
plt.title('EVOLUCIÓN DEL VOLUMEN DEL LAGO LAJA - CASO BASE (Filtraciones fijas 47 m³/s)', 
          fontweight='bold', fontsize=14, pad=15)
plt.legend(loc='best', framealpha=0.95, fontsize=10, ncol=4)
plt.grid(True, alpha=0.3)
plt.ylim(V_MIN - 300, V_MAX + 300)

plt.tight_layout()
plt.savefig('graficos/1_volumen_lago.png', dpi=300, bbox_inches='tight')
print("  ✓ Guardado: graficos/1_volumen_lago.png")
plt.close()

# ========== GRÁFICO 2: ENERGÍA GENERADA POR TEMPORADA ==========
print("\n📊 Generando gráfico de energía por temporada...")

# Energía por temporada
energia_temp = energia.groupby('Temporada')['Energia_GWh'].sum()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Barras por temporada
ax1.bar(energia_temp.index, energia_temp.values, color=colors_temp, 
        alpha=0.8, edgecolor='black', linewidth=1.5)
ax1.set_xlabel('Temporada', fontweight='bold', fontsize=12)
ax1.set_ylabel('Energía (GWh)', fontweight='bold', fontsize=12)
ax1.set_title('ENERGÍA GENERADA POR TEMPORADA', fontweight='bold', fontsize=13)
ax1.set_xticks(range(1, 7))
ax1.grid(True, alpha=0.3, axis='y')

# Agregar valores sobre barras
for i, v in enumerate(energia_temp.values):
    ax1.text(i + 1, v + 50, f'{v:.1f}\nGWh', ha='center', va='bottom', 
             fontweight='bold', fontsize=9)

# Energía por central (top 10)
energia_central = energia.groupby('Central')['Energia_GWh'].sum().sort_values(ascending=False)
top10 = energia_central.head(10)

nombres_centrales = {
    1: 'El Toro', 2: 'Abanico', 3: 'Antuco', 8: 'Polcura', 
    9: 'Quilleco', 13: 'Trupán', 15: 'Laja'
}
labels = [nombres_centrales.get(i, f'Central {i}') for i in top10.index]

ax2.barh(labels, top10.values, color='steelblue', alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_xlabel('Energía Total (GWh)', fontweight='bold', fontsize=12)
ax2.set_title('TOP 10 CENTRALES GENERADORAS', fontweight='bold', fontsize=13)
ax2.grid(True, alpha=0.3, axis='x')
ax2.invert_yaxis()

# Agregar valores
for i, v in enumerate(top10.values):
    ax2.text(v + 100, i, f'{v:.0f} GWh', va='center', fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig('graficos/2_energia_generada.png', dpi=300, bbox_inches='tight')
print("  ✓ Guardado: graficos/2_energia_generada.png")
plt.close()

# ========== GRÁFICO 3: CUMPLIMIENTO DE DEMANDAS DE RIEGO ==========
print("\n📊 Generando gráfico de cumplimiento de riego...")

# Agrupar por semana y temporada
riego_agg = riego.groupby(['Semana', 'Temporada']).agg({
    'Demanda_m3s': 'sum',
    'Provisto_m3s': 'sum', 
    'Deficit_m3s': 'sum'
}).reset_index()

fig, ax = plt.subplots(figsize=(16, 6))

for t in range(1, 7):
    data_t = riego_agg[riego_agg['Temporada'] == t]
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    
    # Demanda
    ax.plot(semanas, data_t['Demanda_m3s'], color=colors_temp[t-1], 
            linewidth=1.5, alpha=0.4, linestyle='--')
    
    # Provisión
    ax.plot(semanas, data_t['Provisto_m3s'], color=colors_temp[t-1], 
            linewidth=2, label=f'Temp {t}', alpha=0.85)

# Líneas separadoras de temporadas
for t in range(1, 6):
    ax.axvline(x=t*48, color='gray', linestyle=':', alpha=0.4, linewidth=1)

ax.set_xlabel('Semanas', fontweight='bold', fontsize=12)
ax.set_ylabel('Caudal (m³/s)', fontweight='bold', fontsize=12)
ax.set_title('CUMPLIMIENTO DE DEMANDAS DE RIEGO (Línea punteada = demanda, Línea sólida = provisión)', 
             fontweight='bold', fontsize=13, pad=15)
ax.legend(loc='best', framealpha=0.95, fontsize=10, ncol=6)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('graficos/3_cumplimiento_riego.png', dpi=300, bbox_inches='tight')
print("  ✓ Guardado: graficos/3_cumplimiento_riego.png")
plt.close()

# ========== RESUMEN EN CONSOLA ==========
print("\n" + "="*70)
print("RESUMEN DE RESULTADOS - CASO BASE (Filtraciones fijas 47 m³/s)")
print("="*70)

print(f"\n📈 ENERGÍA GENERADA:")
print(f"   Total 6 temporadas: {energia_temp.sum():.2f} GWh")
print(f"   Promedio por temporada: {energia_temp.mean():.2f} GWh")
print(f"   Mejor temporada: T{energia_temp.idxmax()} con {energia_temp.max():.2f} GWh")
print(f"   Peor temporada: T{energia_temp.idxmin()} con {energia_temp.min():.2f} GWh")

print(f"\n💧 VOLUMEN DEL LAGO:")
vol_min = volumenes['Volumen_hm3'].min()
vol_max = volumenes['Volumen_hm3'].max()
vol_promedio = volumenes['Volumen_hm3'].mean()
print(f"   Volumen mínimo: {vol_min:.2f} hm³")
print(f"   Volumen máximo: {vol_max:.2f} hm³")
print(f"   Volumen promedio: {vol_promedio:.2f} hm³")
print(f"   Margen sobre V_MIN: {vol_min - V_MIN:.2f} hm³")
print(f"   Margen bajo V_MAX: {V_MAX - vol_max:.2f} hm³")

print(f"\n🌾 CUMPLIMIENTO DE RIEGO:")
deficit_total = riego['Deficit_m3s'].sum()
incumplimientos = riego['Incumplimiento'].sum()
print(f"   Déficit total: {deficit_total:.4f} m³/s")
print(f"   Incumplimientos: {int(incumplimientos)}")
if deficit_total == 0:
    print("   ✅ Todas las demandas de riego fueron satisfechas al 100%")

print(f"\n💦 FILTRACIONES:")
print(f"   Filtración fija: 47.00 m³/s (constante en todas las semanas)")

print("\n" + "="*70)
print("✅ Gráficos generados exitosamente en carpeta 'graficos/'")
print("="*70)
