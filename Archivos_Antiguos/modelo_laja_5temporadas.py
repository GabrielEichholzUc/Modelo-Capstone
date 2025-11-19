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
        
        # Definición de la Topología de Red (Origen -> Nodo -> Destino)
        # Estructura: {'nodo': NombreDelNodoBalance, 'tipo': 'in'/'out', 'var': Variable, 'idx': Indice}
        self.ARCOS_RED = [
            # -------------------------------------------------------
            # 1. NODO: CENTRAL EL TORO (Balance Restricción 3)
            # -------------------------------------------------------
            {'nodo': 'ElToro', 'tipo': 'in',  'var': 'qe', 'idx': 1}, # Extracción Riego del Lago
            {'nodo': 'ElToro', 'tipo': 'in',  'var': 'qe', 'idx': 2}, # Extracción Generación del Lago
            {'nodo': 'ElToro', 'tipo': 'out', 'var': 'qg', 'idx': 1}, # Generación El Toro

            # -------------------------------------------------------
            # 2. NODO: ABANICO (Balance Restricción 7 + 6)
            # -------------------------------------------------------
            {'nodo': 'Abanico', 'tipo': 'in',  'var': 'qa', 'idx': 2}, # Afluente 2
            {'nodo': 'Abanico', 'tipo': 'in',  'var': 'qf', 'idx': None}, # Filtraciones del Lago
            {'nodo': 'Abanico', 'tipo': 'out', 'var': 'qg', 'idx': 2}, # Gen Abanico
            {'nodo': 'Abanico', 'tipo': 'out', 'var': 'qv', 'idx': 2}, # Vert Abanico

            # -------------------------------------------------------
            # 3. NODO: ANTUCO (Balance Restricción 8)
            # -------------------------------------------------------
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qa', 'idx': 3}, # Afluente 3
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qg', 'idx': 1}, # Viene de El Toro
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qg', 'idx': 2}, # Viene de Abanico
            {'nodo': 'Antuco', 'tipo': 'in',  'var': 'qv', 'idx': 2}, # Vertimiento Abanico
            {'nodo': 'Antuco', 'tipo': 'out', 'var': 'qg', 'idx': 3}, # Gen Antuco
            {'nodo': 'Antuco', 'tipo': 'out', 'var': 'qv', 'idx': 3}, # Vert Antuco

            # -------------------------------------------------------
            # 4. NODO: RIEZACO / ZANARTU (Balance Restricción 9)
            # -------------------------------------------------------
            {'nodo': 'RieZaco', 'tipo': 'in',  'var': 'qg', 'idx': 3}, # Viene de Antuco
            {'nodo': 'RieZaco', 'tipo': 'in',  'var': 'qv', 'idx': 3}, # Vertimiento Antuco
            {'nodo': 'RieZaco', 'tipo': 'out', 'var': 'qp_sum', 'idx': 1}, # Demanda Riego Canal 1 (Suma de demandantes)
            {'nodo': 'RieZaco', 'tipo': 'out', 'var': 'qv', 'idx': 4}, # Vertimiento/Pasada hacia CLajRucue

            # -------------------------------------------------------
            # 5. NODO: CANECOL (Balance Restricción 10)
            # -------------------------------------------------------
            {'nodo': 'Canecol', 'tipo': 'in',  'var': 'qa', 'idx': 5}, # Afluente 5
            {'nodo': 'Canecol', 'tipo': 'out', 'var': 'qg', 'idx': 5}, # Gen Canecol
            {'nodo': 'Canecol', 'tipo': 'out', 'var': 'qv', 'idx': 5}, # Vert Canecol

            # -------------------------------------------------------
            # 6. NODO: CANRUCUE (Balance Restricción 11)
            # -------------------------------------------------------
            {'nodo': 'CanRucue', 'tipo': 'in',  'var': 'qv', 'idx': 5}, # Viene de Vert Canecol
            {'nodo': 'CanRucue', 'tipo': 'out', 'var': 'qg', 'idx': 6}, # Gen CanRucue
            {'nodo': 'CanRucue', 'tipo': 'out', 'var': 'qv', 'idx': 6}, # Vert CanRucue

            # -------------------------------------------------------
            # 7. NODO: CLAJRUCUE (Balance Restricción 12)
            # -------------------------------------------------------
            {'nodo': 'CLajRucue', 'tipo': 'in',  'var': 'qv', 'idx': 4}, # Viene de Vert RieZaco
            {'nodo': 'CLajRucue', 'tipo': 'out', 'var': 'qg', 'idx': 7}, # Gen CLajRucue
            {'nodo': 'CLajRucue', 'tipo': 'out', 'var': 'qv', 'idx': 7}, # Vert CLajRucue

            # -------------------------------------------------------
            # 8. NODO: RUCUE (Balance Restricción 13)
            # -------------------------------------------------------
            {'nodo': 'Rucue', 'tipo': 'in',  'var': 'qg', 'idx': 6}, # Viene de CanRucue
            {'nodo': 'Rucue', 'tipo': 'in',  'var': 'qg', 'idx': 7}, # Viene de CLajRucue
            {'nodo': 'Rucue', 'tipo': 'out', 'var': 'qg', 'idx': 8}, # Gen Rucue
            {'nodo': 'Rucue', 'tipo': 'out', 'var': 'qv', 'idx': 8}, # Vert Rucue

            # -------------------------------------------------------
            # 9. NODO: QUILLECO (Balance Restricción 14)
            # -------------------------------------------------------
            {'nodo': 'Quilleco', 'tipo': 'in',  'var': 'qg', 'idx': 8}, # Viene de Rucue
            {'nodo': 'Quilleco', 'tipo': 'in',  'var': 'qv', 'idx': 8}, # Vertimiento Rucue
            {'nodo': 'Quilleco', 'tipo': 'out', 'var': 'qg', 'idx': 9}, # Gen Quilleco
            {'nodo': 'Quilleco', 'tipo': 'out', 'var': 'qv', 'idx': 9}, # Vert Quilleco

            # -------------------------------------------------------
            # 10. NODO: TUCAPEL (Balance Restricción 15)
            # -------------------------------------------------------
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qa', 'idx': 4}, # Afluente 4
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qg', 'idx': 5}, # Viene de Canecol (Gen)
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 6}, # Vert CanRucue
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 7}, # Vert CLajRucue
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qg', 'idx': 9}, # Gen Quilleco
            {'nodo': 'Tucapel', 'tipo': 'in',  'var': 'qv', 'idx': 9}, # Vert Quilleco
            {'nodo': 'Tucapel', 'tipo': 'out', 'var': 'qg', 'idx': 10}, # Gen Tucapel
            {'nodo': 'Tucapel', 'tipo': 'out', 'var': 'qv', 'idx': 10}, # Vert Tucapel

            # -------------------------------------------------------
            # 11. NODO: CANAL LAJA (Balance Restricción 16)
            # -------------------------------------------------------
            {'nodo': 'CanalLaja', 'tipo': 'in',  'var': 'qg', 'idx': 10}, # Viene de Tucapel
            {'nodo': 'CanalLaja', 'tipo': 'in',  'var': 'qv', 'idx': 10}, # Vertimiento Tucapel
            {'nodo': 'CanalLaja', 'tipo': 'out', 'var': 'qg', 'idx': 11}, # Gen Canal Laja
            {'nodo': 'CanalLaja', 'tipo': 'out', 'var': 'qv', 'idx': 11}, # Vert Canal Laja

            # -------------------------------------------------------
            # 12. NODO: LAJA 1 (Balance Restricción 18)
            # -------------------------------------------------------
            {'nodo': 'Laja1', 'tipo': 'in',  'var': 'qa', 'idx': 6}, # Afluente 6
            {'nodo': 'Laja1', 'tipo': 'in',  'var': 'qv', 'idx': 11}, # Vert Canal Laja (Pasa por Saltos)
            {'nodo': 'Laja1', 'tipo': 'out', 'var': 'qg', 'idx': 13}, # Gen Laja 1
            {'nodo': 'Laja1', 'tipo': 'out', 'var': 'qv', 'idx': 13}, # Vert Laja 1

            # -------------------------------------------------------
            # 13. NODO: EL DIUTO (Balance Restricción 19)
            # -------------------------------------------------------
            {'nodo': 'ElDiuto', 'tipo': 'in',  'var': 'qg', 'idx': 11}, # Viene de Canal Laja
            {'nodo': 'ElDiuto', 'tipo': 'out', 'var': 'qg', 'idx': 15}, # Gen El Diuto
            {'nodo': 'ElDiuto', 'tipo': 'out', 'var': 'qv', 'idx': 15}, # Vert El Diuto

            # -------------------------------------------------------
            # 14. NODO: RIETUCAPEL (Balance Restricción 20)
            # -------------------------------------------------------
            {'nodo': 'RieTucapel', 'tipo': 'in',  'var': 'qg', 'idx': 15}, # Gen El Diuto
            {'nodo': 'RieTucapel', 'tipo': 'in',  'var': 'qv', 'idx': 15}, # Vert El Diuto
            {'nodo': 'RieTucapel', 'tipo': 'out', 'var': 'qp_sum', 'idx': 2}, # Demanda Riego Canal 2 (Sumidero)
        ]

        # Obtener lista única de nodos de balance definidos en ARCOS_RED
        self.NODOS_BALANCE = ['ElToro', 'Abanico', 'Antuco', 'RieZaco', 'Canecol', 
                             'CanRucue', 'CLajRucue', 'Rucue', 'Quilleco', 'Tucapel',
                             'CanalLaja', 'Laja1', 'ElDiuto', 'RieTucapel']
        
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
        
        # Variables (Formulación LaTeX)
        self.V_30Nov = {}  # V_30Nov[t]: Volumen al 30 Nov previo a temp t
        self.V = {}  # V[w,t]: Volumen al final de semana w de temporada t
        
        # Variables de linealización (zonas)
        self.phi_var = {}  # phi[k,w,t]: Binaria zona k completa en semana w, temporada t
        self.delta_f = {}  # delta_f[k,w,t]: Filtración incremental en zona k
        self.delta_vr = {}  # delta_vr[k,t]: Volumen riego incremental en zona k, temporada t
        self.delta_vg = {}  # delta_vg[k,t]: Volumen generación incremental en zona k, temporada t
        
        # Volúmenes disponibles
        self.VR = {}  # VR[w,t]: Volumen disponible para riego
        self.VR_0 = {}  # VR_0[t]: Volumen inicial riego temporada t
        self.VG = {}  # VG[w,t]: Volumen disponible para generación
        self.VG_0 = {}  # VG_0[t]: Volumen inicial generación temporada t
        
        # Caudales
        self.qer = {}  # qer[w,t]: Caudal extraído para riego
        self.qeg = {}  # qeg[w,t]: Caudal extraído para generación
        self.qf = {}  # qf[w,t]: Caudal de filtración
        self.qg = {}  # qg[i,w,t]: Caudal generación
        self.qv = {}  # qv[i,w,t]: Caudal vertimiento
        self.qp = {}  # qp[d,j,w,t]: Caudal provisto riego
        
        # Déficit y superávit
        self.deficit = {}  # deficit[d,j,w,t]
        self.superavit = {}  # superavit[d,j,w,t]
        
        # Variables binarias de decisión
        self.eta = {}  # eta[d,j,w,t]: Binaria incumplimiento convenio
        self.alpha = {}  # alpha[w,t]: Binaria Abanico(1) vs Tucapel(0)
        self.beta = {}  # beta[w,t]: Binaria umbral V_min
        
        # Energía generada
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
        """Crea todas las variables de decisión según formulación LaTeX"""
        print("Creando variables de decisión (Formulación LaTeX)...")
        
        # Número de zonas de linealización
        num_zonas = len(self.K) - 1
        K_zonas = list(range(1, num_zonas + 1))  # Zonas 1 a K-1
        
        # Volúmenes del lago
        self.V_30Nov = self.model.addVars(self.T, lb=0, ub=self.V_MAX, name="V_30Nov")
        self.V = self.model.addVars(self.W, self.T, lb=0, ub=self.V_MAX, name="V")
        
        # Variables de linealización (phi y deltas)
        self.phi_var = self.model.addVars(K_zonas, self.W, self.T, vtype=GRB.BINARY, name="phi")
        self.delta_f = self.model.addVars(K_zonas, self.W, self.T, lb=0, name="delta_f")
        self.delta_vr = self.model.addVars(K_zonas, self.T, lb=0, name="delta_vr")
        self.delta_vg = self.model.addVars(K_zonas, self.T, lb=0, name="delta_vg")
        
        # Volúmenes disponibles por uso
        self.VR_0 = self.model.addVars(self.T, lb=0, name="VR_0")
        self.VR = self.model.addVars(self.W, self.T, lb=0, name="VR")
        self.VG_0 = self.model.addVars(self.T, lb=0, name="VG_0")
        self.VG = self.model.addVars(self.W, self.T, lb=0, name="VG")
        
        # Caudales
        self.qer = self.model.addVars(self.W, self.T, lb=0, name="qer")
        self.qeg = self.model.addVars(self.W, self.T, lb=0, name="qeg")
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
        """Crea todas las restricciones según formulación LaTeX"""
        print("Creando restricciones (Formulación LaTeX)...")
        
        # Número de zonas
        num_zonas = len(self.K) - 1
        K_zonas = list(range(1, num_zonas + 1))
        K_list = sorted(self.K)
        
        # ========== 1. DEFINICIÓN DE FILTRACIONES ==========
        print("  1. Definición de filtraciones...")
        for t in self.T:
            for w in self.W:
                # qf[w,t] = f_1 + Σ delta_f[k,w,t]
                self.model.addConstr(
                    self.qf[w, t] == self.FC[K_list[0]] + gp.quicksum(
                        self.delta_f[k, w, t] for k in K_zonas
                    ),
                    name=f"def_filtracion_{w}_{t}")
                
                for k in K_zonas:
                    k_idx = k - 1  # Índice en K_list
                    f_k = self.FC[K_list[k_idx]]
                    f_k_next = self.FC[K_list[k_idx + 1]]
                    
                    # delta_f[k,w,t] ≤ f_{k+1} - f_k
                    self.model.addConstr(
                        self.delta_f[k, w, t] <= f_k_next - f_k,
                        name=f"delta_f_upper_{k}_{w}_{t}")
                    
                    # delta_f[k,w,t] ≥ phi[k,w,t] * (f_{k+1} - f_k)
                    self.model.addConstr(
                        self.delta_f[k, w, t] >= self.phi_var[k, w, t] * (f_k_next - f_k),
                        name=f"delta_f_lower_{k}_{w}_{t}")
                    
                    # delta_f[k,w,t] ≤ phi[k-1,w,t] * (f_{k+1} - f_k)  (si k > 1)
                    if k > 1:
                        self.model.addConstr(
                            self.delta_f[k, w, t] <= self.phi_var[k-1, w, t] * (f_k_next - f_k),
                            name=f"delta_f_prev_{k}_{w}_{t}")
                    else:
                        # Para k=1, phi[0] = 1 (siempre activo)
                        self.model.addConstr(
                            self.delta_f[k, w, t] <= f_k_next - f_k,
                            name=f"delta_f_prev_{k}_{w}_{t}")
                
                # V[w,t] = v_1 + Σ (v_{k+1} - v_k)/(f_{k+1} - f_k) * delta_f[k,w,t]
                v_expr = self.VC[K_list[0]]
                for k in K_zonas:
                    k_idx = k - 1
                    v_k = self.VC[K_list[k_idx]]
                    v_k_next = self.VC[K_list[k_idx + 1]]
                    f_k = self.FC[K_list[k_idx]]
                    f_k_next = self.FC[K_list[k_idx + 1]]
                    
                    if abs(f_k_next - f_k) > 1e-6:
                        coef = (v_k_next - v_k) / (f_k_next - f_k)
                        v_expr += coef * self.delta_f[k, w, t]
                
                self.model.addConstr(
                    self.V[w, t] == v_expr,
                    name=f"vol_from_filtracion_{w}_{t}")
        
        # ========== 2. DEFINICIÓN DE VOLÚMENES DE RIEGO (30 NOV) ==========
        print("  2. Volúmenes disponibles de riego...")
        for t in self.T:
            # VR_0[t] = vr_1 + Σ delta_vr[k,t]
            self.model.addConstr(
                self.VR_0[t] == self.VUC[(1, K_list[0])] + gp.quicksum(
                    self.delta_vr[k, t] for k in K_zonas
                ),
                name=f"def_VR0_{t}")
            
            for k in K_zonas:
                k_idx = k - 1
                vr_k = self.VUC[(1, K_list[k_idx])]
                vr_k_next = self.VUC[(1, K_list[k_idx + 1])]
                
                # delta_vr[k,t] ≤ vr_{k+1} - vr_k
                self.model.addConstr(
                    self.delta_vr[k, t] <= vr_k_next - vr_k,
                    name=f"delta_vr_upper_{k}_{t}")
                
                # delta_vr[k,t] ≥ phi[k,32,t] * (vr_{k+1} - vr_k)
                self.model.addConstr(
                    self.delta_vr[k, t] >= self.phi_var[k, 32, t] * (vr_k_next - vr_k),
                    name=f"delta_vr_lower_{k}_{t}")
                
                # delta_vr[k,t] ≤ phi[k-1,32,t] * (vr_{k+1} - vr_k)
                if k > 1:
                    self.model.addConstr(
                        self.delta_vr[k, t] <= self.phi_var[k-1, 32, t] * (vr_k_next - vr_k),
                        name=f"delta_vr_prev_{k}_{t}")
                else:
                    self.model.addConstr(
                        self.delta_vr[k, t] <= vr_k_next - vr_k,
                        name=f"delta_vr_prev_{k}_{t}")
            
            # V[32,t] = v_1 + Σ (v_{k+1} - v_k)/(vr_{k+1} - vr_k) * delta_vr[k,t]
            # (Esta restricción vincula V[32,t] con VR_0[t])
            v_expr = self.VC[K_list[0]]
            for k in K_zonas:
                k_idx = k - 1
                v_k = self.VC[K_list[k_idx]]
                v_k_next = self.VC[K_list[k_idx + 1]]
                vr_k = self.VUC[(1, K_list[k_idx])]
                vr_k_next = self.VUC[(1, K_list[k_idx + 1])]
                
                if abs(vr_k_next - vr_k) > 1e-6:
                    coef = (v_k_next - v_k) / (vr_k_next - vr_k)
                    v_expr += coef * self.delta_vr[k, t]
            
            self.model.addConstr(
                self.V[32, t] == v_expr,
                name=f"vol32_from_VR_{t}")
        
        # ========== 3. DEFINICIÓN DE VOLÚMENES DE GENERACIÓN (30 NOV) ==========
        print("  3. Volúmenes disponibles de generación...")
        for t in self.T:
            # VG_0[t] = vg_1 + Σ delta_vg[k,t]
            self.model.addConstr(
                self.VG_0[t] == self.VUC[(2, K_list[0])] + gp.quicksum(
                    self.delta_vg[k, t] for k in K_zonas
                ),
                name=f"def_VG0_{t}")
            
            for k in K_zonas:
                k_idx = k - 1
                vg_k = self.VUC[(2, K_list[k_idx])]
                vg_k_next = self.VUC[(2, K_list[k_idx + 1])]
                
                # delta_vg[k,t] ≤ vg_{k+1} - vg_k
                self.model.addConstr(
                    self.delta_vg[k, t] <= vg_k_next - vg_k,
                    name=f"delta_vg_upper_{k}_{t}")
                
                # delta_vg[k,t] ≥ phi[k,32,t] * (vg_{k+1} - vg_k)
                self.model.addConstr(
                    self.delta_vg[k, t] >= self.phi_var[k, 32, t] * (vg_k_next - vg_k),
                    name=f"delta_vg_lower_{k}_{t}")
                
                # delta_vg[k,t] ≤ phi[k-1,32,t] * (vg_{k+1} - vg_k)
                if k > 1:
                    self.model.addConstr(
                        self.delta_vg[k, t] <= self.phi_var[k-1, 32, t] * (vg_k_next - vg_k),
                        name=f"delta_vg_prev_{k}_{t}")
                else:
                    self.model.addConstr(
                        self.delta_vg[k, t] <= vg_k_next - vg_k,
                        name=f"delta_vg_prev_{k}_{t}")
        
        # ========== 4. GENERACIÓN EN EL TORO ==========
        print("  4. Generación en El Toro...")
        for t in self.T:
            for w in self.W:
                # qg[1,w,t] = qer[w,t] + qeg[w,t]
                self.model.addConstr(
                    self.qg[1, w, t] == self.qer[w, t] + self.qeg[w, t],
                    name=f"gen_eltoro_{w}_{t}")
        
        # ========== 5. BALANCE DE VOLUMEN EN EL LAGO ==========
        print("  5. Balance de volumen del lago...")
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
        # Nota: qg[16] representa las filtraciones que se usarán en el balance de Abanico
        print("  5. Filtraciones del lago...")
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qg[16, w, t] == self.qf[w, t],
                    name=f"laja_filt_{w}_{t}")
        
        # ========== 6. RESTRICCIÓN GENÉRICA DE BALANCE DE FLUJO EN REDES ==========
        print("  6. Balance de flujo en red...")
        for n in self.NODOS_BALANCE:
            for t in self.T:
                for w in self.W:
                    flujo_entrante = 0
                    flujo_saliente = 0
                    
                    # Filtrar arcos para este nodo
                    arcos_nodo = [a for a in self.ARCOS_RED if a['nodo'] == n]
                    
                    for arco in arcos_nodo:
                        # Seleccionar la variable correcta según el tipo
                        if arco['var'] == 'qa':
                            valor = self.QA[arco['idx'], w, t]
                        elif arco['var'] == 'qg':
                            valor = self.qg[arco['idx'], w, t]
                        elif arco['var'] == 'qv':
                            valor = self.qv[arco['idx'], w, t]
                        elif arco['var'] == 'qe':  # Extracciones del lago
                            valor = self.qe[arco['idx'], w, t]
                        elif arco['var'] == 'qf':  # Filtraciones
                            valor = self.qf[w, t]
                        elif arco['var'] == 'qp_sum':
                            # Suma de todos los demandantes 'd' para el canal 'j' (idx)
                            valor = gp.quicksum(self.qp[d, arco['idx'], w, t] for d in self.D)
                        
                        # Sumar al lado correcto de la ecuación
                        if arco['tipo'] == 'in':
                            flujo_entrante += valor
                        else:
                            flujo_saliente += valor
                    
                    # Agregar la restricción: Entradas == Salidas
                    self.model.addConstr(flujo_entrante == flujo_saliente, name=f"Balance_{n}_{w}_{t}")
        
        # ========== 7. RESTRICCIÓN ESPECIAL: RIESALTOS ==========
        # RieSaltos tiene una restricción especial: solo el demandante 3 (Saltos del Laja)
        # puede retirar agua del canal 3, y es igual al vertimiento de Canal Laja (qv[11])
        print("  7. Restricción especial RieSaltos...")
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qp[3, 3, w, t] == self.qv[11, w, t],
                    name=f"riesaltos_especial_{w}_{t}")
        
        # ========== 8. BALANCE DE DEMANDAS DE RIEGO ==========
        print("  8. Balance de demandas de riego...")
        for t in self.T:
            for w in self.W:
                for j in self.J:
                    for d in self.D:
                        self.model.addConstr(
                            self.QD.get((d, j, w), 0) - self.qp[d, j, w, t] == self.deficit[d, j, w, t] - self.superavit[d, j, w, t],
                            name=f"balance_demanda_{d}_{j}_{w}_{t}")
        
        # ========== 9. ACTIVACIÓN DE PENALIZACIONES POR CONVENIO (Big-M) ==========
        print("  9. Activación de penalizaciones por convenio...")
        for t in self.T:
            for w in self.W:
                # RIEZACO (Canal j=1)
                # Primeros regantes: déficit solo si incumplimiento o alpha=1 (Abanico tiene prioridad)
                self.model.addConstr(
                    self.deficit[1, 1, w, t] <= self.M_bigM * (self.eta[1, 1, w, t] + self.alpha[w, t]),
                    name=f"bigM_riezaco_1_{w}_{t}")
                
                # Segundos y Saltos en RieZaco
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 1, w, t] <= self.M_bigM * self.eta[d, 1, w, t],
                        name=f"bigM_riezaco_{d}_{w}_{t}")
                
                # RIETUCAPEL (Canal j=2)
                # Primeros regantes: déficit solo si incumplimiento o alpha=1 (Abanico)
                self.model.addConstr(
                    self.deficit[1, 2, w, t] <= self.M_bigM * (self.eta[1, 2, w, t] + self.alpha[w, t]),
                    name=f"bigM_rietucapel_1_{w}_{t}")
                
                # Segundos y Saltos en RieTucapel
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 2, w, t] <= self.M_bigM * self.eta[d, 2, w, t],
                        name=f"bigM_rietucapel_{d}_{w}_{t}")
                
                # RIESALTOS (Canal j=3)
                for d in self.D:
                    self.model.addConstr(
                        self.deficit[d, 3, w, t] <= self.M_bigM * self.eta[d, 3, w, t],
                        name=f"bigM_riesaltos_{d}_{w}_{t}")
                
                # ABANICO (Canal j=4)
                # Primeros regantes: déficit solo si incumplimiento o NO alpha (Tucapel tiene prioridad)
                self.model.addConstr(
                    self.deficit[1, 4, w, t] <= self.M_bigM * (1 + self.eta[1, 4, w, t] - self.alpha[w, t]),
                    name=f"bigM_abanico_1_{w}_{t}")
                
                # Segundos y Saltos en Abanico
                for d in [2, 3]:
                    self.model.addConstr(
                        self.deficit[d, 4, w, t] <= self.M_bigM * self.eta[d, 4, w, t],
                        name=f"bigM_abanico_{d}_{w}_{t}")
        
        # ========== 10. VERTIMIENTO EL TORO = 0 ==========
        print("  10. Vertimiento El Toro...")
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.qv[1, w, t] == 0,
                    name=f"no_vert_eltoro_{w}_{t}")
        
        # ========== 11. CAPACIDADES ==========
        print("  11. Capacidades de generación...")
        for t in self.T:
            for i in self.I:
                for w in self.W:
                    self.model.addConstr(
                        self.qg[i, w, t] <= self.gamma[i],
                        name=f"cap_max_{i}_{w}_{t}")
        
        # ========== 12. VOLUMEN MÍNIMO DEL LAGO ==========
        print("  12. Volumen mínimo del lago...")
        for t in self.T:
            for w in self.W:
                self.model.addConstr(
                    self.V[w, t] >= self.V_min - self.M_bigM * self.beta[w, t],
                    name=f"vol_min_{w}_{t}")
        
        # ========== 13. DEFINICIÓN DE ENERGÍA GENERADA POR CENTRAL ==========
        print("  13. Definición de energía generada...")
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
