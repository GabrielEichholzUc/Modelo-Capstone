"""
Modelo de Optimización - Convenio Hidroeléctricas y Riegos Cuenca Laja
Maximizar generación sujeto a cumplir compromisos de riego
Horizonte: 5 Temporadas
Solver: Gurobi
"""

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

class ModeloLaja:
    def __init__(self):
        """
        Inicializa el modelo de optimización para la cuenca del Laja
        """
        self.model = gp.Model("Convenio_Laja_5Temporadas")
        
        # Conjuntos
        self.S = None  # Simulaciones
        self.T = list(range(1, 6))  # Temporadas (1-5)
        self.M = list(range(1, 13))  # Meses
        self.W = list(range(1, 49))  # Semanas hidrológicas por temporada
        self.D = [1, 2, 3]  # Demandas (1:Primeros, 2:Segundos, 3:Saltos del Laja)
        self.U = [1, 2]  # Usos (1:Riego, 2:Generación)
        self.I = list(range(1, 17))  # Centrales (1-16)
        self.J = [1, 2, 3, 4]  # Puntos de retiro (1:RieZaCo, 2:RieTucapel, 3:RieSaltos, 4:Abanico)
        self.A = list(range(1, 7))  # Afluentes (1:ElToro, 2:Abanico, 3:Antuco, 4:Tucapel, 5:Canecol, 6:Laja_I)
        self.K = None  # Cotas del lago (se definirá con datos)
        
        # Parámetros
        self.V_30Nov_1 = None  # Volumen al 30 Nov previo a temporada 1
        self.V_0 = None  # Volumen al inicio de la planificación
        self.V_MAX = None
        self.FC = {}  # FC[k]: Filtraciones en cota k [m³/s]
        self.VC = {}  # VC[k]: Volumen en cota k [hm³]
        self.VUC = {}  # VUC[u,k]: Volumen de uso u en cota k [hm³]
        self.QA = {}  # QA[a,w,t]: Caudal afluente a en semana w de temporada t [m³/s]
        self.QD = {}  # QD[d,j,w]: Caudal demandado por d en canal j en semana w [m³/s]
        self.gamma = {}  # gamma[i]: Caudal máximo central i [m³/s]
        self.rho = {}  # rho[i]: Rendimiento central i [MW/(m³/s)] - Potencia específica
        self.pi = {}  # pi[i]: Potencia máxima central i [MW]
        self.FS = {}  # FS[w]: Factor segundos en semana w [segundos]
        self.psi = None  # Costo incumplir convenio [GWh] (penalización en función objetivo)
        self.phi = None  # Costo bajar umbral de V_min [GWh] (penalización en función objetivo)
        self.V_min = None  # Volumen mínimo del lago (umbral) [hm³]
        self.Qf = None # Parámetro filraciones (se carga desde Excel)
        self.theta = None # Parámetro porcentaje distribucion (se carga desde Excel)

        # Variables
        self.V_30Nov = {}  # V_30Nov[t]: Volumen al 30 Nov previo a temp t
        self.V = {}  # V[w,t]: Volumen al final de semana w de temporada t
        self.ve = {}  # ve[u,w,t]: Volumen disponible
        self.ve_0 = {}  # ve[u,0,t]: Volumen disponible inicial
        self.qe = {}  # qe[u,w,t]: Caudal extraído
        self.qf = {}  # qf[w,t]: Caudal de filtración
        self.qg = {}  # qg[i,w,t]: Caudal generación
        self.qv = {}  # qv[i,w,t]: Caudal vertimiento
        self.qp = {}  # qp[d,j,w,t]: Caudal provisto riego
        self.deficit = {}  # deficit[d,j,w,t]: Déficit de riego
        self.beta = {}  # beta[w,t]: Deficit volumen del lago
        self.GEN = {}  # GEN[i,t]: Energía generada [GWh] por central i en temporada t
        
    def cargar_parametros(self, dict_parametros):
        """Carga los parámetros del modelo"""
        # Guardar referencia al diccionario completo
        self.parametros = dict_parametros
        
        self.V_30Nov_1 = dict_parametros.get('V_30Nov_1', dict_parametros.get('V_30Nov'))
        self.V_0 = dict_parametros.get('V_0')
        self.V_MAX = dict_parametros.get('V_MAX')
        self.FC = dict_parametros.get('FC')
        self.VC = dict_parametros.get('VC')
        self.QA = dict_parametros.get('QA')
        self.QD = dict_parametros.get('QD')
        self.gamma = dict_parametros.get('gamma')
        self.rho = dict_parametros.get('rho')
        self.pi = dict_parametros.get('pi')
        self.FS = dict_parametros.get('FS')
        self.psi = dict_parametros.get('psi')
        self.phi = dict_parametros.get('phi')
        self.V_min = dict_parametros.get('V_min', 1400)  # Default 1400 si no está en Excel
        self.Qf = dict_parametros.get('Qf')  # Caudal de filtración
        self.theta = dict_parametros.get('theta')  # Prioridades theta[d,j]
        self.K = list(self.VC.keys())
        print("✓ Parámetros cargados correctamente")
        print(f"  - Qf (filtración): {self.Qf} m³/s")
        print(f"  - Theta (prioridades): {len(self.theta) if self.theta else 0} registros")
        
        # Mostrar información de volúmenes por uso si están precalculados
        if 've_0_precalculado' in dict_parametros:
            print(f"  - ve_0 (precalculado): {len(dict_parametros['ve_0_precalculado'])} valores")
        
    def crear_variables(self):
        """Crea todas las variables de decisión"""
        print("Creando variables de decisión...")
        
        # Volúmenes del lago
        self.V_30Nov = self.model.addVars(self.T, lb=0, ub=self.V_MAX, name="V_30Nov")
        self.V = self.model.addVars(self.W, self.T, lb=0, ub=self.V_MAX, name="V")
        
        # Volúmenes por uso
        self.ve = self.model.addVars(self.U, self.W, self.T, lb=0, name="ve")
        self.ve_0 = self.model.addVars(self.U, self.T, lb=0, name="ve_0")
        
        # Caudales
        self.qe = self.model.addVars(self.U, self.W, self.T, lb=0, name="qe")
        self.qf = self.model.addVars(self.W, self.T, lb=0, name="qf")
        self.qg = self.model.addVars(self.I, self.W, self.T, lb=0, name="qg")
        self.qv = self.model.addVars(self.I, self.W, self.T, lb=0, name="qv")
        self.qp = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="qp")
        
        # Variables de holgura
        self.deficit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="deficit")  # Holgura de riego
        self.betha = self.model.addVars(self.W, self.T, lb=0, name="betha")  # Holgura de volumen mínimo
        
        # Variable de energía generada por central y temporada [GWh]
        self.GEN = self.model.addVars(self.I, self.T, lb=0, name="GEN")
        
        print("✓ Variables creadas correctamente")
        
    def crear_restricciones(self):
        """Crea todas las restricciones del modelo"""
        print("Creando restricciones...")
        M_vol = self.V_MAX * 2
        
        # ========== 1. DEFINICIÓN DE FILTRACIONES ==========
        # Usar filtración constante Qf desde parámetros
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qf[w, t] == self.Qf,
                    name=f"filtracion_{w}_{t}")
        
        # ========== 2. VOLÚMENES DISPONIBLES INICIALES POR USO ==========
        # Usar valores precalculados de ve_0[u,t] (generados por preprocesar_volumenes_uso.py)
        # Esto mantiene el modelo completamente lineal (LP, no MILP)
        
        # Verificar si existen valores precalculados
        if 've_0_precalculado' not in self.parametros:
            raise ValueError(
                "ERROR: No se encontraron valores precalculados de ve_0.\n"
                "Debes ejecutar primero el script 'preprocesar_volumenes_uso.py' para calcular\n"
                "los volúmenes iniciales por uso según las reglas del convenio.\n"
                "Ver README_VOLUMENES_POR_USO.md para más detalles."
            )
        
        ve_0_precalc = self.parametros['ve_0_precalculado']
        
        # Fijar ve_0[u,t] a los valores precalculados
        for t in self.T:
            for u in self.U:
                self.model.addConstr(
                    self.ve_0[u, t] == ve_0_precalc[(u, t)],
                    name=f"ve_0_fijo_{u}_{t}")
        
        # ========== 3. GENERACIÓN EN EL TORO ==========
        # qg[1] = suma de extracciones por uso
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[1, w, t] == gp.quicksum(self.qe[u, w, t] for u in self.U),
                    name=f"gen_eltoro_{w}_{t}")
        
        # ========== 4. BALANCE DE VOLÚMENES POR USO ==========
        # Balance volumen por uso a lo largo de la temporada
        for t in self.T:
            for u in self.U:
                for w in self.W:
                    if w == 1:
                        # Primera semana: desde ve_0
                        self.model.addConstr(
                            self.ve[u, w, t] == self.ve_0[u, t] - self.qe[u, w, t] * self.FS[w] / 1000000,
                            name=f"balance_ve_{u}_{w}_{t}")
                    else:
                        # Semanas siguientes: desde semana anterior
                        self.model.addConstr(
                            self.ve[u, w, t] == self.ve[u, w-1, t] - self.qe[u, w, t] * self.FS[w] / 1000000,
                            name=f"balance_ve_{u}_{w}_{t}")
        
        # ========== 5. VOLUMEN TOTAL DEL LAGO ==========
        # Balance volumen total del lago
        for t in self.T:
            for w in self.W:
                if w == 1:
                    if t == 1:
                        # Primera semana temporada 1: desde V_0
                        self.model.addConstr(
                            self.V[w, t] == self.V_0 + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                            name=f"balance_vol_{w}_{t}")
                    else:
                        # Primera semana otras temporadas: desde última semana temporada anterior
                        self.model.addConstr(
                            self.V[w, t] == self.V[48, t-1] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                            name=f"balance_vol_{w}_{t}")
                else:
                    self.model.addConstr(
                        self.V[w, t] == self.V[w-1, t] + (self.QA[1, w, t] - self.qg[1, w, t] - self.qf[w, t]) * self.FS[w] / 1000000,
                        name=f"balance_vol_{w}_{t}")
        
        # Encadenamiento V_30Nov: V_30Nov[t] = V[32, t-1] para t > 1
        for t in self.T:
            if t == 1:
                # Temporada 1: fijar V_30Nov[1] al parámetro
                self.model.addConstr(self.V_30Nov[1] == self.V_30Nov_1, name="V_30Nov_1_fijo")
            else:
                # Temporadas 2-5: V_30Nov[t] = V[32, t-1]
                self.model.addConstr(self.V_30Nov[t] == self.V[32, t-1], name=f"encaden_30Nov_{t}")
        
        # ========== 5b. RESTRICCIÓN DE VOLUMEN MÍNIMO CON HOLGURA ==========
        # V[w,t] + betha[w,t] >= V_min
        # Si V[w,t] < V_min, entonces betha[w,t] > 0 (penalizado en F.O.)
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.V[w, t] + self.betha[w, t] >= self.V_min,
                    name=f"vol_min_holgura_{w}_{t}")
        
        # ========== 6. LAJA FILTRACIONES (Central 16) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[16, w, t] == self.qf[w, t],
                    name=f"laja_filt_{w}_{t}")
        
        # ========== 7. ABANICO (Central 2 + Canal j=4) ==========
        for t in self.T:
            for w in self.W:
                # Balance central Abanico: entrada = salida_turbinada + salida_vertida
                # Entrada: QA[2] + qg[16] (filtraciones del lago)
                # Salida turbinada: qg[2]
                # Salida vertida: qv[2]
                self.model.addConstr(
                    self.qg[2, w, t] + self.qv[2, w, t] == self.QA[2, w, t] + self.qg[16, w, t],
                    name=f"abanico_{w}_{t}")
                
                # Distribución a regantes en canal Abanico
                # El agua disponible para riego es lo que pasa por la central
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 4, w, t] for d in self.D) <= self.qg[2, w, t],
                    name=f"abanico_canal_{w}_{t}")
                
                # Balance demanda en canal Abanico (qp puede ser menor o igual a demanda)
                for d in self.D:
                    self.model.addConstr(
                        self.qp[d, 4, w, t] + self.deficit[d, 4, w, t] >= self.QD.get((d, 4, w), 0),
                        name=f"balance_abanico_{d}_{w}_{t}")
        
        # ========== 8. ANTUCO (Central 3) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[3, w, t] == self.QA[3, w, t] + self.qg[1, w, t] + self.qg[2, w, t] + self.qv[2, w, t] - self.qv[3, w, t],
                    name=f"antuco_{w}_{t}")
        
        # ========== 9. RIEZACO (Punto j=1 - NO es una central, solo distribución a riego) ==========
        # El agua que llega de Antuco se distribuye a riego o se vierte hacia abajo (Clajrucue)
        for t in self.T:
            for w in self.W:
                # Balance: agua_entrante = agua_para_riego + agua_vertida_abajo
                # Entrada: qg[3] + qv[3] (de Antuco)
                # Salida a riego: sum qp[d,1]
                # Salida vertida: qv[4] (va a Clajrucue)
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 1, w, t] for d in self.D) + self.qv[4, w, t] == self.qg[3, w, t] + self.qv[3, w, t],
                    name=f"riezaco_disp_{w}_{t}")
                
                # Balance demanda en canal RieZaCo (qp puede ser menor o igual a demanda)
                for d in self.D:
                    self.model.addConstr(
                        self.qp[d, 1, w, t] + self.deficit[d, 1, w, t] >= self.QD.get((d, 1, w), 0),
                        name=f"balance_riezaco_{d}_{w}_{t}")
        
        # ========== 9-14. CENTRALES INTERMEDIAS ==========
        for t in self.T:
            for w in self.W:
                # 9. Canecol
                self.model.addConstr(
                    self.qg[5, w, t] == self.QA[5, w, t] - self.qv[5, w, t],
                    name=f"canecol_{w}_{t}")
                
                # 10. Canrucue
                self.model.addConstr(
                    self.qg[6, w, t] == self.qv[5, w, t] - self.qv[6, w, t],
                    name=f"canrucue_{w}_{t}")
                
                # 11. Clajrucue
                self.model.addConstr(
                    self.qg[7, w, t] == self.qv[4, w, t] - self.qv[7, w, t],
                    name=f"clajrucue_{w}_{t}")
                
                # 12. Rucue
                self.model.addConstr(
                    self.qg[8, w, t] == self.qg[6, w, t] + self.qg[7, w, t] - self.qv[8, w, t],
                    name=f"rucue_{w}_{t}")
                
                # 13. Quilleco
                self.model.addConstr(
                    self.qg[9, w, t] == self.qg[8, w, t] + self.qv[8, w, t] - self.qv[9, w, t],
                    name=f"quilleco_{w}_{t}")
                
                # 14. Tucapel
                self.model.addConstr(
                    self.qg[10, w, t] == self.qg[5, w, t] + self.qv[6, w, t] + self.qv[7, w, t] + self.qg[9, w, t] + self.qv[9, w, t] + self.QA[4, w, t] - self.qv[10, w, t],
                    name=f"tucapel_{w}_{t}")
        
        # ========== 15. CANAL LAJA (Central 11) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[11, w, t] == self.qg[10, w, t] + self.qv[10, w, t] - self.qv[11, w, t],
                    name=f"canal_laja_{w}_{t}")
        
        # ========== 16. RIESALTOS (Punto j=3 - Distribución a riego desde vertimiento Canal Laja) ==========
        for t in self.T:
            for w in self.W:
                # El agua disponible para riego Saltos viene del vertimiento de Canal Laja
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 3, w, t] for d in self.D) == self.qv[11, w, t],
                    name=f"riesaltos_disp_{w}_{t}")
                
                # Balance demanda en canal RieSaltos (qp puede ser menor o igual a demanda)
                for d in self.D:
                    self.model.addConstr(
                        self.qp[d, 3, w, t] + self.deficit[d, 3, w, t] >= self.QD.get((d, 3, w), 0),
                        name=f"balance_riesaltos_{d}_{w}_{t}")
        
        # ========== 17. LAJA 1 (Central 13) ==========
        for t in self.T:
            for w in self.W:
                # Si existe afluente 6, incluirlo; si no, solo usar qv[11]
                afluente_6 = self.QA.get((6, w, t), 0)  # 0 si no existe
                self.model.addConstr(
                    self.qg[13, w, t] + self.qv[13, w, t] == self.qv[11, w, t] + afluente_6,
                    name=f"laja1_{w}_{t}")
        
        # ========== 18. EL DIUTO (Central 15) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[15, w, t] == self.qg[11, w, t] - self.qv[15, w, t],
                    name=f"el_diuto_{w}_{t}")
        
        # ========== 19. RIETUCAPEL (Punto j=2 - Distribución a riego desde El Diuto) ==========
        # El agua que pasa por El Diuto (qg[15]) está disponible para riego
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 2, w, t] for d in self.D) == self.qg[15, w, t] + self.qv[15, w, t],
                    name=f"rietucapel_disp_{w}_{t}")
                
                # Balance demanda en canal RieTucapel (qp puede ser menor o igual a demanda)
                for d in self.D:
                    self.model.addConstr(
                        self.qp[d, 2, w, t] + self.deficit[d, 2, w, t] >= self.QD.get((d, 2, w), 0),
                        name=f"balance_rietucapel_{d}_{w}_{t}")
        
        # ========== 20. VERTIMIENTO EL TORO = 0 ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qv[1, w, t] == 0,
                    name=f"no_vert_eltoro_{w}_{t}")
        
        # ========== 21. CAPACIDADES ==========
        for t in self.T:
            for i in self.I:
                for w in self.W:
                    self.model.addConstr(
                        self.qg[i, w, t] <= self.gamma[i],
                        name=f"cap_max_{i}_{w}_{t}")
        
        # ========== 22. DEFINICIÓN DE ENERGÍA GENERADA POR CENTRAL ==========
        # GEN[i,t] = Σ_w (qg[i,w,t] × ρ[i] × FS[w] / (3600 × 1000)) [GWh]
        # Unidades: [m³/s] × [MW/(m³/s)] × [s] / 3,600,000 = [MW·s] / 3,600,000 = [GWh]
        # Nota: ρ está en MW/(m³/s), por lo que qg×ρ×FS da MW·s
        #       Dividir por 3600 convierte a MWh, y por 1000 adicional convierte a GWh
        for t in self.T:
            for i in self.I:
                self.model.addConstr(
                    self.GEN[i, t] == gp.quicksum(
                        self.qg[i, w, t] * self.rho[i] * self.FS[w] / (3600 * 1000)
                        for w in self.W
                    ),
                    name=f"def_energia_{i}_{t}")
        
        print("✓ Restricciones creadas correctamente")
        
    def crear_funcion_objetivo(self):
        """Define la función objetivo"""
        print("Creando función objetivo...")
        
        # Generación total usando la variable GEN (energía en GWh)
        generacion_total = gp.quicksum(
            self.GEN[i, t]
            for i in self.I for t in self.T
        )
        
        # Penalización por déficit de riego (suma de todos los déficits)
        # Convertir déficit de m³/s a volumen (hm³) y luego penalizar
        penalidad_deficit = gp.quicksum(
            self.deficit[d, j, w, t] * self.FS[w] / 1000000  # Convertir a hm³
            for d in self.D for j in self.J for w in self.W for t in self.T
        )
        
        # Penalización por violación de volumen mínimo (suma de todas las betha)
        # betha ya está en hm³
        penalidad_volumen = gp.quicksum(
            self.betha[w, t]
            for w in self.W for t in self.T
        )

        # Función objetivo: Maximizar generación - penalización por déficits - penalización por volumen mínimo
        # psi: penalización por déficit de riego [GWh/hm³]
        # phi: penalización por violación de volumen mínimo [GWh/hm³]
        self.model.setObjective(
            generacion_total - penalidad_deficit * self.psi - penalidad_volumen * self.phi,
            GRB.MAXIMIZE
        )
        
        print("✓ Función objetivo creada correctamente")
        print(f"  - Penalización déficit riego (psi): {self.psi} GWh/hm³")
        print(f"  - Penalización volumen mínimo (phi): {self.phi} GWh/hm³")
        
    def construir_modelo(self):
        """Construye el modelo completo"""
        print("\n" + "="*60)
        print("CONSTRUYENDO MODELO - CUENCA LAJA (5 TEMPORADAS)")
        print("="*60 + "\n")
        
        self.crear_variables()
        self.crear_restricciones()
        self.crear_funcion_objetivo()
        
        self.model.update()
        
        print("\n" + "="*60)
        print("MODELO CONSTRUIDO EXITOSAMENTE")
        print("="*60)
        print(f"Temporadas: {len(self.T)}")
        print(f"Variables: {self.model.NumVars}")
        print(f"Restricciones: {self.model.NumConstrs}")
        print(f"Variables binarias: {self.model.NumBinVars}")
        print("="*60 + "\n")
        
    def optimizar(self, time_limit=None, mip_gap=None):
        """Resuelve el modelo"""
        print("\n" + "="*60)
        print("INICIANDO OPTIMIZACIÓN")
        print("="*60 + "\n")
        
        if time_limit:
            self.model.Params.TimeLimit = time_limit
        # MIPGap solo aplica para modelos MILP, no para LP puros
        # Como este es un modelo LP, no configuramos MIPGap
        
        self.model.optimize()
        
        print("\n" + "="*60)
        print("RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*60)
        
        if self.model.status == GRB.OPTIMAL:
            print("✓ Solución óptima encontrada")
            print(f"Valor objetivo: {self.model.ObjVal:,.2f} GWh")
            print(f"Tiempo de resolución: {self.model.Runtime:.2f} segundos")
        elif self.model.status == GRB.TIME_LIMIT:
            print("⚠ Tiempo límite alcanzado")
            print(f"Mejor solución encontrada: {self.model.ObjVal:,.2f} GWh")
        else:
            print(f"✗ Estado de optimización: {self.model.status}")
        
        print("="*60 + "\n")
        
    def exportar_resultados(self, carpeta_salida="resultados"):
        """Exporta los resultados a archivos CSV"""
        import os
        
        if self.model.status not in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
            print("No hay solución factible para exportar")
            return
        
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"\nExportando resultados a carpeta '{carpeta_salida}'...")
        
        # 1. Generación por central, semana y temporada
        df_generacion = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Temporada': t, 'Caudal_m3s': self.qg[i, w, t].X}
            for i in self.I for w in self.W for t in self.T
        ])
        df_generacion.to_csv(f"{carpeta_salida}/generacion.csv", index=False)
        
        # 2. Vertimientos
        df_vertimientos = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Temporada': t, 'Caudal_m3s': self.qv[i, w, t].X}
            for i in self.I for w in self.W for t in self.T if self.qv[i, w, t].X > 0.01
        ])
        df_vertimientos.to_csv(f"{carpeta_salida}/vertimientos.csv", index=False)
        
        # 3. Volúmenes del lago
        df_volumenes = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Volumen_hm3': self.V[w, t].X}
            for w in self.W for t in self.T
        ])
        df_volumenes.to_csv(f"{carpeta_salida}/volumenes_lago.csv", index=False)
        
        # 3b. Volúmenes por uso
        df_volumenes_uso = pd.DataFrame([
            {'Uso': u, 'Semana': w, 'Temporada': t, 'Volumen_hm3': self.ve[u, w, t].X}
            for u in self.U for w in self.W for t in self.T
        ])
        df_volumenes_uso.to_csv(f"{carpeta_salida}/volumenes_por_uso.csv", index=False)
        
        # 3c. Caudales extraídos por uso
        df_extracciones = pd.DataFrame([
            {'Uso': u, 'Semana': w, 'Temporada': t, 'Caudal_m3s': self.qe[u, w, t].X}
            for u in self.U for w in self.W for t in self.T
        ])
        df_extracciones.to_csv(f"{carpeta_salida}/extracciones_por_uso.csv", index=False)
        
        # 4. Retiros y déficits de riego
        df_riego = pd.DataFrame([
            {
                'Demanda': d,
                'Canal': j,
                'Semana': w,
                'Temporada': t,
                'Demanda_m3s': self.QD.get((d, j, w), 0),
                'Provisto_m3s': self.qp[d, j, w, t].X,
                'Deficit_m3s': self.deficit[d, j, w, t].X
            }
            for d in self.D for j in self.J for w in self.W for t in self.T
        ])
        df_riego.to_csv(f"{carpeta_salida}/riego.csv", index=False)
        
        # 4b. Holguras de volumen mínimo (betha)
        df_betha = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Betha_hm3': self.betha[w, t].X}
            for w in self.W for t in self.T if self.betha[w, t].X > 0.001  # Solo exportar valores no nulos
        ])
        if not df_betha.empty:
            df_betha.to_csv(f"{carpeta_salida}/holguras_volumen.csv", index=False)
            print(f"  ⚠️  Se detectaron {len(df_betha)} violaciones de volumen mínimo")
        
        # 5. Energía generada por central y temporada (usando variable GEN)
        df_energia = pd.DataFrame([
            {
                'Central': i,
                'Temporada': t,
                'Energia_GWh': self.GEN[i, t].X,
                'Energia_MWh': self.GEN[i, t].X * 1000
            }
            for i in self.I for t in self.T
        ])
        df_energia.to_csv(f"{carpeta_salida}/energia_total.csv", index=False)
        
        print("✓ Resultados exportados exitosamente")
