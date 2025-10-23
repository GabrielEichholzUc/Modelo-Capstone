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
volumenes = pd.read_csv('resultados_caso_base/volumenes_lago.csv')
riego = pd.read_csv('resultados_caso_base/riego.csv')
generacion = pd.read_csv('resultados_caso_base/generacion.csv')
energia_total = pd.read_csv('resultados_caso_base/energia_total.csv')

# Intentar cargar decision_alpha.csv (solo existe en modelo MIP)
try:
    alpha = pd.read_csv('resultados_caso_base/decision_alpha.csv')
    tiene_alpha = True
    print(f"✓ decision_alpha.csv encontrado (modelo MIP)")
except FileNotFoundError:
    alpha = None
    tiene_alpha = False
    print(f"⚠ decision_alpha.csv no encontrado (caso base LP - sin variables alpha)")

# Intentar cargar volúmenes por uso
try:
    volumenes_uso = pd.read_csv('resultados_caso_base/volumenes_por_uso.csv')
    print(f"✓ Datos cargados: {len(volumenes)} volúmenes lago, {len(riego)} riego, {len(volumenes_uso)} volúmenes por uso, {len(generacion)} generación, {len(energia_total)} GEN[i,t]")
except FileNotFoundError:
    volumenes_uso = None
    print(f"✓ Datos cargados: {len(volumenes)} volúmenes lago, {len(riego)} riego, {len(generacion)} generación, {len(energia_total)} GEN[i,t]")
    print("  ⚠ Archivo volumenes_por_uso.csv no encontrado (ejecuta optimización primero)")

# Cargar parámetros para obtener V_min
try:
    from cargar_datos_5temporadas import cargar_parametros_excel
    parametros = cargar_parametros_excel('Parametros_Finales_Base.xlsx')
    V_min = parametros.get('V_min', 1400)
    print(f"✓ V_min cargado: {V_min} hm³")
except:
    V_min = 1400
    print(f"⚠ No se pudo cargar V_min, usando valor por defecto: {V_min} hm³")

# Parámetros del modelo
T = list(range(1, 6))  # 5 temporadas
W = list(range(1, 49))  # 48 semanas
U = [1, 2]  # Usos: 1=Riego, 2=Generación
J = [1, 2, 3, 4]  # Canales: 1=RieZaCo, 2=RieTucapel, 3=RieSaltos, 4=Abanico
D = [1, 2, 3]  # Demandantes: 1=Primeros, 2=Segundos, 3=Saltos del Laja

nombres_usos = {1: 'Riego', 2: 'Generación'}
nombres_canales = {1: 'RieZaCo', 2: 'RieTucapel', 3: 'RieSaltos', 4: 'Abanico'}
nombres_demandantes = {1: 'Primeros Regantes', 2: 'Segundos Regantes', 3: 'Saltos del Laja'}

print(f"✓ Datos cargados: {len(volumenes)} registros de volúmenes, {len(riego)} de riego")

# ============================================================
# GRÁFICO 1: EVOLUCIÓN V[w,t] - TODAS LAS TEMPORADAS JUNTAS
# ============================================================

print("\n📊 Generando gráfico 1: Volumen lago (todas temporadas agregadas)...")

fig, ax = plt.subplots(figsize=(20, 8))

# Plotear cada temporada una al lado de la otra
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for t in T:
    data_t = volumenes[volumenes['Temporada'] == t]
    # Offset: posicionar cada temporada en su propio bloque de semanas
    x_offset = (t - 1) * 48
    semanas = data_t['Semana'].values + x_offset
    
    ax.plot(semanas, data_t['Volumen_hm3'], 
            linewidth=2, color=colors[t-1], label=f'Temporada {t}', marker='', alpha=0.9)

# Línea horizontal del volumen mínimo
ax.axhline(y=V_min, color='red', linestyle='-.', linewidth=2, alpha=0.7, 
           label=f'V_min = {V_min:.0f} hm³')

# Líneas verticales para separar temporadas
for t in range(1, 5):
    semana_fin = t * 48
    ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)

# Añadir etiquetas de temporadas en el eje x
ax.set_xticks([24, 72, 120, 168, 216])
ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'], fontsize=11, fontweight='bold')

# Eje x secundario con semanas
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(np.arange(0, 241, 48))
ax2.set_xticklabels([f'{i*48}' for i in range(6)], fontsize=9)
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
# GRÁFICO 3: EVOLUCIÓN ve[u,w,t] - TODAS LAS TEMPORADAS JUNTAS
# ============================================================

print("📊 Generando gráfico 3: Volúmenes por uso (todas temporadas agregadas)...")

if volumenes_uso is not None:
    fig, ax = plt.subplots(figsize=(20, 8))

    # Plotear cada uso con color diferente
    colors_usos = {1: '#e74c3c', 2: '#3498db'}  # Rojo para riego, azul para generación
    
    for u in U:
        data_u = volumenes_uso[volumenes_uso['Uso'] == u]
        
        for t in T:
            data_t = data_u[data_u['Temporada'] == t]
            if len(data_t) == 0:
                continue
            
            x_offset = (t - 1) * 48
            semanas = data_t['Semana'].values + x_offset
            volumen = data_t['Volumen_hm3'].values
            
            # Solo mostrar label en la primera temporada
            label = f'{nombres_usos[u]}' if t == 1 else ''
            ax.plot(semanas, volumen, 
                    linewidth=2.5, color=colors_usos[u], label=label, 
                    marker='', alpha=0.85)

    # Líneas verticales para separar temporadas
    for t in range(1, 5):
        semana_fin = t * 48
        ax.axvline(x=semana_fin, color='gray', linestyle='--', alpha=0.4, linewidth=1.5)

    # Añadir etiquetas de temporadas
    ax.set_xticks([24, 72, 120, 168, 216])
    ax.set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'], fontsize=11, fontweight='bold')

    ax.set_xlabel('Temporadas', fontsize=12, fontweight='bold')
    ax.set_ylabel('Volumen por Uso (hm³)', fontsize=12, fontweight='bold')
    ax.set_title('Evolución de Volúmenes por Uso - Temporadas Agregadas', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=12, loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/3_volumenes_uso_todas_temporadas.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Guardado: {output_dir}/3_volumenes_uso_todas_temporadas.png")
    plt.close()
else:
    print("  ⚠ Saltando gráfico 3: no hay datos de volúmenes por uso")

# Gráfico 4 omitido por solicitud del usuario

# ============================================================
# GRÁFICO 5: DEMANDA VS PROVISIÓN - TODAS LAS TEMPORADAS
# ============================================================

print("📊 Generando gráfico 5: Demanda vs Provisión (todas temporadas agregadas)...")

# Cargar demandas del Excel
try:
    demandas = pd.read_excel('Parametros_Finales_Base.xlsx', sheet_name='QD_d,j,w')
except:
    print("  ⚠ No se pudo cargar QD_d,j,w, usando valores de riego.csv")
    demandas = None

# Agregar alpha al dataframe de riego (solo si existe)
if tiene_alpha:
    riego_alpha = riego.merge(alpha, on=['Semana', 'Temporada'], how='left')
    riego_alpha['Alpha'] = riego_alpha['Alpha'].fillna(0)
else:
    # Caso base: no hay alpha, crear columna con 0 (por defecto Tucapel)
    riego_alpha = riego.copy()
    riego_alpha['Alpha'] = 0

# Crear columna 'Incumplimiento' si no existe (para caso base)
if 'Incumplimiento' not in riego_alpha.columns:
    # Incumplimiento = 1 si hay déficit > 0
    riego_alpha['Incumplimiento'] = (riego_alpha['Deficit_m3s'] > 0.01).astype(int)

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
            ax.plot(semanas, provision_vals, linewidth=2, color=colors_provision[t-1], 
                    label=label_p, alpha=0.8)
        
        # Líneas verticales para separar temporadas
        for t in range(1, 5):
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
    axes[-1].set_xticks([24, 72, 120, 168, 216])
    axes[-1].set_xticklabels(['T1', 'T2', 'T3', 'T4', 'T5'], fontsize=11, fontweight='bold')
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
nombres_centrales = cargar_nombres_centrales('Parametros_Finales_Base.xlsx')
print(f"  Nombres de centrales cargados: {len(nombres_centrales)} centrales")

# Cargar datos de rendimiento para filtrar centrales con rho > 0
parametros = cargar_parametros_excel('Parametros_Finales_Base.xlsx')
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
width = 0.15  # Ancho de cada barra
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for idx_t, temp in enumerate(temporadas):
    offset = width * (idx_t - 2)  # Centrar las barras
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
# RESUMEN
# ============================================================

print("\n" + "="*70)
print("✅ VISUALIZACIÓN COMPLETADA")
print("="*70)
print(f"\nGráficos generados en carpeta: {output_dir}/")
print("\nGráficos generados:")
print("  1. Volumen lago - Todas las temporadas juntas")
print("  2. Volumen lago - Por temporada (5 gráficos)")
print("  3. Volúmenes por uso - Todas las temporadas juntas")
print("  4. Volúmenes por uso - Por temporada (2 usos × 5 temporadas)")
print("  5. Demanda vs Provisión - Por canal, todas las temporadas")
print("  6. Demanda vs Provisión - Por canal, demandante y temporada")
print("  7. Generación por central y temporada (barras agrupadas)")
print("\n" + "="*70)
