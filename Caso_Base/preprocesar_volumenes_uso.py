"""
Script de preprocesamiento para calcular volúmenes disponibles por uso
según las reglas del Convenio del Lago Laja
"""

import numpy as np
import pandas as pd
from openpyxl import load_workbook

def calcular_volumenes_iniciales_por_uso(V_30Nov_valores, FS_dict):
    """
    Calcula los volúmenes disponibles iniciales por uso para cada temporada
    según las curvas por tramos del Convenio del Lago Laja.
    
    Parámetros del Convenio:
    - VG_max = 820 hm³ (Volumen máximo para generación)
    - VR_max = 1520 hm³ (Volumen máximo para riego)
    - V_umbral_min = 3650 hm³ (Umbral mínimo)
    - V_umbral_max = 6300 hm³ (Umbral máximo)
    
    Reglas:
    1. Si V30Nov ≤ 3650 → VG = 0, VR = 0
    2. Si 3650 < V30Nov ≤ 6300 → VG = aG * (V30Nov - 3650), VR = aR * (V30Nov - 3650)
    3. Si V30Nov > 6300 → VG = VG_max, VR = VR_max
    
    donde:
    - aG = VG_max / (6300 - 3650) = 820 / 2650 ≈ 0.3094
    - aR = VR_max / (6300 - 3650) = 1520 / 2650 ≈ 0.5736
    
    Args:
        V_30Nov_valores: dict con {t: volumen_30Nov} para cada temporada t
        FS_dict: dict con {w: segundos} para cada semana w
    
    Returns:
        dict con:
        - 've_0': {(u, t): volumen} - Volúmenes iniciales por uso [hm³]
        - 'VG': {t: volumen} - Volumen para generación por temporada [hm³]
        - 'VR': {t: volumen} - Volumen para riego por temporada [hm³]
    """
    
    # Parámetros del convenio
    VG_max = 820.0  # hm³
    VR_max = 1520.0  # hm³
    V_umbral_min = 3650.0  # hm³
    V_umbral_max = 6300.0  # hm³
    
    # Coeficientes de las rectas
    aG = VG_max / (V_umbral_max - V_umbral_min)  # ≈ 0.3094
    aR = VR_max / (V_umbral_max - V_umbral_min)  # ≈ 0.5736
    
    print("\n" + "="*70)
    print("PREPROCESAMIENTO: CÁLCULO DE VOLÚMENES DISPONIBLES POR USO")
    print("="*70)
    print(f"\nParámetros del Convenio del Lago Laja:")
    print(f"  - VG_max (Generación): {VG_max:,.0f} hm³")
    print(f"  - VR_max (Riego): {VR_max:,.0f} hm³")
    print(f"  - V_umbral_min: {V_umbral_min:,.0f} hm³")
    print(f"  - V_umbral_max: {V_umbral_max:,.0f} hm³")
    print(f"  - Coeficiente aG: {aG:.6f}")
    print(f"  - Coeficiente aR: {aR:.6f}")
    
    # Diccionarios de resultados
    ve_0 = {}  # ve_0[t]: Volumen total extraíble por temporada (VG + VR)
    ve_0_por_uso = {}  # ve_0_por_uso[(u, t)]: Volumen inicial disponible para uso u en temporada t
    VG = {}    # VG[t]: Volumen anual para generación en temporada t
    VR = {}    # VR[t]: Volumen anual para riego en temporada t
    
    print("\n" + "-"*70)
    print("Cálculo por temporada:")
    print("-"*70)
    
    for t, V_30Nov in V_30Nov_valores.items():
        print(f"\nTemporada {t}:")
        print(f"  V_30Nov[{t}] = {V_30Nov:,.2f} hm³")
        # Integrar cálculo por tramos usando la función dedicada
        # Preparar valores previos si existen
        V_rini_k = V_30Nov
        V_rini_k_minus1 = None
        VG_prev = None
        if (t - 1) in V_30Nov_valores:
            V_rini_k_minus1 = V_30Nov_valores.get(t - 1)
        if (t - 1) in VG:
            VG_prev = VG.get(t - 1)

        # Parámetros adicionales (pueden provenir de FS_dict o parámetros externos)
        V_mixto = 0.0
        T_TRANS = 0
        VG_INI = None
        VR_INI = None

        # Calcular usando la función por tramos
        vg_calc, vr_calc = calcular_VG_VR_por_tramos(
            V_rini_k=V_rini_k,
            V_rini_k_minus1=V_rini_k_minus1,
            V_mixto=V_mixto,
            t=t,
            T_TRANS=T_TRANS,
            k=t,
            VG_prev=VG_prev,
            VG_INI=VG_INI,
            VR_INI=VR_INI
        )

        # Si la función devolvió None para k==1 o faltó información, aplicar reglas del convenio original
        if vg_calc is None or vr_calc is None:
            if V_30Nov <= V_umbral_min:
                vg_calc = 0.0
                vr_calc = 0.0
                print(f"  → Caso 1 (fallback): V_30Nov ≤ {V_umbral_min:,.0f} hm³")
            elif V_30Nov <= V_umbral_max:
                vg_calc = aG * (V_30Nov - V_umbral_min)
                vr_calc = aR * (V_30Nov - V_umbral_min)
                print(f"  → Caso 2 (fallback): {V_umbral_min:,.0f} < V_30Nov ≤ {V_umbral_max:,.0f} hm³")
            else:
                vg_calc = VG_max
                vr_calc = VR_max
                print(f"  → Caso 3 (fallback): V_30Nov > {V_umbral_max:,.0f} hm³")

        # Asignar resultados
        VG[t] = vg_calc
        VR[t] = vr_calc
        print(f"  → VG[{t}] = {VG[t]:,.2f} hm³")
        print(f"  → VR[{t}] = {VR[t]:,.2f} hm³")
        # Almacenar por uso (compatibilidad) y total
        ve_0_por_uso[(1, t)] = VR[t]  # u=1 es riego
        ve_0_por_uso[(2, t)] = VG[t]  # u=2 es generación
        # ve_0 principal = total extraíble (VG + VR) por temporada
        ve_0[t] = VG[t] + VR[t]

        print(f"  → ve_0_por_uso[u=1 (riego), t={t}] = {ve_0_por_uso[(1, t)]:,.2f} hm³")
        print(f"  → ve_0_por_uso[u=2 (generación), t={t}] = {ve_0_por_uso[(2, t)]:,.2f} hm³")
        print(f"  → Total extraíble temporada {t}: {ve_0[t]:,.2f} hm³")
    
    print("\n" + "="*70)
    print("RESUMEN DE VOLÚMENES DISPONIBLES")
    print("="*70)
    
    # Crear tabla resumen
    data_resumen = []
    for t in sorted(V_30Nov_valores.keys()):
        data_resumen.append({
            'Temporada': t,
            'V_30Nov (hm³)': V_30Nov_valores[t],
            'VR - Riego (hm³)': VR[t],
            'VG - Generación (hm³)': VG[t],
            'Total Extraíble (hm³)': VG[t] + VR[t],
            '% de VR_max': (VR[t] / VR_max * 100) if VR_max > 0 else 0,
            '% de VG_max': (VG[t] / VG_max * 100) if VG_max > 0 else 0
        })
    
    df_resumen = pd.DataFrame(data_resumen)
    print("\n" + df_resumen.to_string(index=False))
    
    print("\n" + "="*70 + "\n")
    
    return {
        # ve_0: mapa temporada -> volumen total extraíble (VG + VR) [hm³]
        've_0': ve_0,
        # ve_0_por_uso: compatibilidad, mantiene (u,t) -> volumen por uso
        've_0_por_uso': ve_0_por_uso,
        'VG': VG,      # {t: volumen en hm³}
        'VR': VR       # {t: volumen en hm³}
    }


def preprocesar_volumenes_uso_desde_parametros(parametros):
    """
    Preprocesa los volúmenes disponibles por uso desde el diccionario de parámetros.
    
    Esta función debe llamarse DESPUÉS de cargar los parámetros y ANTES de construir el modelo.
    
    Args:
        parametros: dict con los parámetros del modelo (debe incluir 'V_30Nov_1' y 'FS')
    
    Returns:
        dict: Parámetros actualizados con 've_0' calculado
    """
    
    # Obtener V_30Nov para cada temporada
    # Nota: En este caso solo tenemos V_30Nov_1 como parámetro
    # Las demás V_30Nov se calcularán durante la optimización
    # Por ahora, usaremos V_30Nov_1 para todas las temporadas como aproximación inicial
    
    V_30Nov_1 = parametros.get('V_30Nov_1')
    
    # Para el preprocesamiento, asumimos que todas las temporadas tendrán 
    # un valor similar a V_30Nov_1 (esto es solo para cálculo inicial)
    # En la práctica, V_30Nov[t] se determinará durante la optimización
    
    V_30Nov_valores = {
        1: V_30Nov_1,
        2: V_30Nov_1,  # Aproximación inicial
        3: V_30Nov_1,  # Aproximación inicial
        4: V_30Nov_1,  # Aproximación inicial
        5: V_30Nov_1   # Aproximación inicial
    }
    
    # Calcular volúmenes disponibles
    resultados = calcular_volumenes_iniciales_por_uso(V_30Nov_valores, parametros['FS'])
    
    # Agregar al diccionario de parámetros
    # IMPORTANTE: Usar ve_0_por_uso para tener los valores separados por uso (u, t)
    parametros['ve_0_precalculado'] = resultados['ve_0_por_uso']
    parametros['VG_por_temporada'] = resultados['VG']
    parametros['VR_por_temporada'] = resultados['VR']
    
    return parametros


def calcular_VG_VR_por_tramos(V_rini_k,
                               V_rini_k_minus1=None,
                               V_mixto=0.0,
                               t=999,
                               T_TRANS=0,
                               k=1,
                               VG_prev=None,
                               VG_INI=None,
                               VR_INI=None):
    """
    Calcula VG_{s,k,m} y VR_{s,k,m} según las reglas por tramos descritas en el Convenio.

    Entradas (nombres consistentes con la formulación matemática):
    - V_rini_k: volumen inicial de la temporada k (V_{rini,k}) [hm3]
    - V_rini_k_minus1: volumen inicial de la temporada k-1 (si está disponible)
    - V_mixto: V_{mixto} (corrige el tramo inicial)
    - t: índice temporal absoluto (se compara con T_TRANS)
    - T_TRANS: umbral temporal para transición
    - k: índice de temporada (si k == 1 se usan VG_INI/VR_INI)
    - VG_prev: VG_{s,k-1,rini} (valor previo de VG, usado en la fórmula cuando corresponde)
    - VG_INI, VR_INI: valores iniciales para k == 1

    Salidas:
    - VG: volumen de derechos de generación (hm3), ya limitado a 1200
    - VR: volumen de derechos de riego (hm3)

    Reglas implementadas (precedencia):
    1) Si k == 1 -> devuelve VG_INI y VR_INI (si están dados, si no, None)
    2) Si t <= T_TRANS o V_rini_k <= 1370: VR = 570 + V_mixto; para VG se usa la fórmula
       recursiva VG_prev + 0.1*(V_rini_k - V_rini_k_minus1) si VG_prev y V_rini_k_minus1 están disponibles,
       si no, se cae a la evaluación por tramos estándar.
    3) En otro caso se evalúan las funciones por tramos según V_rini_k.

    Nota: los intervalos se consideran inclusivos en los límites tal como en la formulación.
    """

    # Validaciones mínimas
    try:
        V = float(V_rini_k)
    except Exception:
        raise ValueError("V_rini_k debe ser convertible a float")

    # Caso k == 1: usar valores iniciales si se proporcionan
    if k == 1:
        return (VG_INI, VR_INI)

    # Inicializar
    VG = None
    VR = None

    # Si t <= T_TRANS o V_rini_k <= 1370: regla especial
    if (t <= T_TRANS) or (V <= 1370):
        # VR según la especificación
        VR = 570.0 + float(V_mixto)

        # VG recursivo si hay información previa
        if (VG_prev is not None) and (V_rini_k_minus1 is not None):
            VG = float(VG_prev) + 0.1 * (float(V_rini_k) - float(V_rini_k_minus1))
        else:
            # Si no hay valores previos disponibles, caer al cálculo por tramos según V
            pass

    # Si VG o VR no fueron asignados por las reglas anteriores, calcular por tramos
    # Cálculo de VG por tramos
    if VG is None:
        if 0 <= V <= 1200:
            VG = 0.05 * V + (30.0 - float(V_mixto))
        elif 1200 <= V <= 1370:
            VG = 60.0 + 0.05 * (V - 1200.0)
        elif 1370 <= V <= 1900:
            VG = 68.5 + 0.40 * (V - 1370.0)
        elif 1900 <= V <= 5582:
            VG = 280.5 + 0.65 * (V - 1900.0)
        else:
            # Fuera de rango superior: extrapolar con el último tramo
            VG = 280.5 + 0.65 * max(0.0, (V - 1900.0))

    # Aplicar límite máximo para VG
    VG = min(VG, 1200.0)

    # Cálculo de VR por tramos (si no fue fijado por la regla t <= T_TRANS o V <= 1370)
    if VR is None:
        if 0 <= V <= 1200:
            VR = 570.0 + float(V_mixto)
        elif 1200 <= V <= 1370:
            VR = 600.0 + 0.40 * (V - 1200.0)
        elif 1370 <= V <= 1900:
            VR = 668.0 + 0.40 * (V - 1370.0)
        elif 1900 <= V <= 5582:
            VR = 880.0 + 0.25 * (V - 1900.0)
        else:
            # Fuera de rango superior: extrapolar con el último tramo
            VR = 880.0 + 0.25 * max(0.0, (V - 1900.0))

    return (float(VG), float(VR))


def guardar_ve_0_en_excel(ve_0, archivo_excel="Parametros_Finales.xlsx"):
    """
    Guarda los volúmenes iniciales precalculados en el archivo Excel
    
    Args:
        ve_0: dict {(u, t): volumen} con los volúmenes calculados
        archivo_excel: nombre del archivo Excel donde guardar
    """
    # Crear DataFrame
    data = []
    # Soportar dos formatos de entrada:
    # 1) ve_0 como {(u, t): valor} (compatibilidad antigua)
    # 2) ve_0 como {t: valor_total} (nuevo formato: total VG+VR por temporada)
    sample_key = None
    try:
        sample_key = next(iter(ve_0.keys()))
    except StopIteration:
        sample_key = None

    if sample_key is None:
        # vacío
        pass
    elif isinstance(sample_key, tuple):
        for (u, t), valor in sorted(ve_0.items()):
            uso_nombre = "Riego" if u == 1 else "Generación"
            data.append({
                'Uso': u,
                'Uso_Nombre': uso_nombre,
                'Temporada': t,
                'VE_0': valor
            })
    else:
        # Se asume que las claves son temporadas (enteros)
        for t, valor in sorted(ve_0.items()):
            data.append({
                'Uso': 0,
                'Uso_Nombre': 'Total',
                'Temporada': t,
                'VE_0': valor
            })
    
    df = pd.DataFrame(data)
    
    try:
        # Intentar cargar el workbook existente de forma segura
        from openpyxl import load_workbook
        import os
        
        if os.path.exists(archivo_excel):
            # Método seguro: usar modo 'a' (append) para preservar hojas existentes
            with pd.ExcelWriter(archivo_excel, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name='VE_0_precalculado', index=False)
        else:
            # Si el archivo no existe, crearlo nuevo
            with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='VE_0_precalculado', index=False)
        
        print(f"\n✅ Volúmenes precalculados guardados en '{archivo_excel}' (hoja 'VE_0_precalculado')")
        
    except Exception as e:
        print(f"\n⚠️  Error al guardar en Excel: {e}")
        # Intentar guardar en un archivo separado como respaldo
        try:
            archivo_alt = "VE_0_precalculado.xlsx"
            with pd.ExcelWriter(archivo_alt, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='VE_0_precalculado', index=False)
            print(f"    ✓ Guardado en archivo alternativo: {archivo_alt}")
            print(f"    → Puedes copiar manualmente la hoja al archivo principal")
        except Exception as e2:
            print(f"    ✗ No se pudo guardar: {e2}")
            print("    → Los valores se calcularon correctamente pero no se guardaron")
        
    return df


if __name__ == "__main__":
    """
    Ejemplo de uso del preprocesamiento
    """
    print("="*70)
    print("EJEMPLO DE PREPROCESAMIENTO DE VOLÚMENES")
    print("="*70)
    
    # Valores de ejemplo
    V_30Nov_ejemplos = {
        1: 5500,  # Temporada 1: Volumen intermedio
        2: 4000,  # Temporada 2: Volumen bajo
        3: 7000,  # Temporada 3: Volumen alto
        4: 3500,  # Temporada 4: Volumen muy bajo
        5: 6300   # Temporada 5: Justo en el umbral máximo
    }
    
    # FS simplificado (en la práctica viene del Excel)
    FS_ejemplo = {w: 604800 for w in range(1, 49)}  # 7 días = 604800 segundos
    
    # Calcular
    resultados = calcular_volumenes_iniciales_por_uso(V_30Nov_ejemplos, FS_ejemplo)
    
    print("\n✓ Preprocesamiento completado")
    print(f"  - ve_0 contiene {len(resultados['ve_0'])} valores")
    print(f"  - VG contiene {len(resultados['VG'])} valores")
    print(f"  - VR contiene {len(resultados['VR'])} valores")
    
    # Guardar en Excel (ejemplo)
    print("\nGuardando en Excel...")
    df_guardado = guardar_ve_0_en_excel(resultados['ve_0'], "Parametros_Finales.xlsx")
    print("\n" + df_guardado.to_string(index=False))