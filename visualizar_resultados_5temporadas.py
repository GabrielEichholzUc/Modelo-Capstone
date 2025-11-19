"""
Script para visualizar resultados del modelo de optimización - 5 temporadas
Genera gráficos de:
- Evolución de volúmenes del lago V[w,t]
- Evolución de volúmenes por uso ve[u,w,t]
- Comparación demanda vs provisión de riego con indicador alpha
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import os

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

# Detectar automáticamente el número de temporadas desde los datos
NUM_TEMPORADAS = volumenes['Temporada'].max()
T = list(range(1, NUM_TEMPORADAS + 1))
T_5 = list(range(1, 6))  # Para gráficos comparativos de 5 años
W = list(range(1, 49))  # 48 semanas
U = [1, 2]  # Usos: 1=Riego, 2=Generación
J = [1, 2, 3, 4]  # Canales: 1=RieZaCo, 2=RieTucapel, 3=RieSaltos, 4=Abanico
D = [1, 2, 3]  # Demandantes: 1=Primeros, 2=Segundos, 3=Saltos del Laja

nombres_usos = {1: 'Riego', 2: 'Generación'}
nombres_canales = {1: 'RieZaCo', 2: 'RieTucapel', 3: 'RieSaltos', 4: 'Abanico'}
nombres_demandantes = {1: 'Primeros Regantes', 2: 'Segundos Regantes', 3: 'Saltos del Laja'}

print(f"✓ Datos cargados: {len(volumenes)} registros de volúmenes, {len(riego)} de riego")
print(f"✓ Temporadas detectadas: {NUM_TEMPORADAS}")

# ============================================================
# GRÁFICO 1: EVOLUCIÓN V[w,t] - TODAS LAS TEMPORADAS JUNTAS
# ============================================================

print("\n📊 Generando gráfico 1: Volumen lago (todas temporadas agregadas)...")

# Colores para las temporadas
colors_10 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# --- GRÁFICO 1A: 5 TEMPORADAS (truncado) ---
if NUM_TEMPORADAS >= 5:
    fig, ax = plt.subplots(figsize=(20, 8))
    
    for t in T_5:
        data_t = volumenes[volumenes['Temporada'] == t]
        x_offset = (t - 1) * 48
        semanas = data_t['Semana'].values + x_offset
        
        ax.plot(semanas, data_t['Volumen_hm3'], 
                linewidth=2, color=colors_10[t-1], label=f'Temporada {t}', marker='', alpha=0.9)

    ax.axhline(y=V_MIN, color='red', linestyle='-.', linewidth=2, alpha=0.7, 
               label=f'V_MIN = {V_MIN:.0f} hm³')
    ax.axhline(y=V_MAX, color='orange', linestyle='-.', linewidth=2, alpha=0.7, 
               label=f'V_MAX = {V_MAX:.0f} hm³')

    for t in range(1, 5):
        ax.axvline(x=t * 48, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)

    ax.set_xticks([24, 72, 120, 168, 216])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'], fontsize=11, fontweight='bold')

    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(np.arange(0, 241, 48))
    ax2.set_xticklabels([f'{i*48}' for i in range(6)], fontsize=9)
    ax2.set_xlabel('Semana Global', fontsize=10)

    ax.set_xlabel('Temporadas', fontsize=12, fontweight='bold')
    ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
    ax.set_title('Evolución del Volumen del Lago Laja - Primeras 5 Temporadas', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='best', ncol=5)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/1a_volumen_lago_5_temporadas.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/1a_volumen_lago_5_temporadas.png (vista 5 años)")
    plt.close()

# --- GRÁFICO 1B: TODAS LAS TEMPORADAS (10 años completo) ---
fig, ax = plt.subplots(figsize=(24, 8))

for t in T:
    data_t = volumenes[volumenes['Temporada'] == t]
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    
    ax.plot(semanas, data_t['Volumen_hm3'], 
            linewidth=2, color=colors_10[t-1] if t <= 10 else colors_10[t % 10], 
            label=f'Temporada {t}', marker='', alpha=0.9)

ax.axhline(y=V_MIN, color='red', linestyle='-.', linewidth=2, alpha=0.7, 
           label=f'V_MIN = {V_MIN:.0f} hm³')
ax.axhline(y=V_MAX, color='orange', linestyle='-.', linewidth=2, alpha=0.7, 
           label=f'V_MAX = {V_MAX:.0f} hm³')

for t in range(1, NUM_TEMPORADAS):
    ax.axvline(x=t * 48, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)

xticks_pos = [24 + i*48 for i in range(NUM_TEMPORADAS)]
xticks_labels = [f'T{i+1}' for i in range(NUM_TEMPORADAS)]
ax.set_xticks(xticks_pos)
ax.set_xticklabels(xticks_labels, fontsize=11, fontweight='bold')

ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(np.arange(0, NUM_TEMPORADAS*48 + 1, 48))
ax2.set_xticklabels([f'{i*48}' for i in range(NUM_TEMPORADAS + 1)], fontsize=9)
ax2.set_xlabel('Semana Global', fontsize=10)

ax.set_xlabel('Temporadas', fontsize=12, fontweight='bold')
ax.set_ylabel('Volumen (hm³)', fontsize=12, fontweight='bold')
ax.set_title(f'Evolución del Volumen del Lago Laja - Todas las Temporadas ({NUM_TEMPORADAS} años)', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(fontsize=10, loc='best', ncol=min(NUM_TEMPORADAS, 10))
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/1b_volumen_lago_todas_temporadas.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/1b_volumen_lago_todas_temporadas.png (vista completa {NUM_TEMPORADAS} años)")
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
        
        color_idx = (t-1) if (t-1) < 10 else (t-1) % 10
        ax.scatter(semanas, zonas, alpha=0.6, s=30, 
                  color=colors_10[color_idx], label=f'Temporada {t}')
    
    # Líneas verticales para separar temporadas
    for t in range(1, NUM_TEMPORADAS):
        semana_fin = t * 48
        ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)
    
    xticks_pos = [24 + i*48 for i in range(NUM_TEMPORADAS)]
    xticks_labels = [f'T{i+1}' for i in range(NUM_TEMPORADAS)]
    ax.set_xticks(xticks_pos)
    ax.set_xticklabels(xticks_labels, fontsize=11, fontweight='bold')
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
        colors_demanda = ['#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c']  # Rojo
        colors_provision = ['#27ae60', '#2ecc71', '#16a085', '#1abc9c', '#0e6655']  # Verdes
        
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
            color_idx = (t-1) if (t-1) < len(colors_provision) else (t-1) % len(colors_provision)
            ax.plot(semanas, provision_vals, linewidth=2, color=colors_provision[color_idx], 
                    label=label_p, alpha=0.8)
        
        # Líneas verticales para separar temporadas
        for t in range(1, NUM_TEMPORADAS):
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
    xticks_pos = [24 + i*48 for i in range(NUM_TEMPORADAS)]
    xticks_labels = [f'T{i+1}' for i in range(NUM_TEMPORADAS)]
    axes[-1].set_xticks(xticks_pos)
    axes[-1].set_xticklabels(xticks_labels, fontsize=11, fontweight='bold')
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
        # Crear suficientes subplots para todas las temporadas (2 filas × ceil(NUM_TEMPORADAS/2) columnas)
        ncols = 5 if NUM_TEMPORADAS <= 10 else 6
        nrows = (NUM_TEMPORADAS + ncols - 1) // ncols  # Redondear hacia arriba
        fig, axes = plt.subplots(nrows, ncols, figsize=(3.6*ncols, 5*nrows))
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
        
        # Ocultar subplots vacíos (si NUM_TEMPORADAS no llena todas las posiciones)
        for idx in range(NUM_TEMPORADAS, len(axes)):
            axes[idx].axis('off')
        
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
temporadas_todas = sorted(energia_filtrada['Temporada'].unique())

# --- GRÁFICO 7A: 5 TEMPORADAS ---
if NUM_TEMPORADAS >= 5:
    print("  Generando versión 5 temporadas...")
    temporadas_5 = [t for t in temporadas_todas if t <= 5]
    
    data_matrix_5 = np.zeros((len(centrales), len(temporadas_5)))
    for idx_c, central in enumerate(centrales):
        for idx_t, temp in enumerate(temporadas_5):
            valor = energia_filtrada[
                (energia_filtrada['Central'] == central) & 
                (energia_filtrada['Temporada'] == temp)
            ]['Energia_GWh'].values
            if len(valor) > 0:
                data_matrix_5[idx_c, idx_t] = valor[0]

    fig, ax = plt.subplots(figsize=(16, 8))
    x = np.arange(len(centrales))
    width = 0.15
    colors_5 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for idx_t, temp in enumerate(temporadas_5):
        offset = width * (idx_t - 2)
        ax.bar(x + offset, data_matrix_5[:, idx_t], width, 
               label=f'Temporada {temp}', color=colors_5[idx_t], alpha=0.85)

    ax.set_xlabel('Central', fontsize=12, fontweight='bold')
    ax.set_ylabel('Energía Generada (GWh)', fontsize=12, fontweight='bold')
    ax.set_title('Energía Generada por Central - Primeras 5 Temporadas\n(Solo centrales con rendimiento > 0)', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([nombres_centrales[c] for c in centrales], rotation=45, ha='right')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/7a_generacion_5_temporadas.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/7a_generacion_5_temporadas.png (vista 5 años)")
    plt.close()

# --- GRÁFICO 7B: TODAS LAS TEMPORADAS ---
print(f"  Generando versión {NUM_TEMPORADAS} temporadas...")
data_matrix_all = np.zeros((len(centrales), len(temporadas_todas)))
for idx_c, central in enumerate(centrales):
    for idx_t, temp in enumerate(temporadas_todas):
        valor = energia_filtrada[
            (energia_filtrada['Central'] == central) & 
            (energia_filtrada['Temporada'] == temp)
        ]['Energia_GWh'].values
        if len(valor) > 0:
            data_matrix_all[idx_c, idx_t] = valor[0]

fig, ax = plt.subplots(figsize=(18, 8))
x = np.arange(len(centrales))
width = 0.8 / NUM_TEMPORADAS  # Ajustar ancho según número de temporadas
colors_all = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

for idx_t, temp in enumerate(temporadas_todas):
    offset = width * (idx_t - NUM_TEMPORADAS/2 + 0.5)
    color_idx = idx_t if idx_t < 10 else idx_t % 10
    ax.bar(x + offset, data_matrix_all[:, idx_t], width, 
           label=f'T{temp}', color=colors_all[color_idx], alpha=0.85)

ax.set_xlabel('Central', fontsize=12, fontweight='bold')
ax.set_ylabel('Energía Generada (GWh)', fontsize=12, fontweight='bold')
ax.set_title(f'Energía Generada por Central - Todas las Temporadas ({NUM_TEMPORADAS} años)\n(Solo centrales con rendimiento > 0)', 
             fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([nombres_centrales[c] for c in centrales], rotation=45, ha='right')
ax.legend(fontsize=9, loc='best', ncol=min(NUM_TEMPORADAS, 5))
ax.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/7b_generacion_todas_temporadas.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Guardado: {output_dir}/7b_generacion_todas_temporadas.png (vista completa {NUM_TEMPORADAS} años)")
plt.close()

# ============================================================
# RESUMEN
# ============================================================

print("\n" + "="*70)
print("✅ VISUALIZACIÓN COMPLETADA")
print("="*70)
print(f"\nGráficos generados en carpeta: {output_dir}/")
print(f"\nNúmero de temporadas: {NUM_TEMPORADAS}")
print("\nGráficos generados:")
if NUM_TEMPORADAS >= 5:
    print("  1a. Volumen lago - Primeras 5 temporadas (comparativa)")
print(f"  1b. Volumen lago - Todas las temporadas ({NUM_TEMPORADAS} años)")
print(f"  2. Volumen lago - Por temporada ({NUM_TEMPORADAS} gráficos)")
print(f"  3. Volúmenes por uso - Todas las temporadas juntas")
print(f"  4. Volúmenes por uso - Por temporada (2 usos × {NUM_TEMPORADAS} temporadas)")
print("  5. Demanda vs Provisión - Por canal, todas las temporadas")
print(f"  6. Demanda vs Provisión - Por canal, demandante y temporada")
if NUM_TEMPORADAS >= 5:
    print("  7a. Generación por central - Primeras 5 temporadas (comparativa)")
print(f"  7b. Generación por central - Todas las temporadas ({NUM_TEMPORADAS} años)")
print("\n" + "="*70)
