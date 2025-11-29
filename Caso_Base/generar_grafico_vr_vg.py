"""
Generar gráfico de análisis de uso de volúmenes VR y VG
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Cargar datos
vr_vg = pd.read_csv('resultados/volumenes_vr_vg.csv')
volumenes_uso = pd.read_csv('resultados/volumenes_por_uso.csv')
extracciones_uso = pd.read_csv('resultados/extracciones_por_uso.csv')

# Cargar FS desde archivo (ya exportado desde optimización)
# FS se puede obtener directamente de los datos de extracciones
# Por simplicidad, usar valores típicos de FS (segundos por semana)
FS = {w: 604800 for w in range(1, 49)}  # 7 días * 24 hrs * 3600 seg = 604800 segundos

T = list(range(1, 7))  # 6 temporadas

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
    
    vr_usado = sum(extracciones_t['qer_m3s'].values[w-1] * FS[w] / 1_000_000 for w in range(1, 49))
    vg_usado = sum(extracciones_t['qeg_m3s'].values[w-1] * FS[w] / 1_000_000 for w in range(1, 49))
    
    vr_inicial_list.append(vr_0)
    vr_usado_list.append(vr_usado)
    vr_final_list.append(vr_final)
    
    vg_inicial_list.append(vg_0)
    vg_usado_list.append(vg_usado)
    vg_final_list.append(vg_final)
    
    temporadas_list.append(f'T{t}')

print(f"VR Inicial: {vr_inicial_list}")
print(f"VR Usado: {vr_usado_list}")
print(f"VR Final: {vr_final_list}")
print(f"VG Inicial: {vg_inicial_list}")
print(f"VG Usado: {vg_usado_list}")
print(f"VG Final: {vg_final_list}")

# Crear figura
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# --- PANEL 1: RIEGO (VR) ---
ax = axes[0]
x_pos = np.arange(len(T))
width = 0.6

# Barras invertidas: negativo para "usado" y "final"
bars_vr_inicial = ax.bar(x_pos, vr_inicial_list, width, label='VR Inicial', color='#3498db', alpha=0.9)
bars_vr_usado = ax.bar(x_pos, [-x for x in vr_usado_list], width, label='VR Usado', color='#e74c3c', alpha=0.9)
bars_vr_final = ax.bar(x_pos, [-x for x in vr_final_list], width, bottom=[-vr_usado_list[i] for i in range(len(T))],
                       label='VR Final (Sobrante)', color='#2ecc71', alpha=0.9)

# Etiquetas en las barras con porcentajes
for i, (inicial, usado, final) in enumerate(zip(vr_inicial_list, vr_usado_list, vr_final_list)):
    porcentaje_usado = (usado / inicial * 100) if inicial > 0 else 0
    ax.text(i, inicial/2, f'{porcentaje_usado:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_xlabel('Temporada', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('RIEGO: Inicial vs Usado vs Final', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(temporadas_list)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

# --- PANEL 2: GENERACIÓN (VG) ---
ax = axes[1]

# Barras invertidas
bars_vg_inicial = ax.bar(x_pos, vg_inicial_list, width, label='VG Inicial', color='#3498db', alpha=0.9)
bars_vg_usado = ax.bar(x_pos, [-x for x in vg_usado_list], width, label='VG Usado', color='#e74c3c', alpha=0.9)
bars_vg_final = ax.bar(x_pos, [-x for x in vg_final_list], width, bottom=[-vg_usado_list[i] for i in range(len(T))],
                       label='VG Final (Sobrante)', color='#2ecc71', alpha=0.9)

# Etiquetas en las barras con porcentajes
for i, (inicial, usado, final) in enumerate(zip(vg_inicial_list, vg_usado_list, vg_final_list)):
    porcentaje_usado = (usado / inicial * 100) if inicial > 0 else 0
    ax.text(i, inicial/2, f'{porcentaje_usado:.1f}%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_xlabel('Temporada', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title('GENERACIÓN: Inicial vs Usado vs Final', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(temporadas_list)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Análisis de Uso de Volúmenes Asignados por Temporada', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('graficos/10_analisis_uso_volumenes.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Grafico guardado: graficos/10_analisis_uso_volumenes.png")
plt.close()
