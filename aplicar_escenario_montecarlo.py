#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicar Escenario Monte Carlo al Modelo
========================================

Este script toma un escenario generado por Monte Carlo y lo integra
en el archivo Parametros_Finales.xlsx para ser usado por el modelo.
"""

import pandas as pd
import numpy as np
import sys
import shutil
from datetime import datetime

ARCHIVO_EXCEL = 'Parametros_Finales.xlsx'
BACKUP_DIR = 'backups_parametros'
ESCENARIOS_DIR = 'escenarios_montecarlo'

def aplicar_escenario(num_escenario=None, usar_promedio=False):
    """
    Aplica un escenario de Monte Carlo al archivo de parámetros
    
    Parámetros:
    -----------
    num_escenario : int, número del escenario (1-100) o None para promedio
    usar_promedio : bool, si True usa el escenario promedio
    """
    
    print("=" * 70)
    print("APLICAR ESCENARIO MONTE CARLO AL MODELO")
    print("=" * 70)
    
    # Cargar el escenario seleccionado
    if usar_promedio:
        print(f"\n📂 Cargando escenario promedio...")
        escenario_file = f'{ESCENARIOS_DIR}/escenario_promedio.xlsx'
    else:
        if num_escenario is None:
            num_escenario = 1
        print(f"\n📂 Cargando escenario #{num_escenario}...")
        escenario_file = f'{ESCENARIOS_DIR}/escenario_{num_escenario:03d}.xlsx'
    
    df_escenario = pd.read_excel(escenario_file)
    print(f"  ✓ Escenario cargado: {len(df_escenario)} filas")
    
    # Cargar el Excel de parámetros para obtener el formato original
    print(f"\n📂 Cargando {ARCHIVO_EXCEL}...")
    df_qa_original = pd.read_excel(ARCHIVO_EXCEL, sheet_name='QA_a,w,t')
    
    # Guardar nombres de columnas originales (con fechas)
    columnas_originales = df_qa_original.columns.tolist()
    
    print(f"  ✓ Formato original detectado: {len(columnas_originales)} columnas")
    print(f"    Columnas: {columnas_originales[:5]} ... {columnas_originales[-3:]}")
    
    # Crear nueva hoja QA_a,w,t con el escenario
    print(f"\n🔄 Transformando escenario al formato QA_a,w,t...")
    
    # Nombres de afluentes en el orden del Excel original
    nombres_afluentes = ['ELTORO', 'ABANICO', 'ANTUCO', 'TUCAPEL', 'CANECOL', 'LAJA_I']
    
    # Crear lista de filas para el nuevo DataFrame
    filas_qa = []
    
    # Primera fila: encabezado con números de semana
    fila_header = ['t', 'a'] + [float(i) for i in range(1, 49)]
    filas_qa.append(fila_header)
    
    # Para cada temporada
    for t in range(1, 6):
        # Obtener datos de esta temporada del escenario
        df_temp = df_escenario[df_escenario['Temporada'] == t].copy()
        df_temp = df_temp.sort_values('Afluente')
        
        # Para cada afluente (en orden)
        for a_idx, a in enumerate(range(1, 7)):
            fila_afluente = df_temp[df_temp['Afluente'] == a]
            
            if len(fila_afluente) > 0:
                # Extraer valores de semanas (columnas Semana_1, Semana_2, ..., Semana_48)
                semanas_cols = [f'Semana_{w}' for w in range(1, 49)]
                valores = fila_afluente[semanas_cols].values[0].tolist()
            else:
                # Si no hay datos, poner ceros
                valores = [0.0] * 48
            
            # Crear fila: [Temporada, Nombre_Afluente, val1, val2, ..., val48]
            fila = [t, nombres_afluentes[a_idx]] + valores
            filas_qa.append(fila)
    
    # Crear DataFrame con las columnas originales
    df_qa_nuevo = pd.DataFrame(filas_qa, columns=columnas_originales)
    
    print(f"  ✓ DataFrame QA_a,w,t creado: {df_qa_nuevo.shape}")
    print(f"  Primeras filas:")
    print(df_qa_nuevo.head(3))
    
    # Cargar todas las hojas del Excel
    excel_data = pd.read_excel(ARCHIVO_EXCEL, sheet_name=None)
    
    # Cargar todas las hojas del Excel
    excel_data = pd.read_excel(ARCHIVO_EXCEL, sheet_name=None)
    
    # Reemplazar la hoja QA_a,w,t
    excel_data['QA_a,w,t'] = df_qa_nuevo
    
    # Guardar el Excel actualizado
    print(f"\n💾 Guardando {ARCHIVO_EXCEL} actualizado...")
    
    with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl') as writer:
        for sheet_name, df_sheet in excel_data.items():
            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"  ✓ Archivo actualizado exitosamente")
    
    # Resumen
    print("\n" + "=" * 70)
    print("✅ ESCENARIO APLICADO EXITOSAMENTE")
    print("=" * 70)
    if usar_promedio:
        print(f"\n  Escenario aplicado: PROMEDIO")
    else:
        print(f"\n  Escenario aplicado: #{num_escenario}")
    
    print(f"\n  ✓ Puedes ejecutar el modelo normalmente:")
    print(f"    python3 cargar_datos_5temporadas.py")
    print(f"    python3 optimizar_laja_5temporadas.py")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    import os
    
    # Verificar que existan los archivos necesarios
    if not os.path.exists(ESCENARIOS_DIR):
        print(f"❌ Error: No se encuentra el directorio '{ESCENARIOS_DIR}/'")
        print(f"   Ejecuta primero: python3 simulacion_montecarlo_afluentes.py")
        sys.exit(1)
    
    # Parsear argumentos
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.lower() == 'promedio':
            aplicar_escenario(usar_promedio=True)
        elif arg.isdigit():
            num = int(arg)
            if 1 <= num <= 100:
                aplicar_escenario(num_escenario=num)
            else:
                print("❌ Error: El número de escenario debe estar entre 1 y 100")
                sys.exit(1)
        else:
            print("Uso: python3 aplicar_escenario_montecarlo.py [promedio|1-100]")
            print("  promedio: aplica el escenario promedio")
            print("  1-100: aplica el escenario específico")
            sys.exit(1)
    else:
        # Por defecto: mostrar menú
        print("=" * 70)
        print("APLICAR ESCENARIO MONTE CARLO")
        print("=" * 70)
        print("\nOpciones:")
        print("  1. Aplicar escenario promedio (recomendado)")
        print("  2. Aplicar escenario específico (1-100)")
        print("  3. Cancelar")
        
        opcion = input("\nSelecciona opción [1-3]: ").strip()
        
        if opcion == '1':
            aplicar_escenario(usar_promedio=True)
        elif opcion == '2':
            num = input("Ingresa número de escenario (1-100): ").strip()
            if num.isdigit() and 1 <= int(num) <= 100:
                aplicar_escenario(num_escenario=int(num))
            else:
                print("❌ Número inválido")
                sys.exit(1)
        else:
            print("Operación cancelada")
            sys.exit(0)
