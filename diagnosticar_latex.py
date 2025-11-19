"""
Script para diagnosticar infactibilidad del modelo LaTeX
"""

import gurobipy as gp
from gurobipy import GRB
from cargar_datos_5temporadas import cargar_parametros_excel
from modelo_laja_latex import ModeloLajaLatex

def diagnosticar():
    print("\n" + "="*70)
    print("DIAGNÓSTICO DE INFACTIBILIDAD - MODELO LATEX")
    print("="*70 + "\n")
    
    # Cargar parámetros
    print("Cargando parámetros...")
    parametros = cargar_parametros_excel()
    
    # Crear modelo
    print("Creando modelo...")
    modelo = ModeloLajaLatex()
    modelo.cargar_parametros(parametros)
    modelo.construir_modelo()
    
    # Computar IIS
    print("\n" + "="*70)
    print("COMPUTANDO IIS (Conjunto Irreduciblemente Infactible)...")
    print("="*70 + "\n")
    
    modelo.model.computeIIS()
    
    # Guardar IIS
    modelo.model.write("modelo_infactible.ilp")
    print("✓ IIS guardado en 'modelo_infactible.ilp'\n")
    
    # Analizar restricciones en conflicto
    print("="*70)
    print("RESTRICCIONES EN CONFLICTO:")
    print("="*70 + "\n")
    
    conflictos = []
    for c in modelo.model.getConstrs():
        if c.IISConstr:
            conflictos.append(c.ConstrName)
    
    # Agrupar por tipo
    tipos_conflicto = {}
    for nombre in conflictos:
        tipo = nombre.split('_')[0] if '_' in nombre else nombre
        if tipo not in tipos_conflicto:
            tipos_conflicto[tipo] = []
        tipos_conflicto[tipo].append(nombre)
    
    print(f"Total de restricciones en conflicto: {len(conflictos)}\n")
    
    for tipo, lista in sorted(tipos_conflicto.items()):
        print(f"{tipo}: {len(lista)} restricciones")
        if len(lista) <= 10:
            for nombre in lista:
                print(f"  - {nombre}")
        else:
            for nombre in lista[:5]:
                print(f"  - {nombre}")
            print(f"  ... y {len(lista)-5} más")
        print()
    
    # Analizar variables en conflicto
    print("="*70)
    print("VARIABLES CON LÍMITES EN CONFLICTO:")
    print("="*70 + "\n")
    
    vars_conflicto = []
    for v in modelo.model.getVars():
        if v.IISLB or v.IISUB:
            vars_conflicto.append((v.VarName, v.IISLB, v.IISUB))
    
    if vars_conflicto:
        print(f"Total: {len(vars_conflicto)} variables\n")
        for nombre, lb, ub in vars_conflicto[:20]:
            lb_str = "LB✓" if lb else "   "
            ub_str = "UB✓" if ub else "   "
            print(f"  {lb_str} {ub_str} {nombre}")
        if len(vars_conflicto) > 20:
            print(f"  ... y {len(vars_conflicto)-20} más")
    else:
        print("  Ninguna variable con límites en conflicto")
    
    print("\n" + "="*70)
    print("ANÁLISIS COMPLETADO")
    print("="*70 + "\n")
    
    # Revisar parámetros críticos
    print("="*70)
    print("VERIFICACIÓN DE PARÁMETROS CRÍTICOS:")
    print("="*70 + "\n")
    
    print(f"V_0 = {modelo.V_0} hm³")
    print(f"V_MIN = {modelo.V_MIN} hm³")
    print(f"V_MAX = {modelo.V_MAX} hm³")
    print(f"V_F = {modelo.V_F} hm³")
    print(f"M (Big-M) = {modelo.M_bigM}")
    print(f"Zonas K: {len(modelo.K)}")
    print(f"f_k rango: [{min(modelo.f_k.values()):.2f}, {max(modelo.f_k.values()):.2f}] m³/s")
    print(f"v_k rango: [{min(modelo.v_k.values()):.2f}, {max(modelo.v_k.values()):.2f}] hm³")
    print(f"vr_k rango: [{min(modelo.vr_k.values()):.2f}, {max(modelo.vr_k.values()):.2f}] hm³")
    print(f"vg_k rango: [{min(modelo.vg_k.values()):.2f}, {max(modelo.vg_k.values()):.2f}] hm³")
    
    print("\n" + "="*70)
    
    # Verificar consistencia V_0 con zonas
    print("CONSISTENCIA V_0 CON ZONAS:")
    print("="*70 + "\n")
    
    print(f"V_0 = {modelo.V_0} hm³")
    print(f"Debe estar en rango: [{min(modelo.v_k.values()):.2f}, {max(modelo.v_k.values()):.2f}] hm³")
    
    if modelo.V_0 < min(modelo.v_k.values()):
        print("❌ ERROR: V_0 es menor que v_1 (zona mínima)")
    elif modelo.V_0 > max(modelo.v_k.values()):
        print("❌ ERROR: V_0 es mayor que v_K (zona máxima)")
    else:
        print("✓ V_0 está dentro del rango de zonas")
    
    print()
    
    # Revisar volúmenes de uso
    print("VOLÚMENES DE USO EN SEMANA 32:")
    print("="*70 + "\n")
    
    vr_32 = modelo.vr_k
    vg_32 = modelo.vg_k
    
    print(f"vr_k rango: [{min(vr_32.values()):.2f}, {max(vr_32.values()):.2f}] hm³")
    print(f"vg_k rango: [{min(vg_32.values()):.2f}, {max(vg_32.values()):.2f}] hm³")
    
    # Verificar que v_k esté entre vr_k y vg_k
    for k in modelo.K:
        v = modelo.v_k[k]
        vr = vr_32[k]
        vg = vg_32[k]
        
        if not (min(vr, vg) <= v <= max(vr, vg)):
            print(f"⚠ Zona {k}: v_k={v:.2f} NO está entre vr_k={vr:.2f} y vg_k={vg:.2f}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    diagnosticar()
