"""
This mixin is made to calculate the production rate and energy consumption of a water injection dredger (WID) based on its physical characteristics
"""
import numpy as np
from .simpy_object import SimpyObject
import openclsim.core as core
from .log import Log, LogState, PerformsActivity

class HasDraghead(SimpyObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HasVisor(SimpyObject):
    def __init__(self, width_single_visor, visor_angle, visor_length, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width_single_visor = width_single_visor
        self.visor_angle = visor_angle
        self.visor_length = visor_length

class HasJetTSHD(SimpyObject):
    def __init__(self, jet_discharge_workingpoint, jet_contraction_coefficient, jet_pipe_diameter, nozzle_diameter, n_nozzles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jet_discharge_workingpoint = jet_discharge_workingpoint
        self.jet_contraction_coefficient = jet_contraction_coefficient
        self.nozzle_diameter = nozzle_diameter
        self.n_nozzles = n_nozzles
        self.jet_pipe_diameter = jet_pipe_diameter

class HasDredgePump(SimpyObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class HasPropellerTSHD(SimpyObject):
    def __init__(self, efficiency_transmission, efficiency_hydrodynamic_loading, coefficient_block, coefficient_stern, efficiency_gearing,
                 vessel_width, vessel_length_waterline, n_propellers, vessel_draught, bulbous_bow, distance_waterplanne, *args, **kwargs):
        self.efficiency_transmission = efficiency_transmission
        self.efficiency_hydrodynamic_loading = efficiency_hydrodynamic_loading
        self.efficiency_gearing = efficiency_gearing
        self.coefficient_stern = coefficient_stern
        self.coefficient_block = coefficient_block
        self.vessel_width = vessel_width
        self.vessel_length_waterline = vessel_length_waterline
        self.vessel_draught = vessel_draught
        self.bulbous_bow = bulbous_bow
        self.distance_waterplanne = distance_waterplanne
        self.n_propellers = n_propellers


        super().__init__(*args, **kwargs)

class HasSoilTSHD(SimpyObject):
    def __init__(self, rho_particle, rho_water, compaction_force,
                 initial_permeabilty, permeability_cutting_teeth, dilatancy,
                 viscosity_water, water_depth, gravitatinal_acceleration
                 , mass_flux_coefficient, initial_porosity, porosity_cutting_teeth,
                 *args, **kwargs):
        self.compaction_force = compaction_force
        self.initial_permeabilty = initial_permeabilty
        self.permeability_cutting_teeth = permeability_cutting_teeth
        self.dilatancy = dilatancy
        self.viscosity_water = viscosity_water
        self.water_depth = water_depth
        self.rho_particle = rho_particle
        self.gravitatinal_acceleration = gravitatinal_acceleration
        self.rho_water = rho_water
        self.mass_flux_coefficient = mass_flux_coefficient
        self.initial_porosity = initial_porosity
        self.porosity_cutting_teeth = porosity_cutting_teeth
        super().__init__(*args, **kwargs)
    
class HasTSHDProduction(HasVisor, HasJetTSHD, HasSoilTSHD, Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def situ_production(self, env, velocity_trailing):
        
        self.velocity_trailing = velocity_trailing
        
        # layer thickness
        gamma_rad = self.visor_angle/180 * np.pi
        total_layer_thickness = self.visor_length * np.sin(gamma_rad)

        'penetration depth on Van Rhee method for single jet'
        jet_penetration_workingpoint = np.sqrt((self.mass_flux_coefficient * self.rho_water * self.jet_contraction_coefficient * nozzle_area *
                                                 jet_velocity_workingpoint * (2 * nozzle_pressure_loss/self.rho_water)**0.5) /
                                                 (self.rho_particle * (1 - self.initial_porosity) * velocity_trailing**2))

        if jet_penetration_workingpoint > total_layer_thickness:
            cut_layer_thickness = 0.001
            sledge_layer_thickness = 0.001
            jet_layer_thickness = total_layer_thickness
            
        elif jet_penetration_workingpoint > (total_layer_thickness - sledge_layer_thickness):
            cut_layer_thickness = 0.001
            sledge_layer_thickness = total_layer_thickness - jet_layer_thickness

        # mass flux
        water_content_workingpoint = jet_layer_thickness
        water_content_max = 2 * self.width_single_visor / self.n_nozzles
        if jet_layer_thickness > water_content_max:
            water_content_workingpoint = water_content_max
        mass_flux_workingpoint = jet_velocity_workingpoint * self.rho_particle * (1 - self.initial_porosity) * self.n_nozzles * water_content_workingpoint

        # jet production
        nozzle_area = 0.25 * np.pi * self.nozzle_diameter **2
        jet_area = 0.25 * np.pi * self.jet_pipe_diameter ** 2
        jet_velocity_workingpoint = self.jet_discharge_workingpoint / jet_area
        nozzle_pressure_loss = 0.5 * self.rho_water * ((4 * self.jet_discharge_workingpoint) /
                                                       (self.jet_contraction_coefficient * np.pi * self.nozzle_diameter**2 * self.n_nozzles))**2
        
        sand_production_vr = mass_flux_workingpoint / self.rho_particle
        water_production_vr = sand_production_vr / (1 - self.initial_porosity) * self.initial_porosity
        jet_production = sand_production_vr + water_production_vr + self.jet_discharge_workingpoint

        # cut production
        width_visor = 2 * self.width_single_visor
        cut_production = width_visor * cut_layer_thickness * self.velocity_trailing

        #situ production
        situ_production = jet_production + cut_production

        self.log_entry_v1(
            env.now,
            core.LogState.UNKNOWN,
            {"situ_production": situ_production}
            )
        
        return {
            "situ_production": situ_production
        }

class HasTSHDEnergy(HasPropellerTSHD, HasSoilTSHD, Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def propulsion_power (self, env, velocity_trailing):

        self.velocity_trailing = velocity_trailing
        
        """1) Frictional resistance
            - 1st resistance component defined by Holtrop and Mennen (1982)
            - A modification to the original friction line is applied, based on literature of Zeng (2018), to account for shallow water effects """
        coefficient_midship = 1.006 - 0.0056 * self.coefficient_block ** (-3.56)
        coefficient_waterplane = (1 + 2 * self.coefficient_block) / 3
        coefficient_prismatic = self.coefficient_block / coefficient_midship
        coefficient_bulbousbow = 0.2

        water_displacement = self.coefficient_block * self.vessel_length_waterline * self.vessel_width * self.vessel_draught
        longitudinal_center_buoyancy = -13.5 + 19.4 * coefficient_prismatic
        length_run = self.vessel_length_waterline * (1 - coefficient_prismatic + (0.06 * coefficient_prismatic * longitudinal_center_buoyancy) /
                                                     (4 * coefficient_prismatic - 1))
        area_transverse_transom = 0.2 * self.vessel_width * self.vessel_draught
        wet_area_total = self.vessel_length_waterline * (2 * self.vessel_draught + self.vessel_width) * np.sqrt(coefficient_midship) * (0.453 + 0.4425 * self.coefficient_block - 0.2862 * coefficient_midship - 0.003467 *
                                    (self.vessel_width / self.vessel_draught) + 0.3696 * coefficient_waterplane) + 2.38 * (area_transverse_bulb / self.coefficient_block)
        area_flatbottom = self.vessel_length_waterline * self.vessel_width

        if self.bulbous_bow == "yes":
            area_transverse_bulb = coefficient_bulbousbow * self.vessel_width * self.vessel_draught * coefficient_midship 
        else:
            area_transverse_bulb = 0
        
        reynolds_number = velocity_trailing * self.vessel_length_waterline / self.viscosity_water  
        katsui_number = 0.042612 * np.log10(reynolds_number) + 0.56725

        coefficient_fricitional = 0.075 / ((np.log10(reynolds_number) - 2) ** 2)
        coefficient_fricitional_deep = 0.08169 / ((np.log10(reynolds_number) - 1.717) ** 2)
        coefficient_fricitional_katsui = 0.0066577 / ((np.log10(reynolds_number) - 4.3762) ** katsui_number)
        coefficient_fricitional_proposed = (0.08169 / ((np.log10(reynolds_number) - 1.717) ** 2)) * (1 + 
            (0.003998 / (np.log10(reynolds_number) - 4.393)) * 
            ((self.distance_waterplanne - self.vessel_draught) / self.vessel_length_waterline) ** (-1.083))

        if self.distance_waterplanne / self.vessel_draught <= 4:
            velocity_trailing_shallow = 0.4277 * velocity_trailing * np.exp((self.distance_waterplanne / self.vessel_draught) ** (-0.07625))
        else:
            velocity_trailing_shallow = velocity_trailing

        if (self.distance_waterplanne - self.vessel_draught) / self.vessel_length_waterline > 1:
            coefficient_fricition = coefficient_fricitional + (coefficient_fricitional_deep - coefficient_fricitional_katsui) * (area_flatbottom / wet_area_total)
        else:
            coefficient_fricition = coefficient_fricitional + (coefficient_fricitional_proposed - coefficient_fricitional_katsui) * (area_flatbottom / wet_area_total) * (velocity_trailing_shallow / velocity_trailing) ** 2

        resistance_frictional = (coefficient_fricition * 0.5 * self.rho_water * (velocity_trailing ** 2) * wet_area_total) / 1000
        

        """2) Viscous resistance
        `- 2nd resistance component defined by Holtrop and Mennen (1982)
        - Form factor (1 + k1) has to be multiplied by the frictional resistance R_f, to account for the effect of viscosity"""
        coefficient_afterbody = 1 + 0.0011 * self.coefficient_stern
        # the form factor (1+k1) describes the viscous resistance
        resistance_viscous = 0.93 + 0.487 * coefficient_afterbody * ((self.vessel_width / self.vessel_length_waterline) ** 1.068) * (
            (self.vessel_draught / self.vessel_length_waterline) ** 0.461) * (
            (self.vessel_length_waterline / length_run) ** 0.122) * (
            ((self.vessel_length_waterline ** 3) / water_displacement) ** 0.365) * (
            (1 - coefficient_prismatic) ** (-0.604))


        """3) Appendage resistance
        - 3rd resistance component defined by Holtrop and Mennen (1982)
        - Appendages (like a rudder, shafts, skeg) result in additional frictional resistance"""
        appendage_wet_area = 0.1 * wet_area_total
        resistance_appendage = (0.5 * self.rho_water * (velocity_trailing ** 2) * appendage_wet_area * resistance_viscous * coefficient_fricition) / 1000


        resistance_fricition = resistance_frictional * resistance_viscous + resistance_appendage
        
        """Wave resistance
        - 4th resistance component defined by Holtrop and Mennen (1982)
        - When the speed or the vessel size increases, the wave making resistance increases
        - In shallow water, the wave resistance shows an asymptotical behaviour by reaching the critical speed
        """
        assert g >= 0, f'g should be positive: {g}'
        assert L_wl >= 0, f'L should be positive: {L_wl}'
        F_rL = V_2 / np.sqrt(g * L_wl)  # Froude number based on ship's speed to water and its length of waterline

        # parameter c_7 is determined by the B/L ratio
        if B / L_wl < 0.11:
            c_7 = 0.229577 * (B / L_wl) ** 0.33333
        if B / L_wl > 0.25:
            c_7 = 0.5 - 0.0625 * (L_wl / B)
        else:
            c_7 = B / L_wl

        # half angle of entrance in degrees
        i_E = 1 + 89 * np.exp(-((L_wl / B) ** 0.80856) * ((1 - C_wp) ** 0.30484) * (
                    (1 - C_p - 0.0225 * lcb) ** 0.6367) * ((L_R / B) ** 0.34574) * (
                                            (100 * delta / (L_wl ** 3)) ** 0.16302))

        c_1 = 2223105 * (c_7 ** 3.78613) * ((T / B) ** 1.07961) * (90 - i_E) ** (-1.37165)
        c_3 = (0.56 * A_BT**1.5)/(B * T *(0.31 * np.sqrt(A_BT)+T_F - h_B))
        if BB == 'yes':
            c_2 = np.exp(-1.89 * np.sqrt(c_3))
        else:
            c_2 = 1      # accounts for the effect of the bulbous bow, which is not present at inland ships
        c_5 = 1 - (0.8 * A_T) / (
                    B * T * C_M)  # influence of the transom stern on the wave resistance

        # parameter c_15 depends on the ratio L^3 / delta
        if (L_wl ** 3) / delta < 512:
            c_15 = -1.69385
        if (L_wl ** 3) / delta > 1727:
            c_15 = 0
        else:
            c_15 = -1.69385 + (L_wl / (delta ** (1 / 3)) - 8) / 2.36

        # parameter c_16 depends on C_P
        if C_p < 0.8:
            c_16 = 8.07981 * C_p - 13.8673 * (C_p ** 2) + 6.984388 * (C_p ** 3)
        else:
            c_16 = 1.73014 - 0.7067 * C_p

        if L_wl / B < 12:
            lmbda = 1.446 * C_p - 0.03 * (L_wl / B)
        else:
            lmbda = 1.446 * C_p - 0.36

        m_1 = 0.0140407 * (L_wl / T) - 1.75254 * ((delta) ** (1 / 3) / L_wl) - 4.79323 * (
                    B / L_wl) - c_16
        m_2 = c_15 * (C_p**2) *np.exp((-0.1)* (F_rL**(-2))) 
        
        correction = np.exp(m_1 * (F_rL**(-0.9)) + m_2 * np.cos(lmbda * (F_rL ** (-2))))
        
        R_W =  c_1 * c_2 * c_5 * delta * rho * g * correction / 1000 # kN


        resistance_wave = 1









        resistance_pressure = 1
        resistance_residual = 1

        resistance_total = resistance_fricition + resistance_wave + resistance_pressure + resistance_residual 

        D_s = 0.7 * self.vessel_draught
        w = 0.11 * (0.16 / self.n_propellers) * self.coefficient_block * np.sqrt((water_displacement**(1/3)) / D_s)

        if self.n_propellers == 1:
            t = 0.6 * w * (1 + 0.67 * w)
        else:
            t = 0.8 * w * (1 + 0.25 * w)
        
        
        efficiency_total = self.efficiency_transmission * self.efficiency_hydrodynamic_loading * self.efficiency_gearing
        
        propulsion_power_loading = resistance_total * velocity_trailing * (1 - efficiency_total)
        
        



        self.log_entry_v1(
            env.now,
            core.LogState.UNKNOWN,
            {"propulsion_power_loading": propulsion_power_loading}
            )
        
        return {
            "propulsion_power_loading": propulsion_power_loading
        }
        



class IsTSHD(HasTSHDEnergy, HasTSHDProduction, HasDraghead, HasDredgePump, HasVisor, HasJetTSHD, HasPropellerTSHD, Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)