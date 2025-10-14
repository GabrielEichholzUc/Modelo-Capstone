"""
Script para cargar los parámetros desde el archivo Excel
"""

import pandas as pd
import numpy as np

def cargar_parametros_excel(archivo_excel="Modelo Capstone/Parametros_Finales.xlsx"): 
    """
    Carga todos los parámetros desde el archivo Excel
    
    Returns:
        dict: Diccionario con todos los parámetros del modelo
    """
    print("\n" + "="*60)
    print("CARGANDO PARÁMETROS DESDE EXCEL")
    print("="*60 + "\n")
    
    parametros = {}
    
    # 1. GENERALES (V_30Nov, V_0, V_MAX, psi, phi)
    print("Cargando parámetros generales...")
    df_generales = pd.read_excel(archivo_excel, sheet_name='Generales')
    
    # Leer valores de la primera columna como índice
    for _, row in df_generales.iterrows():
        param = str(row.iloc[0])
        if 'V_30Nov' in param:
            parametros['V_30Nov'] = float(row.iloc[1])
        elif 'V_0' in param or 'V_inicial' in param or 'Volumen inicial' in param:
            parametros['V_0'] = float(row.iloc[1])
        elif 'V_MAX' in param:
            parametros['V_MAX'] = float(row.iloc[1])
        elif 'psi' in param:
            parametros['psi'] = float(row.iloc[1])
        elif 'phi' in param:
            parametros['phi'] = float(row.iloc[1])
    
    print(f"  V_30Nov = {parametros.get('V_30Nov', 'N/A')} hm³")
    print(f"  V_0 = {parametros.get('V_0', 'N/A')} hm³")
    print(f"  V_MAX = {parametros.get('V_MAX', 'N/A')} hm³")
    print(f"  psi (incumplimiento) = {parametros.get('psi', 'N/A')} MWh")
    print(f"  phi (deficit) = {parametros.get('phi', 'N/A')} MWh")
    
    # 2. FC_k (Filtraciones por cota)
    print("\nCargando filtraciones FC_k...")
    df_fc = pd.read_excel(archivo_excel, sheet_name='FC_k')
    parametros['FC'] = {}
    
    # Detectar estructura de la tabla
    if 'k' in df_fc.columns and 'FC' in df_fc.columns:
        for _, row in df_fc.iterrows():
            k = int(row['k'])
            parametros['FC'][k] = float(row['FC'])
    elif df_fc.shape[1] >= 2:  # Primera columna k, segunda FC
        for _, row in df_fc.iterrows():
            if pd.notna(row.iloc[0]):
                k = int(row.iloc[0])
                parametros['FC'][k] = float(row.iloc[1])
    
    print(f"  Cargadas {len(parametros['FC'])} cotas")
    print(f"  Rango cotas: {min(parametros['FC'].keys())} - {max(parametros['FC'].keys())}")
    
    # 3. VC_k (Volumen por cota)
    print("\nCargando volúmenes VC_k...")
    df_vc = pd.read_excel(archivo_excel, sheet_name='VC_k')
    parametros['VC'] = {}
    
    if 'k' in df_vc.columns and 'VC' in df_vc.columns:
        for _, row in df_vc.iterrows():
            k = int(row['k'])
            parametros['VC'][k] = float(row['VC'])
    elif df_vc.shape[1] >= 2:
        for _, row in df_vc.iterrows():
            if pd.notna(row.iloc[0]):
                k = int(row.iloc[0])
                parametros['VC'][k] = float(row.iloc[1])
    
    print(f"  Cargados {len(parametros['VC'])} volúmenes")
    print(f"  Rango: {min(parametros['VC'].values()):.2f} - {max(parametros['VC'].values()):.2f} hm³")
    
    # 4. VUC_k,u (Volumen por uso y cota)
    print("\nCargando volúmenes por uso VUC_k,u...")
    df_vuc = pd.read_excel(archivo_excel, sheet_name='VUC_k,u')
    parametros['VUC'] = {}
    
    # Estructura: Cota | Riego | Generacion
    for _, row in df_vuc.iterrows():
        k = int(row['Cota'])
        parametros['VUC'][(1, k)] = float(row['Riego'])  # u=1 es riego
        parametros['VUC'][(2, k)] = float(row['Generacion'])  # u=2 es generación
    
    print(f"  Cargados {len(parametros['VUC'])} volúmenes de uso")
    
    # 5. QA_a,w (Afluentes)
    print("\nCargando afluentes QA_a,w...")
    df_qa = pd.read_excel(archivo_excel, sheet_name='QA_a,w', header=None)
    parametros['QA'] = {}
    
    # Estructura: Primera fila son los headers (fechas), segunda fila índice 'a'
    # Filas 2-6 son los afluentes (ELTORO, ABANICO, ANTUCO, TUCAPEL, CANECOL)
    # Columnas 1-240 son las semanas
    
    afluentes_nombres = ['ELTORO', 'ABANICO', 'ANTUCO', 'TUCAPEL', 'CANECOL']
    
    for idx_fila, nombre_afluente in enumerate(afluentes_nombres, start=2):
        a = idx_fila - 1  # a = 1 para ELTORO, 2 para ABANICO, etc.
        for w in range(1, 241):  # 240 semanas
            col_idx = w  # Las semanas están en columnas 1-240
            valor = df_qa.iloc[idx_fila, col_idx]
            parametros['QA'][(a, w)] = float(valor)
    
    print(f"  Cargados {len(parametros['QA'])} valores de afluentes")
    print(f"  Semanas: {min([w for a,w in parametros['QA'].keys()])} - {max([w for a,w in parametros['QA'].keys()])}")
    
    # 6. QD_d,j,w (Demandas de riego)
    print("\nCargando demandas de riego QD_d,j,w...")
    df_qd = pd.read_excel(archivo_excel, sheet_name='QD_d,j,w')
    parametros['QD'] = {}
    
    # Estructura: j | d | 1 | 2 | 3 | ... | 240
    # Cada fila tiene un j y d, y las columnas 1-240 son las semanas
    for _, row in df_qd.iterrows():
        j = int(row['j'])
        d = int(row['d'])
        for w in range(1, 241):  # 240 semanas
            # Intentar tanto con string como con número
            if w in df_qd.columns:
                parametros['QD'][(d, j, w)] = float(row[w])
            elif str(w) in df_qd.columns:
                parametros['QD'][(d, j, w)] = float(row[str(w)])
    
    print(f"  Cargados {len(parametros['QD'])} valores de demanda")
    
    # Mostrar algunas demandas de ejemplo
    ejemplos = [(1,1,1), (2,2,1), (3,3,33)]
    for d, j, w in ejemplos:
        if (d, j, w) in parametros['QD']:
            print(f"    QD[d={d},j={j},w={w}] = {parametros['QD'][(d,j,w)]} m³/s")
    
    # 7. Gamma_i (Caudal máximo por central)
    print("\nCargando caudales máximos Gamma_i...")
    df_gamma = pd.read_excel(archivo_excel, sheet_name='Gamma_i')
    parametros['gamma'] = {}
    
    if 'i' in df_gamma.columns and 'Gamma' in df_gamma.columns:
        for _, row in df_gamma.iterrows():
            i = int(row['i'])
            parametros['gamma'][i] = float(row['Gamma'])
    elif df_gamma.shape[1] >= 2:
        for _, row in df_gamma.iterrows():
            if pd.notna(row.iloc[0]):
                i = int(row.iloc[0])
                parametros['gamma'][i] = float(row.iloc[1])
    
    print(f"  Cargados {len(parametros['gamma'])} caudales máximos")
    
    # 8. Rho_i (Rendimiento por central)
    print("\nCargando rendimientos Rho_i...")
    df_rho = pd.read_excel(archivo_excel, sheet_name='Rho_i')
    parametros['rho'] = {}
    
    if 'i' in df_rho.columns and 'Rho' in df_rho.columns:
        for _, row in df_rho.iterrows():
            i = int(row['i'])
            parametros['rho'][i] = float(row['Rho'])
    elif df_rho.shape[1] >= 2:
        for _, row in df_rho.iterrows():
            if pd.notna(row.iloc[0]):
                i = int(row.iloc[0])
                parametros['rho'][i] = float(row.iloc[1])
    
    # Verificar que centrales de retiro tengan rho=0
    for i_retiro in [4, 12, 14]:
        if i_retiro not in parametros['rho']:
            parametros['rho'][i_retiro] = 0.0
        elif parametros['rho'][i_retiro] > 0:
            print(f"  ⚠ Advertencia: Central {i_retiro} es de retiro pero tiene rho={parametros['rho'][i_retiro]}")
    
    print(f"  Cargados {len(parametros['rho'])} rendimientos")
    
    # 9. Pi_i (Potencia máxima) - Si no está en el Excel, calcular desde gamma y rho
    print("\nConfigurando potencias máximas Pi_i...")
    parametros['pi'] = {}
    for i in range(1, 17):
        if i in parametros['gamma'] and i in parametros['rho']:
            parametros['pi'][i] = parametros['gamma'][i] * parametros['rho'][i]
        else:
            parametros['pi'][i] = 0.0
    
    print(f"  Calculadas {len(parametros['pi'])} potencias máximas")
    
    # 10. FS_w (Factor de segundos por semana)
    print("\nCargando factor de segundos FS_w...")
    df_fs = pd.read_excel(archivo_excel, sheet_name='FS_w')
    parametros['FS'] = {}
    
    # Estructura: w | s (segundos)
    for _, row in df_fs.iterrows():
        w = int(row['w'])
        parametros['FS'][w] = float(row['s'])
    
    print(f"  Cargados {len(parametros['FS'])} factores de segundos")
    
    # Contar semanas de 7 y 8 días
    semanas_7dias = sum(1 for v in parametros['FS'].values() if v == 604800)
    semanas_8dias = sum(1 for v in parametros['FS'].values() if v == 691200)
    print(f"    Semanas de 7 días: {semanas_7dias}")
    print(f"    Semanas de 8 días: {semanas_8dias}")
    
    print("\n" + "="*60)
    print("✓ PARÁMETROS CARGADOS EXITOSAMENTE")
    print("="*60 + "\n")
    
    return parametros

def mostrar_resumen(parametros):
    """
    Muestra un resumen de los parámetros cargados
    """
    print("\n" + "="*60)
    print("RESUMEN DE PARÁMETROS")
    print("="*60)
    
    print(f"\n Volúmenes del lago:")
    print(f"  - V_30Nov (medición 30 noviembre): {parametros.get('V_30Nov', 'N/A'):,.0f} hm³")
    print(f"  - V_0 (inicio temporada): {parametros.get('V_0', 'N/A'):,.0f} hm³")
    print(f"  - V_MAX: {parametros['V_MAX']:,.0f} hm³")
    
    print(f"\n Penalizaciones:")
    print(f"  - psi (incumplimiento): {parametros.get('psi', 'N/A'):,.0f} MWh")
    print(f"  - phi (déficit): {parametros.get('phi', 'N/A'):,.0f} MWh")
    
    print(f"\n Cotas del lago:")
    print(f"  - Total cotas: {len(parametros['VC'])}")
    print(f"  - Volumen min: {min(parametros['VC'].values()):,.2f} hm³")
    print(f"  - Volumen max: {max(parametros['VC'].values()):,.2f} hm³")
    
    print(f"\n Afluentes:")
    print(f"  - Total registros: {len(parametros['QA'])}")
    semanas = list(set([w for a,w in parametros['QA'].keys()]))
    print(f"  - Semanas: {min(semanas)} a {max(semanas)}")
    
    # Promedios por afluente
    for a in range(1, 6):
        afluente_nombre = ['El Toro', 'Abanico', 'Antuco', 'Tucapel', 'Canecol'][a-1]
        valores = [parametros['QA'][(a,w)] for w in semanas if (a,w) in parametros['QA']]
        if valores:
            print(f"  - {afluente_nombre} promedio: {np.mean(valores):.2f} m³/s")
    
    print(f"\n Demandas de riego:")
    print(f"  - Total registros: {len(parametros['QD'])}")
    
    print(f"\n Centrales:")
    print(f"  - Total centrales: {len(parametros['gamma'])}")
    centrales_generadoras = [i for i in parametros['rho'].keys() if parametros['rho'][i] > 0]
    print(f"  - Centrales generadoras: {len(centrales_generadoras)}")
    print(f"  - Centrales de retiro/paso: {16 - len(centrales_generadoras)}")
    
    # Top 3 centrales por capacidad
    capacidades = [(i, parametros['gamma'][i] * parametros['rho'][i]) for i in centrales_generadoras]
    capacidades.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  Top 3 por capacidad:")
    for i, cap in capacidades[:3]:
        print(f"    - Central {i}: {cap:.2f} MW")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Probar la carga de datos
    try:
        parametros = cargar_parametros_excel()
        mostrar_resumen(parametros)
        
        print("✓ Carga de datos exitosa")
        print("\nPuedes usar estos parámetros con:")
        print("  from cargar_datos import cargar_parametros_excel")
        print("  parametros = cargar_parametros_excel()")
        
    except Exception as e:
        print(f"\n✗ Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
