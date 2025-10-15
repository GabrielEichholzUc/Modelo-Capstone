# Simulación Monte Carlo de Afluentes

Este módulo permite generar escenarios sintéticos de caudales afluentes basados en datos históricos usando simulación Monte Carlo.

## 📁 Archivos

- `simulacion_montecarlo_afluentes.py`: Script principal para generar escenarios
- `aplicar_escenario_montecarlo.py`: Script para aplicar un escenario al modelo
- `escenarios_montecarlo/`: Carpeta con escenarios generados

## 🚀 Uso Rápido

### 1. Generar Escenarios

```bash
python3 simulacion_montecarlo_afluentes.py
```

Esto generará:
- ✅ 100 escenarios aleatorios **ordenados de pesimista a optimista**
- ✅ Un escenario promedio (recomendado para el modelo)
- ✅ Gráficos de validación

**Nota importante:** Los escenarios se ordenan automáticamente por caudal total promedio:
- `escenario_001.xlsx`: Escenario más **pesimista** (menor caudal)
- `escenario_050.xlsx`: Escenario **mediano**
- `escenario_100.xlsx`: Escenario más **optimista** (mayor caudal)

### 2. Aplicar Escenario al Modelo

**Opción A: Aplicar escenario promedio (recomendado)**
```bash
python3 aplicar_escenario_montecarlo.py promedio
```

**Opción B: Aplicar escenario específico**
```bash
python3 aplicar_escenario_montecarlo.py 5  # Aplica escenario #5
```

**Opción C: Modo interactivo**
```bash
python3 aplicar_escenario_montecarlo.py
```

### 3. Ejecutar el Modelo

```bash
python3 cargar_datos_5temporadas.py
python3 optimizar_laja_5temporadas.py
python3 visualizar_resultados_5temporadas.py
```

## 📊 Métodos de Simulación

El script soporta 4 métodos diferentes:

1. **`empirico`** (por defecto): Muestreo directo de datos históricos
2. **`normal`**: Distribución normal con media y desviación empíricas
3. **`lognormal`**: Distribución lognormal (apropiada para caudales)
4. **`bootstrap`**: Bootstrap con perturbación gaussiana

Para cambiar el método, edita la variable `METODO` en `simulacion_montecarlo_afluentes.py`.

## 🎯 Parámetros Configurables

En `simulacion_montecarlo_afluentes.py`:

```python
NUM_ESCENARIOS = 100  # Número de escenarios a generar
SEED = 42            # Semilla para reproducibilidad
METODO = 'empirico'  # Método de muestreo
```

## 📈 Validación

El script genera automáticamente:

- **Comparación visual**: Histogramas de datos históricos vs. simulados
- **Estadísticas**: Media y desviación estándar por afluente
- **Test K-S**: Prueba de Kolmogorov-Smirnov (si scipy está disponible)

## 📂 Estructura de Archivos Generados

```
escenarios_montecarlo/
├── escenario_001.xlsx              # Escenario PESIMISTA (menor caudal)
├── escenario_002.xlsx              # Escenario pesimista-intermedio
├── ...
├── escenario_005.xlsx              # Escenario intermedio
├── ...
├── escenario_010.xlsx              # Escenario optimista-intermedio
├── todos_escenarios.xlsx           # Consolidado (primeros 20, ordenados)
├── escenario_promedio.xlsx         # Promedio de todos (RECOMENDADO)
└── comparacion_historicos_simulados.png  # Validación visual
```

**📊 Ordenamiento de Escenarios:**
Los escenarios están ordenados por **caudal total promedio** de menor a mayor:
- Escenario #1: Más pesimista (~29.65 m³/s promedio)
- Escenario #50: Mediano (~30.90 m³/s promedio)
- Escenario #100: Más optimista (~32.41 m³/s promedio)

## 🔄 Workflow Completo

```bash
# 1. Generar escenarios
python3 simulacion_montecarlo_afluentes.py

# 2. Aplicar escenario promedio
python3 aplicar_escenario_montecarlo.py promedio

# 3. Ejecutar modelo completo
python3 cargar_datos_5temporadas.py
python3 optimizar_laja_5temporadas.py
python3 visualizar_resultados_5temporadas.py
```

## ⚠️ Importante

- El script crea un **backup automático** de `Parametros_Finales.xlsx` en `backups_parametros/`
- Los backups incluyen timestamp: `Parametros_Finales_backup_20241015_110930.xlsx`
- Puedes restaurar el archivo original desde el backup en cualquier momento

## 📊 Estadísticas de Validación

Ejemplo de salida del script:

```
Afluente 1 (Semana 10):
  Históricos: media=74.06, std=54.08
  Simulados:  media=70.30, std=50.38

Afluente 2 (Semana 10):
  Históricos: media=4.30, std=2.97
  Simulados:  media=4.33, std=3.08
```

Las distribuciones simuladas deben tener estadísticas similares a las históricas.

## 🔧 Troubleshooting

**Error: "No module named 'scipy'"**
- Scipy es opcional. El script funcionará sin ella (se omitirá el test K-S)
- Para instalar: `pip3 install scipy`

**Error: "No se encuentra el directorio 'escenarios_montecarlo/'"**
- Ejecuta primero `python3 simulacion_montecarlo_afluentes.py`

**Los escenarios son muy diferentes a los históricos**
- Verifica el método de simulación (`METODO`)
- Aumenta `NUM_ESCENARIOS` para mejor representatividad
- Revisa el gráfico de comparación
