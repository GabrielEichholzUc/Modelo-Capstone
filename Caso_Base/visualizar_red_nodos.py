"""
Script para visualizar la red de nodos del sistema hídrico
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Configuración
fig = plt.figure(figsize=(24, 16))
ax = plt.gca()
ax.set_xlim(-1, 21)
ax.set_ylim(-1, 15)
ax.axis('off')

# Definir posiciones de nodos (x, y) - reorganizadas para mejor visualización
nodos_pos = {
    'Lago Laja': (2, 13),
    'ElToro': (2, 11),
    'Abanico': (6, 11),
    'Antuco': (6, 9),
    'RieZaco': (6, 7),
    'Canecol': (10, 11),
    'CanRucue': (10, 9),
    'CLajRucue': (10, 7),
    'Rucue': (13, 8),
    'Quilleco': (16, 8),
    'Tucapel': (16, 6),
    'CanalLaja': (16, 4),
    'Laja1': (19, 4),
    'ElDiuto': (19, 2),
    'RieTucapel': (19, 0.5),
}

# Afluentes (posiciones)
afluentes_pos = {
    'QA_Abanico': (6, 12.5),
    'QA_Antuco': (4, 9),
    'QA_Tucapel': (14, 6),
    'QA_Canecol': (10, 12.5),
    'QA_Laja1': (20.5, 4),
}

# Canales de riego (posiciones)
canales_pos = {
    'Canal RieZaco': (3, 7),
    'Canal RieTucapel': (20.5, 0.5),
    'Canal Abanico\n(medición)': (8.5, 11),
}

# Colores
color_nodo_central = '#3498db'  # Azul para centrales
color_nodo_juncion = '#95a5a6'  # Gris para junciones
color_afluente = '#27ae60'  # Verde para afluentes
color_canal_riego = '#e74c3c'  # Rojo para canales de riego
color_lago = '#1abc9c'  # Turquesa para el lago

# Función para dibujar nodo
def dibujar_nodo(pos, nombre, color, tipo='central'):
    x, y = pos
    if tipo == 'lago':
        # Lago como elipse grande
        elipse = mpatches.Ellipse((x, y), width=1.5, height=0.8, 
                                  color=color, alpha=0.8, ec='black', linewidth=2)
        ax.add_patch(elipse)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=11, fontweight='bold', color='white')
    elif tipo == 'afluente':
        # Afluente como triángulo
        triangle = mpatches.RegularPolygon((x, y), 3, radius=0.3,
                                          color=color, alpha=0.8, ec='black', linewidth=1.5)
        ax.add_patch(triangle)
        ax.text(x, y-0.6, nombre, ha='center', va='top', 
                fontsize=8, fontweight='bold', color=color)
    elif tipo == 'canal':
        # Canal de riego como rectángulo
        rect = FancyBboxPatch((x-0.5, y-0.3), 1.0, 0.6,
                             boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', 
                             linewidth=2, alpha=0.8)
        ax.add_patch(rect)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=8, fontweight='bold', color='white')
    else:
        # Nodo normal como rectángulo redondeado
        rect = FancyBboxPatch((x-0.4, y-0.25), 0.8, 0.5,
                             boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', 
                             linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=9, fontweight='bold', color='white')

# Función para dibujar flecha
def dibujar_flecha(pos1, pos2, label='', color='black', style='->'):
    arrow = FancyArrowPatch(pos1, pos2,
                           arrowstyle=style, mutation_scale=20,
                           linewidth=2, color=color, alpha=0.7)
    ax.add_patch(arrow)
    if label:
        mid_x = (pos1[0] + pos2[0]) / 2
        mid_y = (pos1[1] + pos2[1]) / 2
        ax.text(mid_x, mid_y, label, ha='center', va='bottom',
                fontsize=7, color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

# Dibujar lago
dibujar_nodo(nodos_pos['Lago Laja'], 'Lago\nLaja', color_lago, tipo='lago')

# Dibujar nodos (centrales y junciones)
centrales = ['ElToro', 'Abanico', 'Antuco', 'CanRucue', 'CLajRucue', 
             'Rucue', 'Quilleco', 'Tucapel', 'CanalLaja', 'Laja1', 'ElDiuto', 'Canecol']
junciones = ['RieZaco', 'RieTucapel']

for nodo in centrales:
    dibujar_nodo(nodos_pos[nodo], nodo, color_nodo_central)

for nodo in junciones:
    dibujar_nodo(nodos_pos[nodo], nodo, color_nodo_juncion)

# Dibujar afluentes
for afluente, pos in afluentes_pos.items():
    nombre = afluente.replace('QA_', 'QA\n')
    dibujar_nodo(pos, nombre, color_afluente, tipo='afluente')

# Dibujar canales de riego
for canal, pos in canales_pos.items():
    dibujar_nodo(pos, canal, color_canal_riego, tipo='canal')

# Dibujar conexiones principales (flujo de generación qg y qv)
conexiones = [
    # Desde Lago
    ('Lago Laja', 'ElToro', 'qer+qeg'),
    
    # Flujo principal
    ('ElToro', 'Antuco', 'qg[1]'),
    ('Abanico', 'Antuco', 'qg[2]'),
    ('Antuco', 'RieZaco', 'qg[3]+qv[3]'),
    ('Canecol', 'CanRucue', 'qg[5]+qv[5]'),
    ('CanRucue', 'Rucue', 'qg[6]'),
    ('CLajRucue', 'Rucue', 'qg[7]'),
    ('Rucue', 'Quilleco', 'qg[8]+qv[8]'),
    ('Quilleco', 'Tucapel', 'qg[9]+qv[9]'),
    ('Tucapel', 'CanalLaja', 'qg[10]+qv[10]'),
    ('CanalLaja', 'Laja1', 'qv[11]'),
    ('CanalLaja', 'ElDiuto', 'qg[11]'),
    ('Laja1', 'RieTucapel', 'qg[13]+qv[13]'),
    ('ElDiuto', 'RieTucapel', 'qg[15]+qv[15]'),
    
    # Vertimientos
    ('RieZaco', 'CLajRucue', 'qv[4]'),
    ('CanRucue', 'Rucue', 'qv[6]'),
]

for origen, destino, label in conexiones:
    pos1 = nodos_pos[origen]
    pos2 = nodos_pos[destino]
    # Ajustar puntos de inicio y fin para que no se solapen con los nodos
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.5 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, label, color='#2c3e50')

# Conexiones de afluentes
afluentes_conexiones = [
    ('QA_Abanico', 'Abanico', 'QA[2]'),
    ('QA_Antuco', 'Antuco', 'QA[3]'),
    ('QA_Tucapel', 'Tucapel', 'QA[4]'),
    ('QA_Canecol', 'Canecol', 'QA[5]'),
    ('QA_Laja1', 'Laja1', 'QA[6]'),
]

for afluente, destino, label in afluentes_conexiones:
    pos1 = afluentes_pos[afluente]
    pos2 = nodos_pos[destino]
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.4 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, '', color=color_afluente)

# Conexiones de canales de riego
riego_conexiones = [
    ('RieZaco', 'Canal RieZaco', 'qp[1]'),
    ('RieTucapel', 'Canal RieTucapel', 'qp[2]'),
    ('Abanico', 'Canal Abanico\n(medición)', 'qp[4]'),
]

for origen, destino, label in riego_conexiones:
    pos1 = nodos_pos[origen]
    pos2 = canales_pos[destino]
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.5 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, label, color=color_canal_riego, style='->')

# Flecha de filtraciones desde Lago a Abanico
dibujar_flecha((nodos_pos['Lago Laja'][0]+0.5, nodos_pos['Lago Laja'][1]-0.4), 
               (nodos_pos['Abanico'][0]-0.4, nodos_pos['Abanico'][1]+0.25),
               'qf', color='#9b59b6', style='->')

# Leyenda
legend_elements = [
    mpatches.Patch(facecolor=color_nodo_central, edgecolor='black', label='Centrales Hidroeléctricas'),
    mpatches.Patch(facecolor=color_nodo_juncion, edgecolor='black', label='Nodos de Junción'),
    mpatches.Patch(facecolor=color_lago, edgecolor='black', label='Lago Laja (Embalse)'),
    mpatches.Patch(facecolor=color_afluente, edgecolor='black', label='Afluentes'),
    mpatches.Patch(facecolor=color_canal_riego, edgecolor='black', label='Canales de Riego'),
]

ax.legend(handles=legend_elements, loc='upper left', fontsize=12, 
         framealpha=0.95, edgecolor='black', fancybox=True)

# Título
plt.title('Red de Nodos del Sistema Hídrico - Lago Laja', 
         fontsize=20, fontweight='bold', pad=25)

# Notas
ax.text(10, 14.2, 'Sistema de centrales hidroeléctricas y canales de riego', 
       ha='center', fontsize=12, style='italic', color='#34495e')

# Guardar
plt.tight_layout(pad=2.0)
plt.savefig('graficos/red_nodos_sistema.png', dpi=300, bbox_inches='tight', 
            facecolor='white', pad_inches=0.5)
print("✓ Gráfico de red de nodos guardado: graficos/red_nodos_sistema.png")
plt.close()

print("\n" + "="*70)
print("NODOS DEL SISTEMA:")
print("="*70)
print("\nCentrales Hidroeléctricas:")
print("  1. El Toro - Extracción desde Lago Laja")
print("  2. Abanico - Recibe filtraciones del lago")
print("  3. Antuco - Punto de convergencia")
print("  4. CanRucue - En río Laja")
print("  5. CLajRucue - Canal Laja Rucue")
print("  6. Rucue - Convergencia")
print("  7. Quilleco")
print("  8. Tucapel")
print("  9. CanalLaja")
print(" 10. Laja1")
print(" 11. ElDiuto")
print(" 12. Canecol")

print("\nNodos de Junción:")
print("  - RieZaco - Distribución hacia riego primeros regantes")
print("  - RieTucapel - Distribución hacia riego segundos regantes")

print("\nAfluentes:")
print("  - QA[2]: Abanico")
print("  - QA[3]: Antuco")
print("  - QA[4]: Tucapel")
print("  - QA[5]: Canecol")
print("  - QA[6]: Laja I")

print("\nCanales de Riego:")
print("  - Canal RieZaco [j=1] - Primeros Regantes")
print("  - Canal RieTucapel [j=2] - Segundos Regantes + Saltos del Laja")
print("  - Canal Abanico [j=4] - Alternativa a Tucapel (variable α)")

print("\n" + "="*70)
"""
Script para visualizar la red de nodos del sistema hídrico
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Configuración
fig = plt.figure(figsize=(24, 16))
ax = plt.gca()
ax.set_xlim(-1, 21)
ax.set_ylim(-1, 15)
ax.axis('off')

# Definir posiciones de nodos (x, y) - reorganizadas para mejor visualización
nodos_pos = {
    'Lago Laja': (2, 13),
    'ElToro': (2, 11),
    'Abanico': (6, 11),
    'Antuco': (6, 9),
    'RieZaco': (6, 7),
    'Canecol': (10, 11),
    'CanRucue': (10, 9),
    'CLajRucue': (10, 7),
    'Rucue': (13, 8),
    'Quilleco': (16, 8),
    'Tucapel': (16, 6),
    'CanalLaja': (16, 4),
    'Laja1': (19, 4),
    'ElDiuto': (19, 2),
    'RieTucapel': (19, 0.5),
}

# Afluentes (posiciones)
afluentes_pos = {
    'QA_Abanico': (6, 12.5),
    'QA_Antuco': (4, 9),
    'QA_Tucapel': (14, 6),
    'QA_Canecol': (10, 12.5),
    'QA_Laja1': (20.5, 4),
}

# Canales de riego (posiciones)
canales_pos = {
    'Canal RieZaco': (3, 7),
    'Canal RieTucapel': (20.5, 0.5),
    'Canal Abanico\n(medición)': (8.5, 11),
}

# Colores
color_nodo_central = '#3498db'  # Azul para centrales
color_nodo_juncion = '#95a5a6'  # Gris para junciones
color_afluente = '#27ae60'  # Verde para afluentes
color_canal_riego = '#e74c3c'  # Rojo para canales de riego
color_lago = '#1abc9c'  # Turquesa para el lago

# Función para dibujar nodo
def dibujar_nodo(pos, nombre, color, tipo='central'):
    x, y = pos
    if tipo == 'lago':
        # Lago como elipse grande
        elipse = mpatches.Ellipse((x, y), width=1.5, height=0.8, 
                                  color=color, alpha=0.8, ec='black', linewidth=2)
        ax.add_patch(elipse)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=11, fontweight='bold', color='white')
    elif tipo == 'afluente':
        # Afluente como triángulo
        triangle = mpatches.RegularPolygon((x, y), 3, radius=0.3,
                                          color=color, alpha=0.8, ec='black', linewidth=1.5)
        ax.add_patch(triangle)
        ax.text(x, y-0.6, nombre, ha='center', va='top', 
                fontsize=8, fontweight='bold', color=color)
    elif tipo == 'canal':
        # Canal de riego como rectángulo
        rect = FancyBboxPatch((x-0.5, y-0.3), 1.0, 0.6,
                             boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', 
                             linewidth=2, alpha=0.8)
        ax.add_patch(rect)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=8, fontweight='bold', color='white')
    else:
        # Nodo normal como rectángulo redondeado
        rect = FancyBboxPatch((x-0.4, y-0.25), 0.8, 0.5,
                             boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', 
                             linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x, y, nombre, ha='center', va='center', 
                fontsize=9, fontweight='bold', color='white')

# Función para dibujar flecha
def dibujar_flecha(pos1, pos2, label='', color='black', style='->'):
    arrow = FancyArrowPatch(pos1, pos2,
                           arrowstyle=style, mutation_scale=20,
                           linewidth=2, color=color, alpha=0.7)
    ax.add_patch(arrow)
    if label:
        mid_x = (pos1[0] + pos2[0]) / 2
        mid_y = (pos1[1] + pos2[1]) / 2
        ax.text(mid_x, mid_y, label, ha='center', va='bottom',
                fontsize=7, color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

# Dibujar lago
dibujar_nodo(nodos_pos['Lago Laja'], 'Lago\nLaja', color_lago, tipo='lago')

# Dibujar nodos (centrales y junciones)
centrales = ['ElToro', 'Abanico', 'Antuco', 'CanRucue', 'CLajRucue', 
             'Rucue', 'Quilleco', 'Tucapel', 'CanalLaja', 'Laja1', 'ElDiuto', 'Canecol']
junciones = ['RieZaco', 'RieTucapel']

for nodo in centrales:
    dibujar_nodo(nodos_pos[nodo], nodo, color_nodo_central)

for nodo in junciones:
    dibujar_nodo(nodos_pos[nodo], nodo, color_nodo_juncion)

# Dibujar afluentes
for afluente, pos in afluentes_pos.items():
    nombre = afluente.replace('QA_', 'QA\n')
    dibujar_nodo(pos, nombre, color_afluente, tipo='afluente')

# Dibujar canales de riego
for canal, pos in canales_pos.items():
    dibujar_nodo(pos, canal, color_canal_riego, tipo='canal')

# Dibujar conexiones principales (flujo de generación qg y qv)
conexiones = [
    # Desde Lago
    ('Lago Laja', 'ElToro', 'qer+qeg'),
    
    # Flujo principal
    ('ElToro', 'Antuco', 'qg[1]'),
    ('Abanico', 'Antuco', 'qg[2]'),
    ('Antuco', 'RieZaco', 'qg[3]+qv[3]'),
    ('Canecol', 'CanRucue', 'qg[5]+qv[5]'),
    ('CanRucue', 'Rucue', 'qg[6]'),
    ('CLajRucue', 'Rucue', 'qg[7]'),
    ('Rucue', 'Quilleco', 'qg[8]+qv[8]'),
    ('Quilleco', 'Tucapel', 'qg[9]+qv[9]'),
    ('Tucapel', 'CanalLaja', 'qg[10]+qv[10]'),
    ('CanalLaja', 'Laja1', 'qv[11]'),
    ('CanalLaja', 'ElDiuto', 'qg[11]'),
    ('Laja1', 'RieTucapel', 'qg[13]+qv[13]'),
    ('ElDiuto', 'RieTucapel', 'qg[15]+qv[15]'),
    
    # Vertimientos
    ('RieZaco', 'CLajRucue', 'qv[4]'),
    ('CanRucue', 'Rucue', 'qv[6]'),
]

for origen, destino, label in conexiones:
    pos1 = nodos_pos[origen]
    pos2 = nodos_pos[destino]
    # Ajustar puntos de inicio y fin para que no se solapen con los nodos
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.5 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, label, color='#2c3e50')

# Conexiones de afluentes
afluentes_conexiones = [
    ('QA_Abanico', 'Abanico', 'QA[2]'),
    ('QA_Antuco', 'Antuco', 'QA[3]'),
    ('QA_Tucapel', 'Tucapel', 'QA[4]'),
    ('QA_Canecol', 'Canecol', 'QA[5]'),
    ('QA_Laja1', 'Laja1', 'QA[6]'),
]

for afluente, destino, label in afluentes_conexiones:
    pos1 = afluentes_pos[afluente]
    pos2 = nodos_pos[destino]
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.4 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, '', color=color_afluente)

# Conexiones de canales de riego
riego_conexiones = [
    ('RieZaco', 'Canal RieZaco', 'qp[1]'),
    ('RieTucapel', 'Canal RieTucapel', 'qp[2]'),
    ('Abanico', 'Canal Abanico\n(medición)', 'qp[4]'),
]

for origen, destino, label in riego_conexiones:
    pos1 = nodos_pos[origen]
    pos2 = canales_pos[destino]
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    offset = 0.5 / dist
    pos1_adj = (pos1[0] + dx*offset, pos1[1] + dy*offset)
    pos2_adj = (pos2[0] - dx*offset, pos2[1] - dy*offset)
    dibujar_flecha(pos1_adj, pos2_adj, label, color=color_canal_riego, style='->')

# Flecha de filtraciones desde Lago a Abanico
dibujar_flecha((nodos_pos['Lago Laja'][0]+0.5, nodos_pos['Lago Laja'][1]-0.4), 
               (nodos_pos['Abanico'][0]-0.4, nodos_pos['Abanico'][1]+0.25),
               'qf', color='#9b59b6', style='->')

# Leyenda
legend_elements = [
    mpatches.Patch(facecolor=color_nodo_central, edgecolor='black', label='Centrales Hidroeléctricas'),
    mpatches.Patch(facecolor=color_nodo_juncion, edgecolor='black', label='Nodos de Junción'),
    mpatches.Patch(facecolor=color_lago, edgecolor='black', label='Lago Laja (Embalse)'),
    mpatches.Patch(facecolor=color_afluente, edgecolor='black', label='Afluentes'),
    mpatches.Patch(facecolor=color_canal_riego, edgecolor='black', label='Canales de Riego'),
]

ax.legend(handles=legend_elements, loc='upper left', fontsize=12, 
         framealpha=0.95, edgecolor='black', fancybox=True)

# Título
plt.title('Red de Nodos del Sistema Hídrico - Lago Laja', 
         fontsize=20, fontweight='bold', pad=25)

# Notas
ax.text(10, 14.2, 'Sistema de centrales hidroeléctricas y canales de riego', 
       ha='center', fontsize=12, style='italic', color='#34495e')

# Guardar
plt.tight_layout(pad=2.0)
plt.savefig('graficos/red_nodos_sistema.png', dpi=300, bbox_inches='tight', 
            facecolor='white', pad_inches=0.5)
print("✓ Gráfico de red de nodos guardado: graficos/red_nodos_sistema.png")
plt.close()

print("\n" + "="*70)
print("NODOS DEL SISTEMA:")
print("="*70)
print("\nCentrales Hidroeléctricas:")
print("  1. El Toro - Extracción desde Lago Laja")
print("  2. Abanico - Recibe filtraciones del lago")
print("  3. Antuco - Punto de convergencia")
print("  4. CanRucue - En río Laja")
print("  5. CLajRucue - Canal Laja Rucue")
print("  6. Rucue - Convergencia")
print("  7. Quilleco")
print("  8. Tucapel")
print("  9. CanalLaja")
print(" 10. Laja1")
print(" 11. ElDiuto")
print(" 12. Canecol")

print("\nNodos de Junción:")
print("  - RieZaco - Distribución hacia riego primeros regantes")
print("  - RieTucapel - Distribución hacia riego segundos regantes")

print("\nAfluentes:")
print("  - QA[2]: Abanico")
print("  - QA[3]: Antuco")
print("  - QA[4]: Tucapel")
print("  - QA[5]: Canecol")
print("  - QA[6]: Laja I")

print("\nCanales de Riego:")
print("  - Canal RieZaco [j=1] - Primeros Regantes")
print("  - Canal RieTucapel [j=2] - Segundos Regantes + Saltos del Laja")
print("  - Canal Abanico [j=4] - Alternativa a Tucapel (variable α)")

print("\n" + "="*70)