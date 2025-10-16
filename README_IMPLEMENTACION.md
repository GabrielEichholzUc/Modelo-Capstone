# Implementación del Modelo de Optimización

## Definición de Parámetros del Problema

### Simulación Monte Carlo de Afluentes

Este módulo permite generar escenarios sintéticos de caudales afluentes basados en datos históricos usando simulación Monte Carlo, usando un método lognormal.

En el archivo `README_MONTECARLO.md` se detallan los pasos para generar y aplicar escenarios Monte Carlo al modelo de optimización.

### Volúmenes del Lago

`V_30Nov_1` y `V_0` Se extraen desde la página del coordinador eléctrico nacional.

`V_MIN` se define para asegurar el colchón inferior.

## Ejecución del Modelo y Resultados

Se corren 3 de los 10 escenarios: 1, 5 y 10 (pesimista, intermedio y optimista). Se obtienen los siguientes resultados en la implementación gurobi:

| Escenario | Valor Objetivo (GWh) | Tiempo (s) | Gap (%) |
|-----------|----------------------|------------|---------|
| 5         | 25.285,69 GWh        | 713.8      | 1.81    |
| 50        | 26.265,58 GWh        | 450.1      | 1.82    |
| 100       | 27.606,39 GWh        | 3536       | 2.58    |

Se generan gráficos de los resultados en la carpeta `graficos/`.
