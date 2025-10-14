"""
Modelo de Optimización - Convenio Hidroeléctricas y Riegos Cuenca Laja
Maximizar generación sujeto a cumplir compromisos de riego
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
        self.model = gp.Model("Convenio_Laja")
        
        # Conjuntos (se definirán con los datos)
        self.S = None  # Simulaciones
        self.M = list(range(1, 13))  # Meses
        self.W = list(range(1, 49))  # Semanas hidrológicas
        self.D = [1, 2, 3]  # Demandas (1:Primeros, 2:Segundos, 3:Saltos del Laja)
        self.U = [1, 2]  # Usos (1:Riego, 2:Generación)
        self.I = list(range(1, 17))  # Centrales (1-16)
        self.J = [1, 2, 3]  # Puntos de retiro
        self.A = list(range(1, 7))  # Afluentes (1:ElToro, 2:Abanico, 3:Antuco, 4:Tucapel, 5:Canecol, 6:Laja1)
        self.K = None  # Cotas del lago (se definirá con datos)
        
        # Parámetros (se cargarán desde archivos)
        self.V_30Nov = None  # Volumen del lago al 30 de noviembre
        self.V_0 = None  # Volumen del lago al inicio de la temporada
        self.V_MAX = None
        self.FC = {}  # FC[k]: Filtraciones en cota k
        self.VC = {}  # VC[k]: Volumen en cota k
        self.VUC = {}  # VUC[u,k]: Volumen de uso u en cota k
        self.QA = {}  # QA[a,w]: Caudal afluente a en semana w
        self.QD = {}  # QD[d,j,w]: Caudal demandado por d en canal j en semana w
        self.gamma = {}  # gamma[i]: Caudal máximo central i
        self.rho = {}  # rho[i]: Rendimiento central i
        self.pi = {}  # pi[i]: Potencia máxima central i
        self.FS = {}  # FS[w]: Factor segundos en semana w
        self.psi = None  # Costo incumplir convenio
        self.phi = None  # Costo déficit de riego
        self.M_bigM = 500  # Parámetro Big-M para restricciones
        
        # Variables (se crearán después de cargar datos)
        self.V = {}  # V[w]: Volumen del lago al final de semana w
        self.ca = {}  # ca[k,w]: Binaria si lago en cota k en semana w
        self.ca_0 = {}  # ca[k,0]: Binaria si lago en cota k al inicio de temporada
        self.ca_30Nov = {}  # ca[k,30Nov]: Binaria si lago en cota k al 30 de noviembre
        self.ve = {}  # ve[u,w]: Volumen disponible para uso u en semana w
        self.ve_0 = {}  # ve[u,0]: Volumen disponible para uso u al inicio de temporada
        self.qe = {}  # qe[u,w]: Caudal extraído para uso u en semana w
        self.qf = {}  # qf[w]: Caudal de filtración en semana w
        self.qg = {}  # qg[i,w]: Caudal generación central i en semana w
        self.qv = {}  # qv[i,w]: Caudal vertimiento central i en semana w
        self.qp = {}  # qp[d,j,w]: Caudal provisto para d en canal j en semana w
        self.deficit = {}  # deficit[d,j,w]: Déficit de riego
        self.superavit = {}  # superavit[d,j,w]: Superávit de riego
        self.eta = {}  # eta[d,j,w]: Binaria incumplimiento convenio
        
    def cargar_parametros(self, dict_parametros):
        """
        Carga los parámetros del modelo desde un diccionario
        
        Args:
            dict_parametros: Diccionario con todos los parámetros necesarios
        """
        self.V_30Nov = dict_parametros.get('V_30Nov')
        self.V_0 = dict_parametros.get('V_0')
        self.V_MAX = dict_parametros.get('V_MAX')
        self.FC = dict_parametros.get('FC')
        self.VC = dict_parametros.get('VC')
        self.VUC = dict_parametros.get('VUC')
        self.QA = dict_parametros.get('QA')
        self.QD = dict_parametros.get('QD')
        self.gamma = dict_parametros.get('gamma')
        self.rho = dict_parametros.get('rho')
        self.FS = dict_parametros.get('FS')
        self.psi = dict_parametros.get('psi')
        self.phi = dict_parametros.get('phi')
        
        # Definir conjunto de cotas basado en los datos
        self.K = list(self.VC.keys())
        
        print("✓ Parámetros cargados correctamente")
        
    def crear_variables(self):
        """
        Crea todas las variables de decisión del modelo
        """
        print("Creando variables de decisión...")
        
        # V[w]: Volumen del lago
        self.V = self.model.addVars(self.W, lb=0, ub=self.V_MAX, name="V")
        
        # ca[k,w]: Variable binaria de cota en semana w
        self.ca = self.model.addVars(self.K, self.W, vtype=GRB.BINARY, name="ca")
        
        # ca_0[k]: Variable binaria de cota al inicio de temporada
        self.ca_0 = self.model.addVars(self.K, vtype=GRB.BINARY, name="ca_0")
        
        # ca_30Nov[k]: Variable binaria de cota al 30 de noviembre
        self.ca_30Nov = self.model.addVars(self.K, vtype=GRB.BINARY, name="ca_30Nov")
        
        # ve[u,w]: Volumen disponible para uso u en semana w
        self.ve = self.model.addVars(self.U, self.W, lb=0, name="ve")
        
        # ve_0[u]: Volumen disponible para uso u al inicio de temporada
        self.ve_0 = self.model.addVars(self.U, lb=0, name="ve_0")
        
        # qe[u,w]: Caudal extraído por uso
        self.qe = self.model.addVars(self.U, self.W, lb=0, name="qe")
        
        # qf[w]: Caudal de filtración
        self.qf = self.model.addVars(self.W, lb=0, name="qf")
        
        # qg[i,w]: Caudal de generación
        self.qg = self.model.addVars(self.I, self.W, lb=0, name="qg")
        
        # qv[i,w]: Caudal de vertimiento
        self.qv = self.model.addVars(self.I, self.W, lb=0, name="qv")
        
        # qp[d,j,w]: Caudal provisto para riego
        self.qp = self.model.addVars(self.D, self.J, self.W, lb=0, name="qp")
        
        # deficit[d,j,w]: Déficit de riego
        self.deficit = self.model.addVars(self.D, self.J, self.W, lb=0, name="deficit")
        
        # superavit[d,j,w]: Superávit de riego
        self.superavit = self.model.addVars(self.D, self.J, self.W, lb=0, name="superavit")
        
        # eta[d,j,w]: Incumplimiento de convenio
        self.eta = self.model.addVars(self.D, self.J, self.W, vtype=GRB.BINARY, name="eta")
        
        print("✓ Variables creadas correctamente")
        
    def crear_restricciones(self):
        """
        Crea todas las restricciones del modelo
        """
        print("Creando restricciones...")
        
        # ========== 1. DEFINICIÓN DE VARIABLE DE COTAS ==========
        # Restricciones para V_30Nov (medición del 30 de noviembre)
        for i, k in enumerate(self.K[:-1]):
            k_next = self.K[i + 1]
            M_vol = self.V_MAX * 2
            
            # V_30Nov <= VC[k+1] + M*(1 - ca_30Nov[k])
            self.model.addConstr(
                self.V_30Nov <= self.VC[k_next] + M_vol * (1 - self.ca_30Nov[k]),
                name=f"cota_30Nov_sup_{k}"
            )
            
            # V_30Nov >= VC[k] - M*(1 - ca_30Nov[k])
            self.model.addConstr(
                self.V_30Nov >= self.VC[k] - M_vol * (1 - self.ca_30Nov[k]),
                name=f"cota_30Nov_inf_{k}"
            )
        
        # Exactamente una cota activa para V_30Nov
        self.model.addConstr(
            gp.quicksum(self.ca_30Nov[k] for k in self.K[:-1]) == 1,
            name="una_cota_30Nov"
        )
        
        # Restricciones para V_0 (inicio de temporada)
        for i, k in enumerate(self.K[:-1]):
            k_next = self.K[i + 1]
            M_vol = self.V_MAX * 2
            
            # V_0 <= VC[k+1] + M*(1 - ca_0[k])
            self.model.addConstr(
                self.V_0 <= self.VC[k_next] + M_vol * (1 - self.ca_0[k]),
                name=f"cota_0_sup_{k}"
            )
            
            # V_0 >= VC[k] - M*(1 - ca_0[k])
            self.model.addConstr(
                self.V_0 >= self.VC[k] - M_vol * (1 - self.ca_0[k]),
                name=f"cota_0_inf_{k}"
            )
        
        # Exactamente una cota activa para V_0
        self.model.addConstr(
            gp.quicksum(self.ca_0[k] for k in self.K[:-1]) == 1,
            name="una_cota_0"
        )
        
        # Restricciones para V[w] (cada semana)
        for w in self.W:
            for i, k in enumerate(self.K[:-1]):
                k_next = self.K[i + 1]
                M_vol = self.V_MAX * 2
                
                # V[w] <= VC[k+1] + M*(1 - ca[k,w])
                self.model.addConstr(
                    self.V[w] <= self.VC[k_next] + M_vol * (1 - self.ca[k, w]),
                    name=f"cota_sup_{k}_{w}"
                )
                
                # V[w] >= VC[k] - M*(1 - ca[k,w])
                self.model.addConstr(
                    self.V[w] >= self.VC[k] - M_vol * (1 - self.ca[k, w]),
                    name=f"cota_inf_{k}_{w}"
                )
            
            # Exactamente una cota activa por semana
            self.model.addConstr(
                gp.quicksum(self.ca[k, w] for k in self.K[:-1]) == 1,
                name=f"una_cota_{w}"
            )
        
        # ========== 2. DEFINICIÓN DE FILTRACIONES ==========
        for w in self.W:
            self.model.addConstr(
                self.qf[w] == gp.quicksum(self.ca[k, w] * self.FC[k] for k in self.K[:-1]),
                name=f"filtracion_{w}"
            )
        
        # ========== 3. GENERACIÓN EN EL TORO ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[1, w] == gp.quicksum(self.qe[u, w] for u in self.U),
                name=f"gen_eltoro_{w}"
            )
        
        # ========== 4. VOLÚMENES DISPONIBLES ==========
        # Balance de volumen del lago: V_w = V_{w-1} + (QA_{1,w} - qg_{1,w} - qf_w) * FS_w / 1000000
        for w in self.W:
            if w == 1:
                # Primera semana: V_1 = V_0 + (QA_{1,1} - qg_{1,1} - qf_1) * FS_1 / 1000000
                self.model.addConstr(
                    self.V[w] == self.V_0 + (self.QA[1, w] - self.qg[1, w] - self.qf[w]) * self.FS[w] / 1000000,
                    name=f"balance_vol_{w}"
                )
            else:
                # Semanas siguientes
                self.model.addConstr(
                    self.V[w] == self.V[w-1] + (self.QA[1, w] - self.qg[1, w] - self.qf[w]) * self.FS[w] / 1000000,
                    name=f"balance_vol_{w}"
                )
        
        # Volumen disponible para uso u al inicio: ve_{u,0} = sum(ca_30Nov[k] * VUC[u,k])
        for u in self.U:
            self.model.addConstr(
                self.ve_0[u] == gp.quicksum(self.ca_30Nov[k] * self.VUC[(u, k)] for k in self.K[:-1]),
                name=f"ve_inicial_{u}"
            )
        
        # Balance de volumen por uso: ve_{u,w} = ve_{u,w-1} - qe_{u,w} * FS_w / 1000000
        for u in self.U:
            for w in self.W:
                if w == 1:
                    # Primera semana
                    self.model.addConstr(
                        self.ve[u, w] == self.ve_0[u] - self.qe[u, w] * self.FS[w] / 1000000,
                        name=f"balance_ve_{u}_{w}"
                    )
                else:
                    # Semanas siguientes
                    self.model.addConstr(
                        self.ve[u, w] == self.ve[u, w-1] - self.qe[u, w] * self.FS[w] / 1000000,
                        name=f"balance_ve_{u}_{w}"
                    )
        
        # ========== 5. LAJA FILTRACIONES (Central 16) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[16, w] == self.qf[w],
                name=f"laja_filt_{w}"
            )
        
        # ========== 6. ABANICO (Central 2) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[2, w] == self.QA[2, w] + self.qg[16, w] - self.qv[2, w],
                name=f"abanico_{w}"
            )
        
        # ========== 7. ANTUCO (Central 3) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[3, w] == self.QA[3, w] + self.qg[1, w] + self.qg[2, w] + self.qv[2, w] - self.qv[3, w],
                name=f"antuco_{w}"
            )
        
        # ========== 8. RIEGZACO (Central 4 - Punto de retiro j=1) ==========
        for w in self.W:
            # Caudal total disponible en RieZaCo se distribuye entre todos los demandantes
            self.model.addConstr(
                gp.quicksum(self.qp[d, 1, w] for d in self.D) == self.qg[3, w] + self.qv[3, w] - self.qv[4, w],
                name=f"riezaco_disp_{w}"
            )
            
            for d in self.D:
                # Balance demanda
                self.model.addConstr(
                    self.QD[d, 1, w] - self.qp[d, 1, w] == self.deficit[d, 1, w] - self.superavit[d, 1, w],
                    name=f"balance_riezaco_{d}_{w}"
                )
                
                # Big-M para incumplimiento
                self.model.addConstr(
                    self.deficit[d, 1, w] <= self.M_bigM * self.eta[d, 1, w],
                    name=f"bigM_riezaco_{d}_{w}"
                )
        
        # ========== 9. CANECOL (Central 5) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[5, w] == self.QA[5, w] - self.qv[5, w],
                name=f"canecol_{w}"
            )
        
        # ========== 10. CANRUCUE (Central 6) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[6, w] == self.qv[5, w] - self.qv[6, w],
                name=f"canrucue_{w}"
            )
        
        # ========== 11. CLAJRUCUE (Central 7) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[7, w] == self.qv[4, w] - self.qv[7, w],
                name=f"clajrucue_{w}"
            )
        
        # ========== 12. RUCUE (Central 8) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[8, w] == self.qg[6, w] + self.qg[7, w] - self.qv[8, w],
                name=f"rucue_{w}"
            )
        
        # ========== 13. QUILLECO (Central 9) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[9, w] == self.qg[8, w] + self.qv[8, w] - self.qv[9, w],
                name=f"quilleco_{w}"
            )
        
        # ========== 14. TUCAPEL (Central 10) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[10, w] == self.qg[5, w] + self.qv[6, w] + self.qv[7, w] + self.qg[9, w] + self.qv[9, w] + self.QA[4, w] - self.qv[10, w],
                name=f"tucapel_{w}"
            )
        
        # ========== 15. CANAL LAJA (Central 11) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[11, w] == self.qg[10, w] + self.qv[10, w] - self.qv[11, w],
                name=f"canal_laja_{w}"
            )
        
        # ========== 16. RIESALTOS (Central 12 - Punto de retiro j=3) ==========
        for w in self.W:
            # Caudal total disponible en RieSaltos se distribuye entre todos los demandantes
            self.model.addConstr(
                gp.quicksum(self.qp[d, 3, w] for d in self.D) == self.qv[11, w] - self.qv[12, w],
                name=f"riesaltos_disp_{w}"
            )
            
            for d in self.D:
                # Balance demanda
                self.model.addConstr(
                    self.QD[d, 3, w] - self.qp[d, 3, w] == self.deficit[d, 3, w] - self.superavit[d, 3, w],
                    name=f"balance_riesaltos_{d}_{w}"
                )
                
                # Big-M para incumplimiento
                self.model.addConstr(
                    self.deficit[d, 3, w] <= self.M_bigM * self.eta[d, 3, w],
                    name=f"bigM_riesaltos_{d}_{w}"
                )
        
        # ========== 17. LAJA 1 (Central 13) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[13, w] + self.qv[13, w] == self.qv[11, w] + self.QA[6, w],
                name=f"laja1_{w}"
            )
        
        # ========== 18. EL DIUTO (Central 15) ==========
        for w in self.W:
            self.model.addConstr(
                self.qg[15, w] == self.qg[11, w] - self.qv[15, w],
                name=f"el_diuto_{w}"
            )
        
        # ========== 19. RIETUCAPEL (Central 14 - Punto de retiro j=2) ==========
        for w in self.W:
            # Caudal total disponible en RieTucapel se distribuye entre todos los demandantes
            self.model.addConstr(
                gp.quicksum(self.qp[d, 2, w] for d in self.D) == self.qg[15, w] + self.qv[15, w],
                name=f"rietucapel_disp_{w}"
            )
            
            for d in self.D:
                # Balance demanda
                self.model.addConstr(
                    self.QD[d, 2, w] - self.qp[d, 2, w] == self.deficit[d, 2, w] - self.superavit[d, 2, w],
                    name=f"balance_rietucapel_{d}_{w}"
                )
                
                # Big-M para incumplimiento
                self.model.addConstr(
                    self.deficit[d, 2, w] <= self.M_bigM * self.eta[d, 2, w],
                    name=f"bigM_rietucapel_{d}_{w}"
                )
        
        # ========== 20. VERTIMIENTO EL TORO = 0 ==========
        for w in self.W:
            self.model.addConstr(
                self.qv[1, w] == 0,
                name=f"no_vert_eltoro_{w}"
            )
        
        # ========== 21. CAPACIDADES ==========
        for i in self.I:
            for w in self.W:
                self.model.addConstr(
                    self.qg[i, w] <= self.gamma[i],
                    name=f"cap_max_{i}_{w}"
                )
        
        print("✓ Restricciones creadas correctamente")
        
    def crear_funcion_objetivo(self):
        """
        Define la función objetivo: Maximizar generación - penalidades
        """
        print("Creando función objetivo...")
        
        # Generación total (energía en MWh)
        generacion_total = gp.quicksum(
            self.qg[i, w] * self.rho[i] * self.FS[w]
            for i in self.I for w in self.W
        )
        
        # Penalidad por incumplimiento de convenio
        penalidad_incumplimiento = gp.quicksum(
            self.eta[d, j, w] * self.psi
            for d in self.D for j in self.J for w in self.W
        )
        
        # Penalidad por déficit de riego
        penalidad_deficit = gp.quicksum(
            self.deficit[d, j, w] * self.phi
            for d in self.D for j in self.J for w in self.W
        )

        # Función objetivo: Maximizar generación - penalidades
        self.model.setObjective(
            generacion_total - penalidad_incumplimiento - penalidad_deficit,
            GRB.MAXIMIZE
        )
        
        print("✓ Función objetivo creada correctamente")
        
    def construir_modelo(self):
        """
        Construye el modelo completo
        """
        print("\n" + "="*60)
        print("CONSTRUYENDO MODELO DE OPTIMIZACIÓN - CUENCA LAJA")
        print("="*60 + "\n")
        
        self.crear_variables()
        self.crear_restricciones()
        self.crear_funcion_objetivo()
        
        self.model.update()
        
        print("\n" + "="*60)
        print("MODELO CONSTRUIDO EXITOSAMENTE")
        print("="*60)
        print(f"Variables: {self.model.NumVars}")
        print(f"Restricciones: {self.model.NumConstrs}")
        print(f"Variables binarias: {self.model.NumBinVars}")
        print("="*60 + "\n")
        
    def optimizar(self, time_limit=None, mip_gap=None):
        """
        Resuelve el modelo de optimización
        
        Args:
            time_limit: Tiempo límite en segundos (None = sin límite)
            mip_gap: Gap de optimalidad (None = 0.01%)
        """
        print("\n" + "="*60)
        print("INICIANDO OPTIMIZACIÓN")
        print("="*60 + "\n")
        
        # Configurar parámetros de Gurobi
        if time_limit:
            self.model.Params.TimeLimit = time_limit
        if mip_gap:
            self.model.Params.MIPGap = mip_gap
        else:
            self.model.Params.MIPGap = 0.0001  # 0.01% por defecto
        
        # Resolver
        self.model.optimize()
        
        # Mostrar resultados
        print("\n" + "="*60)
        print("RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*60)
        
        if self.model.status == GRB.OPTIMAL:
            print("✓ Solución óptima encontrada")
            print(f"Valor objetivo: {self.model.ObjVal:,.2f} MWh")
            print(f"Gap de optimalidad: {self.model.MIPGap*100:.4f}%")
            print(f"Tiempo de resolución: {self.model.Runtime:.2f} segundos")
        elif self.model.status == GRB.TIME_LIMIT:
            print("⚠ Tiempo límite alcanzado")
            print(f"Mejor solución encontrada: {self.model.ObjVal:,.2f} MWh")
            print(f"Gap de optimalidad: {self.model.MIPGap*100:.2f}%")
        else:
            print(f"✗ Estado de optimización: {self.model.status}")
        
        print("="*60 + "\n")
        
    def exportar_resultados(self, carpeta_salida="resultados"):
        """
        Exporta los resultados a archivos CSV
        
        Args:
            carpeta_salida: Carpeta donde guardar los resultados
        """
        import os
        
        if self.model.status not in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
            print("No hay solución factible para exportar")
            return
        
        # Crear carpeta si no existe
        os.makedirs(carpeta_salida, exist_ok=True)
        
        print(f"\nExportando resultados a carpeta '{carpeta_salida}'...")
        
        # 1. Generación por central y semana
        df_generacion = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Caudal_m3s': self.qg[i, w].X}
            for i in self.I for w in self.W
        ])
        df_generacion.to_csv(f"{carpeta_salida}/generacion.csv", index=False)
        
        # 2. Vertimientos
        df_vertimientos = pd.DataFrame([
            {'Central': i, 'Semana': w, 'Caudal_m3s': self.qv[i, w].X}
            for i in self.I for w in self.W if self.qv[i, w].X > 0.01
        ])
        df_vertimientos.to_csv(f"{carpeta_salida}/vertimientos.csv", index=False)
        
        # 3. Volúmenes del lago
        df_volumenes = pd.DataFrame([
            {'Semana': w, 'Volumen_hm3': self.V[w].X}
            for w in self.W
        ])
        df_volumenes.to_csv(f"{carpeta_salida}/volumenes_lago.csv", index=False)
        
        # 4. Retiros y déficits de riego
        df_riego = pd.DataFrame([
            {
                'Demanda': d, 
                'Canal': j, 
                'Semana': w, 
                'Demanda_m3s': self.QD[d, j, w],
                'Provisto_m3s': self.qp[d, j, w].X,
                'Deficit_m3s': self.deficit[d, j, w].X,
                'Incumplimiento': self.eta[d, j, w].X
            }
            for d in self.D for j in self.J for w in self.W
        ])
        df_riego.to_csv(f"{carpeta_salida}/riego.csv", index=False)
        
        # 5. Resumen de energía por central
        df_energia = pd.DataFrame([
            {
                'Central': i,
                'Energia_Total_MWh': sum(self.qg[i, w].X * self.rho[i] * self.FS[w] for w in self.W)
            }
            for i in self.I
        ])
        df_energia.to_csv(f"{carpeta_salida}/energia_total.csv", index=False)
        
        print("✓ Resultados exportados exitosamente")
        

def ejemplo_uso():
    """
    Ejemplo de cómo usar el modelo (con datos ficticios)
    """
    # Crear instancia del modelo
    modelo = ModeloLaja()
    
    # Aquí deberías cargar tus datos reales
    # Por ahora creamos datos de ejemplo mínimos
    
    # Ejemplo de estructura de parámetros (DEBES REEMPLAZAR CON TUS DATOS)
    parametros = {
        'V_30Nov': 1000,  # hm3
        'V_MAX': 2000,    # hm3
        'FC': {k: 0.5 for k in range(1, 79)},  # Filtraciones
        'VC': {k: k * 25 for k in range(1, 79)},  # Volúmenes por cota
        'VUC': {(u, k): k * 10 for u in [1, 2] for k in range(1, 79)},  # Vol uso
        'QA': {(a, w): 50 for a in range(1, 6) for w in range(1, 49)},  # Afluentes
        'QD': {(d, j, w): 10 for d in [1, 2, 3] for j in [1, 2, 3] for w in range(1, 49)},  # Demandas
        'gamma': {i: 100 for i in range(1, 17)},  # Caudal máximo
        'rho': {i: 0.5 if i not in [4, 12, 14] else 0 for i in range(1, 17)},  # Rendimiento
        'pi': {i: 50 for i in range(1, 17)},  # Potencia máxima
        'FS': {w: 604800 for w in range(1, 49)},  # Segundos por semana
        'psi': 1000,  # Costo incumplimiento
        'phi': 100,   # Costo déficit
    }
    
    # Cargar parámetros
    modelo.cargar_parametros(parametros)
    
    # Construir modelo
    modelo.construir_modelo()
    
    # Optimizar
    modelo.optimizar(time_limit=300)  # 5 minutos máximo
    
    # Exportar resultados
    modelo.exportar_resultados()
    

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MODELO DE OPTIMIZACIÓN - CUENCA DEL LAJA")
    print("Convenio Hidroeléctricas y Riegos")
    print("="*60 + "\n")
    
    print("Para usar este modelo, debes:")
    print("1. Cargar tus datos reales en un diccionario")
    print("2. Llamar a modelo.cargar_parametros(dict_parametros)")
    print("3. Ejecutar modelo.construir_modelo()")
    print("4. Ejecutar modelo.optimizar()")
    print("5. Exportar resultados con modelo.exportar_resultados()")
    print("\n" + "="*60 + "\n")
