# 🚀 Guía Rápida: Optimización del Caso Base

## 📖 Descripción

El script `optimizar_caso_base.py` ejecuta la optimización del **modelo caso base** para la Cuenca del Lago Laja, considerando 5 temporadas con las siguientes características:

- **Modelo:** LP (Linear Programming) completamente lineal
- **Variables de holgura:** `deficit` (riego) y `betha` (volumen mínimo)
- **Horizonte:** 5 temporadas × 48 semanas = 240 semanas
- **Función objetivo:** Maximizar generación - psi·deficit - phi·betha

## 📋 Pre-requisitos

Antes de ejecutar el script, asegúrate de tener:

1. ✅ **Archivo Excel** con parámetros: `Parametros_Finales.xlsx`
2. ✅ **Hoja `VE_0_precalculado`** en el Excel (generada por preprocesamiento)
3. ✅ **Gurobi instalado** con licencia válida
4. ✅ **Python 3.8+** con librerías: `gurobipy`, `pandas`, `numpy`, `openpyxl`

### ⚠️ Importante: Preprocesamiento

Si la hoja `VE_0_precalculado` no existe, ejecuta primero:

```bash
python ejemplo_preprocesamiento.py
```

Este script calculará los volúmenes iniciales por uso (`ve_0[u,t]`) según las reglas del Convenio del Lago Laja.

## 🎯 Ejecución

### Comando Básico

```bash
python optimizar_caso_base.py
```

### Salida Esperada

El script ejecutará los siguientes pasos:

1. **Verificación de pre-requisitos** - Valida archivos y dependencias
2. **Carga de datos** - Lee parámetros desde Excel
3. **Inicialización del modelo** - Crea instancia de `ModeloLaja`
4. **Configuración de parámetros** - Carga parámetros en el modelo
5. **Construcción del modelo** - Define variables y restricciones
6. **Optimización** - Ejecuta solver de Gurobi
7. **Exportación de resultados** - Guarda archivos CSV
8. **Resumen** - Muestra estadísticas clave

## 📊 Resultados Generados

Los resultados se guardan en la carpeta `resultados_caso_base/`:

| Archivo                    | Descripción                                            |
| -------------------------- | ------------------------------------------------------ |
| `generacion.csv`           | Caudales de generación por central, semana y temporada |
| `vertimientos.csv`         | Vertimientos en cada punto del sistema                 |
| `volumenes_lago.csv`       | Evolución del volumen del lago                         |
| `volumenes_por_uso.csv`    | Volúmenes disponibles por uso (riego/generación)       |
| `extracciones_por_uso.csv` | Caudales extraídos por uso                             |
| `riego.csv`                | Retiros, demandas y déficits de riego                  |
| `holguras_volumen.csv`     | Violaciones de volumen mínimo (si existen)             |
| `energia_total.csv`        | Energía generada por central y temporada               |

## 🎛️ Configuración del Solver

El script usa la siguiente configuración para Gurobi:

```python
tiempo_limite = 1800  # 30 minutos
gap = 0.01            # 1% de optimalidad
```

**Nota:** Como el modelo es LP (sin variables binarias), la resolución suele ser **muy rápida** (segundos o minutos).

## 📈 Interpretación de Resultados

### Variables de Holgura

El modelo incluye dos tipos de holguras penalizadas en la función objetivo:

#### 1. Déficit de Riego (`deficit`)

**Archivo:** `riego.csv`

```csv
Demanda,Canal,Semana,Temporada,Demanda_m3s,Provisto_m3s,Deficit_m3s
1,1,5,1,10.0,7.5,2.5
```

- `Deficit_m3s = 0` → ✅ Demanda satisfecha
- `Deficit_m3s > 0` → ⚠️ Déficit de riego
- **Penalización:** `psi × deficit` [GWh/hm³]

#### 2. Violación de Volumen Mínimo (`betha`)

**Archivo:** `holguras_volumen.csv` (solo si hay violaciones)

```csv
Semana,Temporada,Betha_hm3
15,1,50.5
23,2,30.2
```

- `Betha_hm3 = 0` → ✅ Volumen cumple V_min
- `Betha_hm3 > 0` → ⚠️ Volumen bajó de V_min
- **Penalización:** `phi × betha` [GWh/hm³]

### Estadísticas en Pantalla

El script mostrará automáticamente:

```
📊 ESTADÍSTICAS DE RIEGO:
  Total observaciones:    1,440
  Déficits detectados:    15
  Déficit total:          45.50 m³/s acumulado
  Déficit máximo:         5.20 m³/s

💧 VOLUMEN DEL LAGO:
  Volumen inicial:        5,500.00 hm³
  Volumen final:          5,200.00 hm³
  Volumen mínimo:         4,850.00 hm³
  Volumen máximo:         6,100.00 hm³

⚡ GENERACIÓN ELÉCTRICA:
  Energía total:          1,234.56 GWh
  Energía promedio/temp:  246.91 GWh
```

## 🔍 Verificación de Resultados

### 1. Verificar Estado de Optimización

Al finalizar, el script muestra:

```
✅ OPTIMIZACIÓN EXITOSA
  Estado:                 Óptimo
  Valor objetivo:         1,234.56 GWh
  Tiempo de resolución:   15.23 segundos
  Gap de optimalidad:     0.0000%
```

**Estados posibles:**

- `Óptimo` (GRB.OPTIMAL) → ✅ Solución óptima encontrada
- `Tiempo límite` (GRB.TIME_LIMIT) → ⚠️ Solución factible pero posiblemente no óptima
- `Infactible` (GRB.INFEASIBLE) → ❌ Problema sin solución (revisar parámetros)

### 2. Revisar Variables Binarias

El modelo caso base es **LP puro**, por lo que:

```
Variables binarias:     0
```

Si este número es > 0, hay un error en el modelo.

### 3. Comprobar Archivos Generados

```bash
# Listar archivos generados
ls resultados_caso_base/

# Ver primeras líneas de un resultado
head resultados_caso_base/riego.csv
```

## 🛠️ Troubleshooting

### Error: "No se encontraron valores precalculados de ve_0"

**Causa:** No existe la hoja `VE_0_precalculado` en el Excel.

**Solución:**

```bash
python ejemplo_preprocesamiento.py
```

### Error: "Gurobi no está instalado"

**Causa:** No se encuentra la librería `gurobipy`.

**Solución:**

```bash
pip install gurobipy
# Y asegúrate de tener una licencia válida
```

### Error: "Model is infeasible"

**Causas posibles:**

- Volúmenes iniciales incompatibles con restricciones
- Demandas imposibles de satisfacer con afluentes disponibles
- V_min muy alto para el volumen inicial

**Solución:**

- Revisa parámetros en Excel (V_0, V_min, demandas)
- Ajusta valores de `V_30Nov` en el preprocesamiento
- Usa `modelo.model.computeIIS()` para identificar restricciones conflictivas

### Modelo tarda mucho en resolver

**Causa poco probable:** El modelo es LP, debería ser muy rápido.

**Posibles causas:**

- Problema de escalado numérico
- Matriz mal condicionada

**Solución:**

- Verifica unidades de parámetros
- Ajusta parámetros de Gurobi (método simplex vs. barrier)
- Consulta logs de Gurobi para detalles

## 🔄 Comparación con Otros Modelos

| Aspecto            | Caso Base      | Modelo 1 Temporada | Modelo 5 Temp (original) |
| ------------------ | -------------- | ------------------ | ------------------------ |
| Temporadas         | 5              | 1                  | 5                        |
| Variables binarias | 0              | 0                  | 15-25                    |
| Tipo               | LP             | LP                 | MILP                     |
| Tiempo resolución  | Segundos       | <1 min             | Minutos-horas            |
| Variables holgura  | deficit, betha | deficit            | deficit, superavit       |
| ve_0               | Precalculado   | Precalculado       | Dinámico (binarias)      |

## 📚 Documentación Relacionada

- `README_LP_COMPLETAMENTE_LINEAL.md` - Explicación del enfoque LP
- `README_WORKFLOW.md` - Flujo de trabajo completo
- `CAMBIOS_VARIABLES_HOLGURA.md` - Detalles de variables deficit y betha
- `README_VOLUMENES_POR_USO.md` - Preprocesamiento de ve_0

## 💡 Consejos

1. **Ejecuta el preprocesamiento primero** - Siempre que cambies `V_30Nov` o parámetros del convenio
2. **Revisa las holguras** - Valores altos de `deficit` o `betha` indican problemas
3. **Ajusta penalizaciones** - Calibra `psi` y `phi` según prioridades del caso de estudio
4. **Compara escenarios** - Ejecuta con diferentes valores de afluentes o demandas
5. **Documenta cambios** - Guarda versiones del Excel con nombres descriptivos

## 🎓 Próximos Pasos

Después de ejecutar la optimización:

1. ✅ **Visualizar resultados:**

   ```bash
   python visualizar_resultados_5temporadas.py
   ```

2. ✅ **Analizar holguras:**

   - Revisar `holguras_volumen.csv` (si existe)
   - Identificar períodos críticos de déficit

3. ✅ **Iterar si es necesario:**

   - Ajustar `psi` y `phi`
   - Modificar `V_30Nov` en preprocesamiento
   - Re-ejecutar optimización

4. ✅ **Análisis de sensibilidad:**
   - Variar parámetros clave (afluentes, demandas, V_min)
   - Comparar resultados entre escenarios

---

**¡Listo para optimizar el caso base! 🚀**

Para cualquier duda, consulta la documentación o revisa los comentarios en el código.
