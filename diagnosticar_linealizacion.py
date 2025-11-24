"""
Script para diagnosticar la linealización de VR_0 y VG_0
"""

from modelo_laja_latex import ModeloLajaLatex
from cargar_datos_5temporadas import cargar_parametros_excel

# Cargar y optimizar modelo
print("Cargando modelo...")
parametros = cargar_parametros_excel()
modelo = ModeloLajaLatex()
modelo.cargar_parametros(parametros)
modelo.construir_modelo()

print("\nOptimizando...")
modelo.optimizar(time_limit=60, mip_gap=0.02)

if modelo.model.status == 2 or modelo.model.status == 9:  # Optimal o TimeLimit con solución
    print("\n" + "="*70)
    print("DIAGNÓSTICO DE LINEALIZACIÓN - TEMPORADA 1")
    print("="*70)
    
    # Verificar V_30Nov[1]
    v30_val = modelo.V_30Nov[1].X
    print(f"\nV_30Nov[1] = {v30_val:.2f} hm³")
    
    # Verificar delta_v30 y phi_30 para temporada 1
    print("\nVariables delta_v30 y phi_30 para t=1:")
    print(f"{'Zona k':<10} {'delta_v30':<15} {'phi_30':<10} {'v_k':<15} {'v_k+1':<15} {'ancho':<15}")
    print("-" * 90)
    
    total_delta = 0
    K_zonas = modelo.K[:-1]
    
    for k in K_zonas:
        delta_val = modelo.delta_v30[k, 1].X
        phi_val = modelo.phi_30[k, 1].X
        v_k = modelo.v_k[k]
        v_k_next = modelo.v_k[k+1]
        ancho = v_k_next - v_k
        total_delta += delta_val
        
        print(f"{k:<10} {delta_val:<15.4f} {phi_val:<10.1f} {v_k:<15.2f} {v_k_next:<15.2f} {ancho:<15.2f}")
    
    print("-" * 90)
    print(f"{'TOTAL':<10} {total_delta:<15.4f}")
    print(f"\nVerificación: v[1] + Σ delta_v30 = {modelo.v_k[1]:.2f} + {total_delta:.2f} = {modelo.v_k[1] + total_delta:.2f}")
    print(f"Debería ser igual a V_30Nov[1] = {v30_val:.2f}")
    
    if abs(modelo.v_k[1] + total_delta - v30_val) < 0.01:
        print("✓ Restricción V_30Nov correcta")
    else:
        print("✗ ERROR: Restricción V_30Nov NO se cumple!")
    
    # Calcular VR_0 y VG_0 manualmente
    print("\n" + "="*70)
    print("CÁLCULO MANUAL DE VR_0 Y VG_0")
    print("="*70)
    
    vr_calc = modelo.vr_k[1]
    vg_calc = modelo.vg_k[1]
    
    print(f"\nBase: vr[1] = {modelo.vr_k[1]:.2f}, vg[1] = {modelo.vg_k[1]:.2f}")
    print(f"\n{'Zona k':<10} {'delta_v30':<15} {'coef_vr':<15} {'contrib_vr':<15} {'coef_vg':<15} {'contrib_vg':<15}")
    print("-" * 90)
    
    for k in K_zonas:
        delta_val = modelo.delta_v30[k, 1].X
        
        v_k = modelo.v_k[k]
        v_k_next = modelo.v_k[k+1]
        vr_k = modelo.vr_k[k]
        vr_k_next = modelo.vr_k[k+1]
        vg_k = modelo.vg_k[k]
        vg_k_next = modelo.vg_k[k+1]
        
        if abs(v_k_next - v_k) > 1e-6:
            coef_vr = (vr_k_next - vr_k) / (v_k_next - v_k)
            coef_vg = (vg_k_next - vg_k) / (v_k_next - v_k)
        else:
            coef_vr = 0
            coef_vg = 0
        
        contrib_vr = coef_vr * delta_val
        contrib_vg = coef_vg * delta_val
        
        vr_calc += contrib_vr
        vg_calc += contrib_vg
        
        print(f"{k:<10} {delta_val:<15.4f} {coef_vr:<15.6f} {contrib_vr:<15.4f} {coef_vg:<15.6f} {contrib_vg:<15.4f}")
    
    print("-" * 90)
    print(f"{'TOTAL':<10} {'':<15} {'':<15} {vr_calc:<15.2f} {'':<15} {vg_calc:<15.2f}")
    
    # Comparar con valores del modelo
    vr_modelo = modelo.VR_0[1].X
    vg_modelo = modelo.VG_0[1].X
    
    print(f"\nVR_0[1] calculado manualmente: {vr_calc:.2f} hm³")
    print(f"VR_0[1] del modelo: {vr_modelo:.2f} hm³")
    if abs(vr_calc - vr_modelo) < 0.01:
        print("✓ VR_0 correcto")
    else:
        print(f"✗ ERROR: Diferencia de {abs(vr_calc - vr_modelo):.2f} hm³")
    
    print(f"\nVG_0[1] calculado manualmente: {vg_calc:.2f} hm³")
    print(f"VG_0[1] del modelo: {vg_modelo:.2f} hm³")
    if abs(vg_calc - vg_modelo) < 0.01:
        print("✓ VG_0 correcto")
    else:
        print(f"✗ ERROR: Diferencia de {abs(vg_calc - vg_modelo):.2f} hm³")
    
    # Valores esperados
    print(f"\n" + "="*70)
    print("COMPARACIÓN CON VALORES ESPERADOS")
    print("="*70)
    print(f"Para V_30Nov = {v30_val:.2f} hm³:")
    print(f"  VR_0 esperado: ≈ 1205 hm³")
    print(f"  VR_0 obtenido: {vr_modelo:.2f} hm³")
    print(f"  VG_0 esperado: ≈ 1096 hm³")
    print(f"  VG_0 obtenido: {vg_modelo:.2f} hm³")

else:
    print(f"\n✗ Modelo no tiene solución óptima. Status: {modelo.model.status}")
