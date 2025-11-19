"""
Script para cargar los parámetros desde el archivo Excel
Versión para 5 temporadas
"""

import pandas as pd
import numpy as np

def cargar_nombres_centrales(archivo_excel="Parametros_Finales.xlsx"):
    """
    Carga los nombres de las centrales desde la hoja Índices
    
    Returns:
        dict: Diccionario {i: nombre_central} para i=1..16
    """
    df_indices = pd.read_excel(archivo_excel, sheet_name='Índices')
    
    # Extraer columnas de Centrales (asumiendo que están en las dos primeras columnas)
    centrales_df = df_indices[['Centrales', 'Unnamed: 1']].dropna()
    
    # Filtrar solo las filas donde la primera columna es numérica (índice de central)
    centrales_df = centrales_df[centrales_df['Centrales'].apply(lambda x: isinstance(x, (int, float)))]
    
    # Limitar a las primeras 16 centrales
    centrales_df = centrales_df.head(16)
    
    # Crear diccionario
    nombres = {}
    for _, row in centrales_df.iterrows():
        idx = int(row['Centrales'])
        nombre = str(row['Unnamed: 1']).strip()
        nombres[idx] = nombre
    
    return nombres

def cargar_parametros_excel(archivo_excel="Parametros_Finales.xlsx"): 
    """
    Carga todos los parámetros desde el archivo Excel para modelo de 5 temporadas
    
    Returns:
        dict: Diccionario con todos los parámetros del modelo
    """
    print("\n" + "="*60)
    print("CARGANDO PARÁMETROS DESDE EXCEL")
    print("="*60 + "\n")
    
    parametros = {}
    
    # 1. GENERALES (V_30Nov_1, V_0, V_MIN, V_MAX, V_F, psi, nu)
    print("Cargando parámetros generales...")
    df_generales = pd.read_excel(archivo_excel, sheet_name='Generales')
    
    # Leer valores de la primera columna como índice
    for _, row in df_generales.iterrows():
        param = str(row.iloc[0])
        if 'V_30Nov' in param or 'V_30_Nov' in param:
            parametros['V_30Nov_1'] = float(row.iloc[1])
        elif 'V_0' in param or 'V_inicial' in param or 'Volumen inicial' in param:
            parametros['V_0'] = float(row.iloc[1])
        elif 'V_MAX' in param:
            parametros['V_MAX'] = float(row.iloc[1])
        elif 'V_MIN' in param or 'V_min' in param:
            parametros['V_MIN'] = float(row.iloc[1])
        elif 'V_F' in param or 'V_final' in param:
            parametros['V_F'] = float(row.iloc[1])
        elif 'psi' in param:
            parametros['psi'] = float(row.iloc[1])  # [GWh]
        elif 'nu' in param or 'phi' in param:
            parametros['nu'] = float(row.iloc[1])  # [GWh] - nu en LaTeX
        elif 'M' in param and 'MAX' not in param and 'MIN' not in param and 'V_' not in param:
            parametros['M'] = float(row.iloc[1])
    
    print(f"  V_30Nov_1 = {parametros.get('V_30Nov_1', 'N/A')} hm³")
    print(f"  V_0 = {parametros.get('V_0', 'N/A')} hm³")
    print(f"  V_MIN = {parametros.get('V_MIN', 'N/A')} hm³")
    print(f"  V_MAX = {parametros.get('V_MAX', 'N/A')} hm³")
    print(f"  V_F = {parametros.get('V_F', 'N/A')} hm³")
    print(f"  psi (incumplimiento) = {parametros.get('psi', 'N/A')} GWh")
    print(f"  nu (umbral V_MIN/V_MAX) = {parametros.get('nu', 'N/A')} GWh")
    print(f"  M (Big-M) = {parametros.get('M', 'N/A')}")
    
    # 2. FC_k (Filtraciones por zona)
    print("\nCargando filtraciones f_k...")
    df_fk = pd.read_excel(archivo_excel, sheet_name='FC_k')
    parametros['FC'] = {}  # Se mantiene FC internamente para compatibilidad
    
    if 'k' in df_fk.columns and 'f_k' in df_fk.columns:
        for _, row in df_fk.iterrows():
            k = int(row['k'])
            parametros['FC'][k] = float(row['f_k'])
    elif df_fk.shape[1] >= 2:
        for _, row in df_fk.iterrows():
            if pd.notna(row.iloc[0]):
                k = int(row.iloc[0])
                parametros['FC'][k] = float(row.iloc[1])
    
    print(f"  Cargadas {len(parametros['FC'])} zonas")
    print(f"  Rango zonas: {min(parametros['FC'].keys())} - {max(parametros['FC'].keys())}")
    
    # 3. VC_k (Volumen por zona)
    print("\nCargando volúmenes v_k...")
    df_vk = pd.read_excel(archivo_excel, sheet_name='VC_k')
    parametros['VC'] = {}  # Se mantiene VC internamente para compatibilidad
    
    if 'k' in df_vk.columns and 'v_k' in df_vk.columns:
        for _, row in df_vk.iterrows():
            k = int(row['k'])
            parametros['VC'][k] = float(row['v_k'])
    elif df_vk.shape[1] >= 2:
        for _, row in df_vk.iterrows():
            if pd.notna(row.iloc[0]):
                k = int(row.iloc[0])
                parametros['VC'][k] = float(row.iloc[1])
    
    print(f"  Cargados {len(parametros['VC'])} volúmenes")
    print(f"  Rango: {min(parametros['VC'].values()):.2f} - {max(parametros['VC'].values()):.2f} hm³")
    
    # 4. VUC_k,u (Volumen por uso y zona) - ahora en una sola hoja
    print("\nCargando volúmenes por uso vr_k y vg_k...")
    df_vuc = pd.read_excel(archivo_excel, sheet_name='VUC_k,u')
    parametros['VUC'] = {}
    
    # Asumiendo formato: k | vr_k (u=1) | vg_k (u=2)
    if 'k' in df_vuc.columns:
        for _, row in df_vuc.iterrows():
            k = int(row['k'])
            if 'vr_k' in df_vuc.columns:
                parametros['VUC'][(1, k)] = float(row['vr_k'])
            if 'vg_k' in df_vuc.columns:
                parametros['VUC'][(2, k)] = float(row['vg_k'])
    else:
        # Formato por columnas: primera col=k, segunda col=vr_k, tercera col=vg_k
        for _, row in df_vuc.iterrows():
            if pd.notna(row.iloc[0]):
                k = int(row.iloc[0])
                if df_vuc.shape[1] >= 2 and pd.notna(row.iloc[1]):
                    parametros['VUC'][(1, k)] = float(row.iloc[1])
                if df_vuc.shape[1] >= 3 and pd.notna(row.iloc[2]):
                    parametros['VUC'][(2, k)] = float(row.iloc[2])
    
    print(f"  Cargados {len(parametros['VUC'])} volúmenes de uso")
    
    # 5. QA_a,w,t (Afluentes por semana y temporada - 6 afluentes)
    print("\nCargando afluentes QA_a,w,t...")
    parametros['QA'] = {}
    
    # Nombres de afluentes
    afluentes_nombres = {
        1: 'ELTORO',
        2: 'ABANICO', 
        3: 'ANTUCO',
        4: 'TUCAPEL',
        5: 'CANECOL',
        6: 'LAJA_I'
    }
    
    # Leer datos desde hoja única QA_a,w,t
    try:
        sheet_name = 'QA_a,w,t'
        df_qa = pd.read_excel(archivo_excel, sheet_name=sheet_name, header=None)
        print(f"  Leyendo desde hoja '{sheet_name}'...")
        
        # Estructura: 
        # Fila 0-1: encabezados
        # Columna 0: temporada (t)
        # Columna 1: nombre afluente
        # Columnas 2-49: semanas 1-48
        # Filas: 6 afluentes por temporada (ELTORO, ABANICO, ANTUCO, TUCAPEL, CANECOL, LAJA_I)
        
        # Mapeo de nombres de afluentes a índices
        afluentes_map = {
            'ELTORO': 1,
            'ABANICO': 2,
            'ANTUCO': 3,
            'TUCAPEL': 4,
            'CANECOL': 5,
            'LAJA_I': 6  # Sexto afluente
        }
        
        # Leer desde fila 2 en adelante (saltando encabezados)
        for row_idx in range(2, df_qa.shape[0]):
            try:
                # Leer temporada y nombre del afluente
                t = int(df_qa.iloc[row_idx, 0])
                nombre_afluente = str(df_qa.iloc[row_idx, 1]).strip().upper()
                
                # Obtener índice del afluente
                if nombre_afluente in afluentes_map:
                    a = afluentes_map[nombre_afluente]
                    
                    # Cargar todos los afluentes (1-6)
                    # Leer las 48 semanas (columnas 2-49)
                    for w in range(1, 49):
                        col_idx = w + 1  # Columna 2 = semana 1, ..., columna 49 = semana 48
                        try:
                            valor = df_qa.iloc[row_idx, col_idx]
                            parametros['QA'][(a, w, t)] = float(valor) if pd.notna(valor) else 0.0
                        except:
                            parametros['QA'][(a, w, t)] = 0.0
            except Exception as e:
                continue
        
        # Contar cuántas temporadas se cargaron
        temporadas_cargadas = set()
        afluentes_cargados = set()
        for (a, w, t) in parametros['QA'].keys():
            temporadas_cargadas.add(t)
            afluentes_cargados.add(a)
        
        for t in sorted(temporadas_cargadas):
            print(f"  ✓ Cargada temporada {t}")
        
        # Mostrar afluentes cargados
        afluentes_nombres_map = {1: 'ELTORO', 2: 'ABANICO', 3: 'ANTUCO', 4: 'TUCAPEL', 5: 'CANECOL', 6: 'LAJA_I'}
        print(f"  ✓ Afluentes cargados ({len(afluentes_cargados)}): ", end="")
        print(", ".join([f"{a}:{afluentes_nombres_map[a]}" for a in sorted(afluentes_cargados)]))
            
    except Exception as e:
        print(f"  ⚠ Error cargando hoja 'QA_a,w,t': {e}")
        # Si falla, llenar con ceros
        for t in range(1, 6):
            for a in range(1, 7):  # Ahora incluye afluente 6
                for w in range(1, 49):
                    parametros['QA'][(a, w, t)] = 0.0
    
    print(f"  Total cargados: {len(parametros['QA'])} valores de afluentes")
    print(f"  Afluentes: 1-6, Semanas: 1-48, Temporadas: 1-5")
    
    # Mostrar ejemplos
    print(f"  Ejemplo QA[a=1,w=1,t=1] = {parametros['QA'][(1,1,1)]:.2f} m³/s")
    print(f"  Ejemplo QA[a=2,w=1,t=1] = {parametros['QA'][(2,1,1)]:.2f} m³/s")
    if (6, 1, 1) in parametros['QA']:
        print(f"  Ejemplo QA[a=6,w=1,t=1] (LAJA_I) = {parametros['QA'][(6,1,1)]:.2f} m³/s")
    
    # 6. QD_d,j,w (Demandas de riego - sin temporada, se repite cada año)
    print("\nCargando demandas de riego QD_d,j,w...")
    df_qd = pd.read_excel(archivo_excel, sheet_name='QD_d,j,w')
    parametros['QD'] = {}
    
    # Estructura: j | d | 1 | 2 | 3 | ... | 48
    for _, row in df_qd.iterrows():
        j = int(row['j'])
        d = int(row['d'])
        for w in range(1, 49):  # 48 semanas
            # Intentar leer el valor
            try:
                if w in df_qd.columns:
                    valor = float(row[w])
                elif str(w) in df_qd.columns:
                    valor = float(row[str(w)])
                else:
                    valor = 0.0
                parametros['QD'][(d, j, w)] = valor
            except:
                parametros['QD'][(d, j, w)] = 0.0
    
    print(f"  Cargados {len(parametros['QD'])} valores de demanda")
    
    # Mostrar ejemplos
    if (1, 1, 1) in parametros['QD']:
        print(f"    QD[d=1,j=1,w=1] = {parametros['QD'][(1,1,1)]:.2f} m³/s")
    if (1, 4, 1) in parametros['QD']:
        print(f"    QD[d=1,j=4,w=1] (Abanico) = {parametros['QD'][(1,4,1)]:.2f} m³/s")
    
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
    
    # 8. Rho_i (Rendimiento por central - Potencia específica)
    print("\nCargando rendimientos Rho_i...")
    df_rho = pd.read_excel(archivo_excel, sheet_name='Rho_i')
    parametros['rho'] = {}
    
    if 'i' in df_rho.columns and 'Rho' in df_rho.columns:
        for _, row in df_rho.iterrows():
            i = int(row['i'])
            parametros['rho'][i] = float(row['Rho'])  # Unidades: MW/(m³/s)
    elif df_rho.shape[1] >= 2:
        for _, row in df_rho.iterrows():
            if pd.notna(row.iloc[0]):
                i = int(row.iloc[0])
                parametros['rho'][i] = float(row.iloc[1])  # Unidades: MW/(m³/s)
    
    # Verificar que centrales de retiro tengan rho=0
    for i_retiro in [4, 12, 14]:
        if i_retiro not in parametros['rho']:
            parametros['rho'][i_retiro] = 0.0
        elif parametros['rho'][i_retiro] > 0:
            print(f"  ⚠ Advertencia: Central {i_retiro} es de retiro pero tiene rho={parametros['rho'][i_retiro]}")
    
    print(f"  Cargados {len(parametros['rho'])} rendimientos")
    
    # 9. Pi_i (Potencia máxima)
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
    
    # Estructura: w | FS (segundos)
    if 'w' in df_fs.columns and 'FS' in df_fs.columns:
        for _, row in df_fs.iterrows():
            w = int(row['w'])
            parametros['FS'][w] = float(row['FS'])
    elif df_fs.shape[1] >= 2:
        for _, row in df_fs.iterrows():
            if pd.notna(row.iloc[0]):
                w = int(row.iloc[0])
                parametros['FS'][w] = float(row.iloc[1])
    
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
    print("RESUMEN DE PARÁMETROS - 5 TEMPORADAS")
    print("="*60)
    
    print(f"\n📊 Volúmenes del lago:")
    print(f"  - V_30Nov_1 (previo a temp 1): {parametros.get('V_30Nov_1', 'N/A'):,.0f} hm³")
    print(f"  - V_0 (inicio planificación): {parametros.get('V_0', 'N/A'):,.0f} hm³")
    print(f"  - V_MAX: {parametros['V_MAX']:,.0f} hm³")
    
    print(f"\n💰 Penalizaciones:")
    print(f"  - psi (incumplimiento): {parametros.get('psi', 'N/A'):,.0f} GWh")
    print(f"  - phi (déficit): {parametros.get('phi', 'N/A'):,.0f} GWh")
    
    print(f"\n📏 Cotas del lago:")
    print(f"  - Total cotas: {len(parametros['VC'])}")
    print(f"  - Volumen min: {min(parametros['VC'].values()):,.2f} hm³")
    print(f"  - Volumen max: {max(parametros['VC'].values()):,.2f} hm³")
    
    print(f"\n🌊 Afluentes (QA):")
    print(f"  - Total registros: {len(parametros['QA'])}")
    print(f"  - Afluentes: 1-6 (El Toro, Abanico, Antuco, Tucapel, Canecol, Laja I)")
    print(f"  - Semanas por temporada: 48")
    print(f"  - Temporadas: 5")
    
    # Promedios por afluente y temporada
    afluentes_nombres = ['El Toro', 'Abanico', 'Antuco', 'Tucapel', 'Canecol', 'Laja I']
    for t in range(1, 6):
        print(f"\n  Temporada {t}:")
        for a in range(1, 7):  # Ahora incluye el afluente 6
            valores = [parametros['QA'][(a, w, t)] for w in range(1, 49) if (a, w, t) in parametros['QA']]
            if valores:
                print(f"    - {afluentes_nombres[a-1]}: promedio {np.mean(valores):.2f} m³/s")
    
    print(f"\n🚰 Demandas de riego (QD):")
    print(f"  - Total registros: {len(parametros['QD'])}")
    print(f"  - Canales: 4 (RieZaCo=1, RieTucapel=2, RieSaltos=3, Abanico=4)")
    print(f"  - Demandantes: 3 (Primeros=1, Segundos=2, Saltos del Laja=3)")
    
    print(f"\n⚡ Centrales:")
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
        
        print("✅ Carga de datos exitosa")
        print("\nPuedes usar estos parámetros con:")
        print("  from cargar_datos_5temporadas import cargar_parametros_excel")
        print("  parametros = cargar_parametros_excel()")
        
    except Exception as e:
        print(f"\n❌ Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
