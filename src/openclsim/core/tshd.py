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
    def __init__(self, *args, **kwargs):
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

    def situ_production(self, env, velocity_trailing):      #jet velocity at the working point
        
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

class HasTSHDEnergy(Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class IsTSHD(HasTSHDEnergy, HasTSHDProduction, HasDraghead, HasDredgePump, HasVisor, HasJetTSHD, HasPropellerTSHD, Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)