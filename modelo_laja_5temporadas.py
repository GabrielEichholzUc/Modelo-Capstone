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
        self.M_bigM = None  # Parámetro Big-M (se carga desde Excel)
        
        # Variables
        self.V_30Nov = {}  # V_30Nov[t]: Volumen al 30 Nov previo a temp t
        self.V = {}  # V[w,t]: Volumen al final de semana w de temporada t
        self.ca = {}  # ca[k,w,t]: Binaria cota
        self.ca_0 = {}  # ca[k,0]: Binaria cota inicial
        self.ca_30Nov = {}  # ca[k,30Nov,t]: Binaria cota 30 Nov
        self.ve = {}  # ve[u,w,t]: Volumen disponible
        self.ve_0 = {}  # ve[u,0,t]: Volumen disponible inicial
        self.qe = {}  # qe[u,w,t]: Caudal extraído
        self.qf = {}  # qf[w,t]: Caudal de filtración
        self.qg = {}  # qg[i,w,t]: Caudal generación
        self.qv = {}  # qv[i,w,t]: Caudal vertimiento
        self.qp = {}  # qp[d,j,w,t]: Caudal provisto riego
        self.deficit = {}  # deficit[d,j,w,t]
        self.superavit = {}  # superavit[d,j,w,t]
        self.eta = {}  # eta[d,j,w,t]: Binaria incumplimiento
        self.alpha = {}  # alpha[w,t]: Binaria Abanico(1) vs Tucapel(0)
        self.beta = {}  # beta[w,t]: Binaria umbral 1400 hm³
        self.GEN = {}  # GEN[i,t]: Energía generada [GWh] por central i en temporada t
        
    def cargar_parametros(self, dict_parametros):
        """Carga los parámetros del modelo"""
        self.V_30Nov_1 = dict_parametros.get('V_30Nov_1', dict_parametros.get('V_30Nov'))
        self.V_0 = dict_parametros.get('V_0')
        self.V_MAX = dict_parametros.get('V_MAX')
        self.FC = dict_parametros.get('FC')
        self.VC = dict_parametros.get('VC')
        self.VUC = dict_parametros.get('VUC')
        self.QA = dict_parametros.get('QA')
        self.QD = dict_parametros.get('QD')
        self.gamma = dict_parametros.get('gamma')
        self.rho = dict_parametros.get('rho')
        self.pi = dict_parametros.get('pi')
        self.FS = dict_parametros.get('FS')
        self.psi = dict_parametros.get('psi')
        self.phi = dict_parametros.get('phi')
        self.V_min = dict_parametros.get('V_min', 1400)  # Default 1400 si no está en Excel
        self.M_bigM = dict_parametros.get('M', 10000)  # Default 10000 si no está en Excel
        self.K = list(self.VC.keys())
        print("✓ Parámetros cargados correctamente")
        
    def crear_variables(self):
        """Crea todas las variables de decisión"""
        print("Creando variables de decisión...")
        
        # Volúmenes del lago
        self.V_30Nov = self.model.addVars(self.T, lb=0, ub=self.V_MAX, name="V_30Nov")
        self.V = self.model.addVars(self.W, self.T, lb=0, ub=self.V_MAX, name="V")
        
        # Variables de cota
        self.ca = self.model.addVars(self.K, self.W, self.T, vtype=GRB.BINARY, name="ca")
        self.ca_0 = self.model.addVars(self.K, vtype=GRB.BINARY, name="ca_0")
        self.ca_30Nov = self.model.addVars(self.K, self.T, vtype=GRB.BINARY, name="ca_30Nov")
        
        # Volúmenes por uso
        self.ve = self.model.addVars(self.U, self.W, self.T, lb=0, name="ve")
        self.ve_0 = self.model.addVars(self.U, self.T, lb=0, name="ve_0")
        
        # Caudales
        self.qe = self.model.addVars(self.U, self.W, self.T, lb=0, name="qe")
        self.qf = self.model.addVars(self.W, self.T, lb=0, name="qf")
        self.qg = self.model.addVars(self.I, self.W, self.T, lb=0, name="qg")
        self.qv = self.model.addVars(self.I, self.W, self.T, lb=0, name="qv")
        self.qp = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="qp")
        
        # Déficit y superávit
        self.deficit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="deficit")
        self.superavit = self.model.addVars(self.D, self.J, self.W, self.T, lb=0, name="superavit")
        
        # Variables binarias
        self.eta = self.model.addVars(self.D, self.J, self.W, self.T, vtype=GRB.BINARY, name="eta")
        self.alpha = self.model.addVars(self.W, self.T, vtype=GRB.BINARY, name="alpha")
        self.beta = self.model.addVars(self.W, self.T, vtype=GRB.BINARY, name="beta")
        
        # Variable de energía generada por central y temporada [GWh]
        self.GEN = self.model.addVars(self.I, self.T, lb=0, name="GEN")
        
        print("✓ Variables creadas correctamente")
        
    def crear_restricciones(self):
        """Crea todas las restricciones del modelo"""
        print("Creando restricciones...")
        M_vol = self.V_MAX * 2
        
        # ========== 1. DEFINICIÓN DE VARIABLE DE COTAS ==========
        # Cota al 30 Nov de cada temporada
        for t in self.T:
            for i, k in enumerate(self.K[:-1]):
                k_next = self.K[i + 1]
                self.model.addConstr(
                    self.V_30Nov[t] <= self.VC[k_next] + M_vol * (1 - self.ca_30Nov[k, t]),
                    name=f"cota_30Nov_sup_{k}_{t}")
                self.model.addConstr(
                    self.V_30Nov[t] >= self.VC[k] - M_vol * (1 - self.ca_30Nov[k, t]),
                    name=f"cota_30Nov_inf_{k}_{t}")
            
            self.model.addConstr(
                gp.quicksum(self.ca_30Nov[k, t] for k in self.K[:-1]) == 1,
                name=f"una_cota_30Nov_{t}")
        
        # Cota inicial (solo temporada 1)
        for i, k in enumerate(self.K[:-1]):
            k_next = self.K[i + 1]
            self.model.addConstr(
                self.V_0 <= self.VC[k_next] + M_vol * (1 - self.ca_0[k]),
                name=f"cota_0_sup_{k}")
            self.model.addConstr(
                self.V_0 >= self.VC[k] - M_vol * (1 - self.ca_0[k]),
                name=f"cota_0_inf_{k}")
        
        self.model.addConstr(
            gp.quicksum(self.ca_0[k] for k in self.K[:-1]) == 1,
            name="una_cota_0")
        
        # Cotas semanales
        for t in self.T:
            for w in self.W:
                for i, k in enumerate(self.K[:-1]):
                    k_next = self.K[i + 1]
                    self.model.addConstr(
                        self.V[w, t] <= self.VC[k_next] + M_vol * (1 - self.ca[k, w, t]),
                        name=f"cota_sup_{k}_{w}_{t}")
                    self.model.addConstr(
                        self.V[w, t] >= self.VC[k] - M_vol * (1 - self.ca[k, w, t]),
                        name=f"cota_inf_{k}_{w}_{t}")
                
                self.model.addConstr(
                    gp.quicksum(self.ca[k, w, t] for k in self.K[:-1]) == 1,
                    name=f"una_cota_{w}_{t}")
        
        # ========== 2. DEFINICIÓN DE FILTRACIONES ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qf[w, t] == gp.quicksum(self.ca[k, w, t] * self.FC[k] for k in self.K[:-1]),
                    name=f"filtracion_{w}_{t}")
        
        # ========== 3. GENERACIÓN EN EL TORO ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[1, w, t] == gp.quicksum(self.qe[u, w, t] for u in self.U),
                    name=f"gen_eltoro_{w}_{t}")
        
        # ========== 4. VOLÚMENES DISPONIBLES ==========
        # Balance volumen del lago
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
        
        # Volumen disponible por uso al inicio de cada temporada
        for t in self.T:
            for u in self.U:
                self.model.addConstr(
                    self.ve_0[u, t] == gp.quicksum(self.ca_30Nov[k, t] * self.VUC[(u, k)] for k in self.K[:-1]),
                    name=f"ve_inicial_{u}_{t}")
        
        # Balance volumen por uso
        for t in self.T:
            for u in self.U:
                for w in self.W:
                    if w == 1:
                        self.model.addConstr(
                            self.ve[u, w, t] == self.ve_0[u, t] - self.qe[u, w, t] * self.FS[w] / 1000000,
                            name=f"balance_ve_{u}_{w}_{t}")
                    else:
                        self.model.addConstr(
                            self.ve[u, w, t] == self.ve[u, w-1, t] - self.qe[u, w, t] * self.FS[w] / 1000000,
                            name=f"balance_ve_{u}_{w}_{t}")
        
        # ========== 5. LAJA FILTRACIONES (Central 16) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[16, w, t] == self.qf[w, t],
                    name=f"laja_filt_{w}_{t}")
        
        # ========== 6. ABANICO (Central 2 + Canal j=4) ==========
        for t in self.T:
            for w in self.W:
                # Balance central Abanico
                self.model.addConstr(
                    self.qg[2, w, t] == self.QA[2, w, t] + self.qg[16, w, t] - self.qv[2, w, t],
                    name=f"abanico_{w}_{t}")
                
                # Distribución a regantes en canal Abanico
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 4, w, t] for d in self.D) == self.qg[2, w, t] + self.qv[2, w, t],
                    name=f"abanico_canal_{w}_{t}")
                
                # Balance demanda en canal Abanico
                for d in self.D:
                    self.model.addConstr(
                        self.QD.get((d, 4, w), 0) - self.qp[d, 4, w, t] == self.deficit[d, 4, w, t] - self.superavit[d, 4, w, t],
                        name=f"balance_abanico_{d}_{w}_{t}")
                
                # Big-M para primeros regantes en Abanico (d=1, j=4)
                self.model.addConstr(
                    self.deficit[1, 4, w, t] <= self.M_bigM * (1 + self.eta[1, 4, w, t] - self.alpha[w, t]),
                    name=f"bigM_abanico_1_{w}_{t}")
                
                # Para segundos y emergencia en Abanico
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 4, w, t] <= self.M_bigM * self.eta[d, 4, w, t],
                        name=f"bigM_abanico_{d}_{w}_{t}")
        
        # ========== 7. ANTUCO (Central 3) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[3, w, t] == self.QA[3, w, t] + self.qg[1, w, t] + self.qg[2, w, t] + self.qv[2, w, t] - self.qv[3, w, t],
                    name=f"antuco_{w}_{t}")
        
        # ========== 8. RIEZACO (Central 4 - Punto j=1) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 1, w, t] for d in self.D) == self.qg[3, w, t] + self.qv[3, w, t] - self.qv[4, w, t],
                    name=f"riezaco_disp_{w}_{t}")
                
                for d in self.D:
                    self.model.addConstr(
                        self.QD.get((d, 1, w), 0) - self.qp[d, 1, w, t] == self.deficit[d, 1, w, t] - self.superavit[d, 1, w, t],
                        name=f"balance_riezaco_{d}_{w}_{t}")
                
                # Para primeros regantes (d=1): déficit solo si incumplimiento o alpha=1 (Abanico)
                self.model.addConstr(
                    self.deficit[1, 1, w, t] <= self.M_bigM * (self.eta[1, 1, w, t] + self.alpha[w, t]),
                    name=f"bigM_riezaco_1_{w}_{t}")
                
                # Para segundos y emergencia
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 1, w, t] <= self.M_bigM * self.eta[d, 1, w, t],
                        name=f"bigM_riezaco_{d}_{w}_{t}")
        
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
        
        # ========== 16. RIESALTOS (Central 12 - Punto j=3) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qp[3, 3, w, t] == self.qv[11, w, t],
                    name=f"riesaltos_disp_{w}_{t}")
                
                for d in self.D:
                    self.model.addConstr(
                        self.QD.get((d, 3, w), 0) - self.qp[d, 3, w, t] == self.deficit[d, 3, w, t] - self.superavit[d, 3, w, t],
                        name=f"balance_riesaltos_{d}_{w}_{t}")
                    
                    self.model.addConstr(
                        self.deficit[d, 3, w, t] <= self.M_bigM * self.eta[d, 3, w, t],
                        name=f"bigM_riesaltos_{d}_{w}_{t}")
        
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
        
        # ========== 19. RIETUCAPEL (Central 14 - Punto j=2) ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    gp.quicksum(self.qp[d, 2, w, t] for d in self.D) == self.qg[15, w, t] + self.qv[15, w, t],
                    name=f"rietucapel_disp_{w}_{t}")
                
                for d in self.D:
                    self.model.addConstr(
                        self.QD.get((d, 2, w), 0) - self.qp[d, 2, w, t] == self.deficit[d, 2, w, t] - self.superavit[d, 2, w, t],
                        name=f"balance_rietucapel_{d}_{w}_{t}")
                
                # Para primeros regantes (d=1): déficit solo si incumplimiento o alpha=1 (Abanico)
                self.model.addConstr(
                    self.deficit[1, 2, w, t] <= self.M_bigM * (self.eta[1, 2, w, t] + self.alpha[w, t]),
                    name=f"bigM_rietucapel_1_{w}_{t}")
                
                # Para segundos y emergencia
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 2, w, t] <= self.M_bigM * self.eta[d, 2, w, t],
                        name=f"bigM_rietucapel_{d}_{w}_{t}")
        
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
        
        # ========== 22. VOLUMEN MÍNIMO DEL LAGO ==========
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.V[w, t] >= self.V_min - self.M_bigM * self.beta[w, t],
                    name=f"vol_min_{w}_{t}")
        
        # ========== 23. DEFINICIÓN DE ENERGÍA GENERADA POR CENTRAL ==========
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
        
        # Penalidad por incumplimiento de convenio
        penalidad_incumplimiento = gp.quicksum(
            self.eta[d, j, w, t] * self.psi
            for d in self.D for j in self.J for w in self.W for t in self.T
        )
        
        # Penalidad por bajar del umbral de 1400 hm³
        penalidad_umbral = gp.quicksum(
            self.beta[w, t] * self.phi
            for w in self.W for t in self.T
        )

        self.model.setObjective(
            generacion_total - penalidad_incumplimiento - penalidad_umbral,
            GRB.MAXIMIZE
        )
        
        print("✓ Función objetivo creada correctamente")
        
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
        if mip_gap:
            self.model.Params.MIPGap = mip_gap
        else:
            self.model.Params.MIPGap = 0.01  # 1% por defecto
        
        self.model.optimize()
        
        print("\n" + "="*60)
        print("RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*60)
        
        if self.model.status == GRB.OPTIMAL:
            print("✓ Solución óptima encontrada")
            print(f"Valor objetivo: {self.model.ObjVal:,.2f} GWh")
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
        
        # 4. Retiros y déficits de riego
        df_riego = pd.DataFrame([
            {
                'Demanda': d,
                'Canal': j,
                'Semana': w,
                'Temporada': t,
                'Demanda_m3s': self.QD.get((d, j, w), 0),
                'Provisto_m3s': self.qp[d, j, w, t].X,
                'Deficit_m3s': self.deficit[d, j, w, t].X,
                'Incumplimiento': self.eta[d, j, w, t].X
            }
            for d in self.D for j in self.J for w in self.W for t in self.T
        ])
        df_riego.to_csv(f"{carpeta_salida}/riego.csv", index=False)
        
        # 5. Variable alpha (decisión Abanico vs Tucapel)
        df_alpha = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Alpha': self.alpha[w, t].X}
            for w in self.W for t in self.T
        ])
        df_alpha.to_csv(f"{carpeta_salida}/decision_alpha.csv", index=False)
        
        # 6. Variable beta (umbral 1400 hm³)
        df_beta = pd.DataFrame([
            {'Semana': w, 'Temporada': t, 'Beta': self.beta[w, t].X}
            for w in self.W for t in self.T
        ])
        df_beta.to_csv(f"{carpeta_salida}/decision_beta.csv", index=False)
        
        # 7. Energía generada por central y temporada (usando variable GEN)
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
