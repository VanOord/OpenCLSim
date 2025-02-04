"""
This mixin is made to calculate the production rate and energy consumption of a water injection dredger (WID) based on its physical characteristics
"""
import numpy as np
from .simpy_object import SimpyObject

class HasJetBeam(SimpyObject):
    def __init__(self, jet_beam_width, jet_beam_diameter, n_nozzles, velocity_water_jets, nozzle_diameter, water_jet_production, stand_of_distance,
                dredging_speed, nozzle_pressure, undrained_shear_strength, jet_contraction_coefficient, *args, **kwargs):
        self.jet_beam_width = jet_beam_width
        self.jet_beam_diameter = jet_beam_diameter
        self.n_nozzles = n_nozzles
        self.velocity_water_jets = velocity_water_jets
        self.nozzle_diameter = nozzle_diameter
        self.water_jet_production = water_jet_production
        self.stand_of_distance = stand_of_distance
        self.dredging_speed = dredging_speed
        self.nozzle_pressure = nozzle_pressure
        self.undrained_shear_strength = undrained_shear_strength
        self.jet_contraction_coefficient = jet_contraction_coefficient
        super().__init__(*args, **kwargs)

class HasJetPipe(SimpyObject):
    def __init__(self, jet_pipe_length, attachment_cable_length, jet_pipe_diameter, rhu_jet_pipe, c_drag, *args, **kwargs):
        self.jet_pipe_length = jet_pipe_length
        self.attachment_cable_length = attachment_cable_length
        self.jet_pipe_diameter = jet_pipe_diameter
        self.rhu_jet_pipe = rhu_jet_pipe
        self.c_drag = c_drag
        super().__init__(*args, **kwargs)

class HasSoil(SimpyObject):
    def __init__(self, rho_situ, rho_particle, rho_water, rho_cloud, saturation, dredged_volume, dredged_area, mass_flux_coefficient, grain_size_diameter, initial_porosity, *args, **kwargs):
        self.rho_situ = rho_situ
        self.rho_particle = rho_particle
        self.rho_water = rho_water
        self.rho_cloud = rho_cloud
        self.saturation = saturation
        self.dredged_volume = dredged_volume
        self.dredged_area = dredged_area
        self.mass_flux_coefficient = mass_flux_coefficient
        self.grain_size_diameter = grain_size_diameter
        self.initial_porosity = initial_porosity
        super().__init__(*args, **kwargs)

# class HasPropeller(SimpyObject):
#     def __init__(self, env, *args, **kwargs):
#         super().__init__(env, *args, **kwargs)

class HasWIDProduction:
    # """Based on empirical knowledge"""
    # def calculate_production_density(self):
    #     cc_situ = (self.rho_cloud - self.rho_water) / (self.rho_situ - self.rho_water)     # Amount to make 1 cubic meter of situ mixture [m3]
    #     gram_situ = cc_situ * self.rho_situ                                     # Weight of situ mixture [gram]

    #     ratio_water_situ = (1000 / cc_situ) - 1                                 # Ratio of amount of water to be added to dredged volume
    #     Volume_total_water = ratio_water_situ * self.dredged_volume             # Total water amount that needs to be injected in soil [m3]
     
    #     f_entrainment = self.water_jet_production / (self.dredging_speed * SoD * w_jetbar)                   # Ratio of entrainment of jets
    #     #f_entrainment = 1
        
    #     T_dredging = V_total_water / (Q_jet * 3600 * f_entrainment)             # Amount of dredging hours needed [hr]
    
    #     V_total_jet = (Q_jet * 3600) * T_dredging                               # Total jet production [m3]
    #     Q_injection = (Q_jet * 3600) * f_entrainment                            # Total water injected of jets + entrainment[m3/hr]
    
    #     Q_dredged = Q_injection / ratio_water_situ                              # Amount of situ soil dredged [m3/hr]

    #     D_penetration = Q_dredged / (v_dredging * 3600 * w_jetbar)              # Depth of jet penetration [m]
         
    #     return locals()

    """Miedema, S. A. (2019). “Production estimation of water jets in drag heads”. In: Proceedings of the Twenty-Second World Dredging Congress, WODCON XXII, p. 17."""
    """https://www.researchgate.net/publication/332174350_PRODUCTION_ESTIMATION_OF_WATER_JETS_IN_DRAG_HEADS"""
    def calculate_production_miedema(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        jet_pipe_area = ((1/4) * np.pi * self.jet_pipe_diameter **2)    # Area of jet pipe [m]
        jet_velocity_wp = self.water_jet_production / jet_pipe_area     # Jet velocity at working point [m/s]
        
        nozzle_pressure_loss = (1/2) * self.rho_water * ((4 * self.water_jet_production) / 
                                                         (self.jet_contraction_coefficient * np.pi * self.nozzle_diameter**2 * self.n_nozzles)) ** 2    # Pressure loss over nozzle at working point [Pa]

        """Equation (13)"""
        penetration_depth = np.sqrt((self.mass_flux_coefficient * self.rho_water * self.jet_contraction_coefficient * jet_pipe_area * jet_velocity_wp * (2 * nozzle_pressure_loss / self.rho_water)**0.5) / 
                                    (self.rho_particle * (1 - self.initial_porosity) * self.dredging_speed**2))     # Penetration depth [m]

        area_production = self.dredging_speed * self.jet_beam_width     # Area production [m2/s]
        production_miedema = area_production * penetration_depth        # Amount of situ soil dredged [m3/s]
        
        dredging_time_once = self.dredged_area / (area_production)                  # Dredging time of one cycle [s]
        n_cycles = (self.dredged_volume / self.dredged_area) / penetration_depth    # Number of dredging cycle repetitions [-]
        dredging_time_total = dredging_time_once * n_cycles                         # Total dredging time [s]

        return production_miedema
            

        
    def get_state(self):
        state = {}
        if hasattr(super(), "get_state"):
            state = super().get_state()

        state.update({"production miedema": self.production_miedema.get_level()})
        # state.update({"production miedema": self.production_miedema.get_level()})
        # state.update({"production miedema": self.production_miedema.get_level()})
        # state.update({"production miedema": self.production_miedema.get_level()})
        # state.update({"production miedema": self.production_miedema.get_level()})
        return state