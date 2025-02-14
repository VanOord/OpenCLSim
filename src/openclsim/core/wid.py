"""
This mixin is made to calculate the production rate and energy consumption of a water injection dredger (WID) based on its physical characteristics
"""
import numpy as np
from .simpy_object import SimpyObject
import openclsim.core as core
from .log import Log, LogState, PerformsActivity


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


class HasJetPipeWID(SimpyObject):
    def __init__(self, jet_pipe_length, attachment_cable_length, jet_pipe_diameter, rhu_jet_pipe, c_drag, *args, **kwargs):
        self.jet_pipe_length = jet_pipe_length
        self.attachment_cable_length = attachment_cable_length
        self.jet_pipe_diameter = jet_pipe_diameter
        self.rhu_jet_pipe = rhu_jet_pipe
        self.c_drag = c_drag
        super().__init__(*args, **kwargs)        


class HasPropellerWID(SimpyObject):
    def __init__(self, rho_situ, rho_particle, rho_water,
                 rho_cloud, saturation, dredged_volume,
                 dredged_area, mass_flux_coefficient, grain_size_diameter,
                 initial_porosity, *args, **kwargs):
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


class HasSoilWID(SimpyObject):
    def __init__(self, rho_situ, rho_particle, rho_water,
                 rho_cloud, saturation, dredged_volume,
                 dredged_area, mass_flux_coefficient, grain_size_diameter,
                 initial_porosity, *args, **kwargs):
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





class HasWIDProduction(Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    """Miedema, S. A. (2019). “Production estimation of water jets in drag heads”.
    In: Proceedings of the Twenty-Second World Dredging Congress, WODCON XXII, p. 17."""
    """https://www.researchgate.net/publication/332174350_PRODUCTION_ESTIMATION_OF_WATER_JETS_IN_DRAG_HEADS"""
    
    def calculate_production_miedema(self, env, *args, **kwargs):

        jet_pipe_area = ((1/4) * np.pi * self.jet_pipe_diameter **2)    # Area of jet pipe [m]
        jet_velocity_wp = self.water_jet_production / jet_pipe_area     # Jet velocity at working point [m/s]
        
        nozzle_pressure_loss = (1/2) * self.rho_water * ((4 * self.water_jet_production) / 
                                                         (self.jet_contraction_coefficient * np.pi *
                                                          self.nozzle_diameter**2 * self.n_nozzles)) ** 2   
                                                          # Pressure loss over nozzle at working point [Pa]

        """Equation (13)"""
        penetration_depth = np.sqrt((self.mass_flux_coefficient * self.rho_water * self.jet_contraction_coefficient *
                                     jet_pipe_area * jet_velocity_wp * (2 * nozzle_pressure_loss / self.rho_water)**0.5) / 
                                    (self.rho_particle * (1 - self.initial_porosity) * self.dredging_speed**2)) 
                                    # Penetration depth [m]

        area_production = self.dredging_speed * self.jet_beam_width     # Area production [m2/s]
        production_miedema = area_production * penetration_depth        # Amount of situ soil dredged [m3/s]

        self.log_entry_v1(
            env.now,
            core.LogState.UNKNOWN,
            {"production_miedema": production_miedema}
            )
        
        return {
            "production_miedema": production_miedema,
        }
    

class HasWIDEnergy(Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    """Miedema, S. A. (2019). “Production estimation of water jets in drag heads”.
    In: Proceedings of the Twenty-Second World Dredging Congress, WODCON XXII, p. 17."""
    """https://www.researchgate.net/publication/332174350_PRODUCTION_ESTIMATION_OF_WATER_JETS_IN_DRAG_HEADS"""
    
    def calculate_production_miedema(self, env, *args, **kwargs):

        jet_pipe_area = ((1/4) * np.pi * self.jet_pipe_diameter **2)    # Area of jet pipe [m]
        jet_velocity_wp = self.water_jet_production / jet_pipe_area     # Jet velocity at working point [m/s]
        
        nozzle_pressure_loss = (1/2) * self.rho_water * ((4 * self.water_jet_production) / 
                                                         (self.jet_contraction_coefficient * np.pi *
                                                          self.nozzle_diameter**2 * self.n_nozzles)) ** 2   
                                                          # Pressure loss over nozzle at working point [Pa]

        """Equation (13)"""
        penetration_depth = np.sqrt((self.mass_flux_coefficient * self.rho_water * self.jet_contraction_coefficient *
                                     jet_pipe_area * jet_velocity_wp * (2 * nozzle_pressure_loss / self.rho_water)**0.5) / 
                                    (self.rho_particle * (1 - self.initial_porosity) * self.dredging_speed**2)) 
                                    # Penetration depth [m]

        area_production = self.dredging_speed * self.jet_beam_width     # Area production [m2/s]
        production_miedema = area_production * penetration_depth        # Amount of situ soil dredged [m3/s]

        self.log_entry_v1(
            env.now,
            core.LogState.UNKNOWN,
            {"production_miedema": production_miedema}
            )
        
        return {
            "production_miedema": production_miedema,
        }
    
    
class IsWID(HasWIDEnergy, HasWIDProduction, HasJetBeam, HasJetPipeWID, HasPropellerWID, HasSoilWID):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)