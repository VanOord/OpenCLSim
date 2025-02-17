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
    def __init__(self, efficiency_transmission, efficiency_hydrodynamic_loading, coefficient_block,
                 coefficient_stern, efficiency_gearing, efficency_openwater,
                 efficiency_relative_rotative, vessel_width, vessel_length_waterline,
                 n_propellers, vessel_draught, vessel_draught_forward, bulbous_bow, distance_waterplanne, *args, **kwargs):
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
        self.vessel_draught_forward = vessel_draught_forward
        self.efficency_openwater = efficency_openwater
        self.efficiency_relative_rotative = efficiency_relative_rotative


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
    
    def propulsion_power (self, env, velocity_vessel):

        self.velocity_trailing = velocity_vessel
        
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
        
        reynolds_number = velocity_vessel * self.vessel_length_waterline / self.viscosity_water  
        katsui_number = 0.042612 * np.log10(reynolds_number) + 0.56725

        coefficient_fricitional = 0.075 / ((np.log10(reynolds_number) - 2) ** 2)
        coefficient_fricitional_deep = 0.08169 / ((np.log10(reynolds_number) - 1.717) ** 2)
        coefficient_fricitional_katsui = 0.0066577 / ((np.log10(reynolds_number) - 4.3762) ** katsui_number)
        coefficient_fricitional_proposed = (0.08169 / ((np.log10(reynolds_number) - 1.717) ** 2)) * (1 + 
            (0.003998 / (np.log10(reynolds_number) - 4.393)) * 
            ((self.distance_waterplanne - self.vessel_draught) / self.vessel_length_waterline) ** (-1.083))

        if self.distance_waterplanne / self.vessel_draught <= 4:
            velocity_trailing_shallow = 0.4277 * velocity_vessel * np.exp((self.distance_waterplanne / self.vessel_draught) ** (-0.07625))
        else:
            velocity_trailing_shallow = velocity_vessel

        if (self.distance_waterplanne - self.vessel_draught) / self.vessel_length_waterline > 1:
            coefficient_fricition = coefficient_fricitional + (coefficient_fricitional_deep - coefficient_fricitional_katsui) * (area_flatbottom / wet_area_total)
        else:
            coefficient_fricition = coefficient_fricitional + (coefficient_fricitional_proposed - coefficient_fricitional_katsui) * (area_flatbottom / wet_area_total) * (velocity_trailing_shallow / velocity_vessel) ** 2

        resistance_frictional = (coefficient_fricition * 0.5 * self.rho_water * (velocity_vessel ** 2) * wet_area_total) / 1000
        

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
        resistance_appendage = (0.5 * self.rho_water * (velocity_vessel ** 2) * appendage_wet_area * resistance_viscous * coefficient_fricition) / 1000


        # total resistance due to friction
        resistance_fricition = resistance_frictional * resistance_viscous + resistance_appendage
        
        """Intermediate calculation: Karpov
        - The Karpov method computes a velocity correction that accounts for limited water depth (corrected velocity V2)
        - V2 has to be implemented in the wave resistance and the residual resistance terms"""

        # The Froude number used in the Karpov method is the depth related froude number F_nh

        # The different alpha** curves are determined with a sixth power polynomial approximation in Excel
        # A distinction is made between different ranges of Froude numbers, because this resulted in a better approximation of the curve
        froude_number = velocity_vessel / np.sqrt(self.gravitatinal_acceleration * area_flatbottom)
        if froude_number <= 0.4:

            if 0 <= area_flatbottom / self.vessel_draught < 1.75:
                alpha_xx = (-4 * 10 ** (
                    -12)) * froude_number ** 3 - 0.2143 * froude_number ** 2 - 0.0643 * froude_number + 0.9997
            if 1.75 <= area_flatbottom / self.vessel_draught < 2.25:
                alpha_xx = -0.8333 * froude_number ** 3 + 0.25 * froude_number ** 2 - 0.0167 * froude_number + 1
            if 2.25 <= area_flatbottom / self.vessel_draught < 2.75:
                alpha_xx = -1.25 * froude_number ** 4 + 0.5833 * froude_number ** 3 - 0.0375 * froude_number ** 2 - 0.0108 * froude_number + 1
            if area_flatbottom / self.vessel_draught >= 2.75:
                alpha_xx = 1

        if froude_number > 0.4:
            if 0 <= area_flatbottom / self.vessel_draught < 1.75:
                alpha_xx = -0.9274 * froude_number ** 6 + 9.5953 * froude_number ** 5 - 37.197 * froude_number ** 4 + 69.666 * froude_number ** 3 - 65.391 * froude_number ** 2 + 28.025 * froude_number - 3.4143
            if 1.75 <= area_flatbottom / self.vessel_draught < 2.25:
                alpha_xx = 2.2152 * froude_number ** 6 - 11.852 * froude_number ** 5 + 21.499 * froude_number ** 4 - 12.174 * froude_number ** 3 - 4.7873 * froude_number ** 2 + 5.8662 * froude_number - 0.2652
            if 2.25 <= area_flatbottom / self.vessel_draught < 2.75:
                alpha_xx = 1.2205 * froude_number ** 6 - 5.4999 * froude_number ** 5 + 5.7966 * froude_number ** 4 + 6.6491 * froude_number ** 3 - 16.123 * froude_number ** 2 + 9.2016 * froude_number - 0.6342
            if 2.75 <= area_flatbottom / self.vessel_draught < 3.25:
                alpha_xx = -0.4085 * froude_number ** 6 + 4.534 * froude_number ** 5 - 18.443 * froude_number ** 4 + 35.744 * froude_number ** 3 - 34.381 * froude_number ** 2 + 15.042 * froude_number - 1.3807
            if 3.25 <= area_flatbottom / self.vessel_draught < 3.75:
                alpha_xx = 0.4078 * froude_number ** 6 - 0.919 * froude_number ** 5 - 3.8292 * froude_number ** 4 + 15.738 * froude_number ** 3 - 19.766 * froude_number ** 2 + 9.7466 * froude_number - 0.6409
            if 3.75 <= area_flatbottom / self.vessel_draught < 4.5:
                alpha_xx = 0.3067 * froude_number ** 6 - 0.3404 * froude_number ** 5 - 5.0511 * froude_number ** 4 + 16.892 * froude_number ** 3 - 20.265 * froude_number ** 2 + 9.9002 * froude_number - 0.6712
            if 4.5 <= area_flatbottom / self.vessel_draught < 5.5:
                alpha_xx = 0.3212 * froude_number ** 6 - 0.3559 * froude_number ** 5 - 5.1056 * froude_number ** 4 + 16.926 * froude_number ** 3 - 20.253 * froude_number ** 2 + 10.013 * froude_number - 0.7196
            if 5.5 <= area_flatbottom / self.vessel_draught < 6.5:
                alpha_xx = 0.9252 * froude_number ** 6 - 4.2574 * froude_number ** 5 + 5.0363 * froude_number ** 4 + 3.3282 * froude_number ** 3 - 10.367 * froude_number ** 2 + 6.3993 * froude_number - 0.2074
            if 6.5 <= area_flatbottom / self.vessel_draught < 7.5:
                alpha_xx = 0.8442 * froude_number ** 6 - 4.0261 * froude_number ** 5 + 5.313 * froude_number ** 4 + 1.6442 * froude_number ** 3 - 8.1848 * froude_number ** 2 + 5.3209 * froude_number - 0.0267
            if 7.5 <= area_flatbottom / self.vessel_draught < 8.5:
                alpha_xx = 0.1211 * froude_number ** 6 + 0.628 * froude_number ** 5 - 6.5106 * froude_number ** 4 + 16.7 * froude_number ** 3 - 18.267 * froude_number ** 2 + 8.7077 * froude_number - 0.4745

            if 8.5 <= area_flatbottom / self.vessel_draught < 9.5:
                if froude_number < 0.6:
                    alpha_xx = 1
                if froude_number >= 0.6:
                    alpha_xx = -6.4069 * froude_number ** 6 + 47.308 * froude_number ** 5 - 141.93 * froude_number ** 4 + 220.23 * froude_number ** 3 - 185.05 * froude_number ** 2 + 79.25 * froude_number - 12.484
            if area_flatbottom / self.vessel_draught >= 9.5:
                if froude_number < 0.6:
                    alpha_xx = 1
                if froude_number >= 0.6:
                    alpha_xx = -6.0727 * froude_number ** 6 + 44.97 * froude_number ** 5 - 135.21 * froude_number ** 4 + 210.13 * froude_number ** 3 - 176.72 * froude_number ** 2 + 75.728 * froude_number - 11.893  
        
            velocity_vessel_modified = velocity_vessel / alpha_xx # V_0 is in m/s


        """Wave resistance
        - 4th resistance component defined by Holtrop and Mennen (1982)
        - When the speed or the vessel size increases, the wave making resistance increases
        - In shallow water, the wave resistance shows an asymptotical behaviour by reaching the critical speed
        """
        center_transverse_area = 0.2 * self.vessel_draught_forward

        assert self.gravitatinal_acceleration >= 0, f'g should be positive: {self.gravitatinal_acceleration}'
        assert self.vessel_length_waterline >= 0, f'L should be positive: {self.vessel_length_waterline}'
        froude_number_waterline = velocity_vessel_modified / np.sqrt(self.gravitatinal_acceleration * self.vessel_length_waterline)  # Froude number based on ship's speed to water and its length of waterline

        # parameter c_7 is determined by the B/L ratio
        if self.vessel_width / self.vessel_length_waterline < 0.11:
            c_7 = 0.229577 * (self.vessel_width / self.vessel_length_waterline) ** 0.33333
        if self.vessel_width / self.vessel_length_waterline > 0.25:
            c_7 = 0.5 - 0.0625 * (self.vessel_length_waterline / self.vessel_width)
        else:
            c_7 = self.vessel_width / self.vessel_length_waterline

        # half angle of entrance in degrees
        angle_waterline_bulbousbow = 1 + 89 * np.exp(-((self.vessel_length_waterline / self.vessel_width) ** 0.80856) * ((1 - coefficient_waterplane) ** 0.30484) * (
                    (1 - coefficient_prismatic - 0.0225 * longitudinal_center_buoyancy) ** 0.6367) * ((length_run / self.vessel_width) ** 0.34574) * (
                                            (100 * water_displacement / (self.vessel_length_waterline ** 3)) ** 0.16302))

        c_1 = 2223105 * (c_7 ** 3.78613) * ((self.vessel_draught / self.vessel_width) ** 1.07961) * (90 - angle_waterline_bulbousbow) ** (-1.37165)
        c_3 = (0.56 * area_transverse_bulb**1.5)/(self.vessel_width * self.vessel_draught *(0.31 * np.sqrt(area_transverse_bulb)+ self.vessel_draught_forward - center_transverse_area))
        if self.bulbous_bow == 'yes':
            c_2 = np.exp(-1.89 * np.sqrt(c_3))
        else:
            c_2 = 1      # accounts for the effect of the bulbous bow, which is not present at inland ships
        c_5 = 1 - (0.8 * area_transverse_transom) / (
                    self.vessel_width * self.vessel_draught * coefficient_midship)  # influence of the transom stern on the wave resistance

        # parameter c_15 depends on the ratio L^3 / delta
        if (self.vessel_length_waterline ** 3) / water_displacement < 512:
            c_15 = -1.69385
        if (self.vessel_length_waterline ** 3) / water_displacement > 1727:
            c_15 = 0
        else:
            c_15 = -1.69385 + (self.vessel_length_waterline / (water_displacement ** (1 / 3)) - 8) / 2.36

        # parameter c_16 depends on C_P
        if coefficient_prismatic < 0.8:
            c_16 = 8.07981 * coefficient_prismatic - 13.8673 * (coefficient_prismatic ** 2) + 6.984388 * (coefficient_prismatic ** 3)
        else:
            c_16 = 1.73014 - 0.7067 * coefficient_prismatic

        if self.vessel_length_waterline / self.vessel_width < 12:
            lmbda = 1.446 * coefficient_prismatic - 0.03 * (self.vessel_length_waterline / self.vessel_width)
        else:
            lmbda = 1.446 * coefficient_prismatic - 0.36

        m_1 = 0.0140407 * (self.vessel_length_waterline / self.vessel_draught) - 1.75254 * ((water_displacement) ** (1 / 3) / self.vessel_length_waterline) - 4.79323 * (
                   self.vessel_length_waterline / self.vessel_draught) - c_16
        m_2 = c_15 * (coefficient_prismatic**2) *np.exp((-0.1)* (froude_number_waterline**(-2))) 
        
        correction_factor = np.exp(m_1 * (froude_number_waterline**(-0.9)) + m_2 * np.cos(lmbda * (froude_number_waterline ** (-2))))
        
        resistance_wave = c_1 * c_2 * c_5 * water_displacement * self.rho_water * self.gravitatinal_acceleration * correction_factor / 1000

        """5) Bulbous Bow Resistance terms
        - Extra resistance due to bulbousbow. Not for IWT, Yes for Dredging Vessels"""
        # Only include Rb if bulbous bow is present, so make if statement
        
        # Froude number based on immersoin of bulbous bow [-]
        froud_number_immersion_bulbousbow = (velocity_vessel_modified/np.sqrt(self.gravitatinal_acceleration*(self.vessel_draught_forward - center_transverse_area - 0.25*np.sqrt(area_transverse_bulb) + 0.15 * velocity_vessel_modified ** 2)))
        
        #P_B is coefficient for the emergence of bulbous bow
        coefficient_emergence_bulbousbow = (0.56 * np.sqrt(area_transverse_bulb))/(self.vessel_draught_forward - 1.5 * center_transverse_area)
        
        if self.bulbous_bow == "yes":
            resistance_bulbousbow = ((0.11 * np.exp(-3* coefficient_emergence_bulbousbow **2) * froud_number_immersion_bulbousbow**3 * area_transverse_bulb**1.5 * self.rho_water * self.gravitatinal_acceleration)/(1+ froud_number_immersion_bulbousbow**2)) /1000
        else:
            resistance_bulbousbow = 0


        # Resistance due to immersed transom: R_TR [kN]
        froud_number_immersion_transom = velocity_vessel_modified / np.sqrt(2 * self.gravitatinal_acceleration * area_transverse_transom / (self.vessel_width + self.vessel_width * coefficient_waterplane))

        if froud_number_immersion_transom < 5:
            c_6 = 0.2 * (1- 0.2 * froud_number_immersion_transom) # coefficient related to the Froude number and the transom immersion
        else:
            c_6 = 0


        resistance_immersed_transom = (0.5 * self.rho_water * (velocity_vessel_modified ** 2) * area_transverse_transom * c_6) / 1000

        resistance_pressure = resistance_bulbousbow + resistance_immersed_transom

        """6) Residual resistance terms"""  
        if self.vessel_draught / self.vessel_length_waterline < 0.04:
            c_4 = self.vessel_draught / self.vessel_length_waterline
        else:
            c_4 = 0.04
        c2=1
        coefficient_residual = 0.006 * (self.vessel_length_waterline + 100) ** (-0.16) - 0.00205 + 0.003 * np.sqrt(self.vessel_length_waterline / 7.5) * (
                    self.coefficient_block ** 4) * c_2 * (0.04 - c_4)
        resistance_residual = (0.5 * self.rho_water * (velocity_vessel_modified ** 2) * wet_area_total * coefficient_residual) / 1000  # kW


        resistance_total = resistance_fricition + resistance_wave + resistance_pressure + resistance_residual 

        D_s = 0.7 * self.vessel_draught
        w = 0.11 * (0.16 / self.n_propellers) * self.coefficient_block * np.sqrt((water_displacement**(1/3)) / D_s)

        if self.n_propellers == 1:
            t = 0.6 * w * (1 + 0.67 * w)
        else:
            t = 0.8 * w * (1 + 0.25 * w)
        
        efficiency_hydraulic = (1 - t) / (1 - w)
        efficiency_total_loading = self.efficiency_transmission * self.efficiency_hydrodynamic_loading * self.efficiency_gearing
        efficiency_hydrodynamic_sailing = self.efficency_openwater * self.efficiency_relative_rotative * efficiency_hydraulic
        efficiency_total_sailing = self.efficiency_transmission * efficiency_hydrodynamic_sailing * self.efficiency_gearing

        propulsion_power_loading = resistance_total * velocity_vessel * (1 - efficiency_total_loading)
        propulsion_power_sailing = resistance_total * velocity_vessel * (1 - efficiency_total_sailing)
        



        self.log_entry_v1(
            env.now,
            core.LogState.UNKNOWN,
            {
                "propulsion_power_loading": propulsion_power_loading,
                "propulsion_power_sailing": propulsion_power_sailing
                }
            )
        
        return {
            "propulsion_power_loading": propulsion_power_loading,
            "propulsion_power_sailing": propulsion_power_sailing
        }
        



class IsTSHD(HasTSHDEnergy, HasTSHDProduction, HasDraghead, HasDredgePump, HasVisor, HasJetTSHD, HasPropellerTSHD, Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)