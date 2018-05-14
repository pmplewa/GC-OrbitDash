from astropy import constants, units
import numpy as np
import pandas as pd
import rebound
import reboundx


# mass, length and time units
m_unit = units.solMass
l_unit = units.arcsec.to(units.rad)*units.pc
t_unit = units.yr

# factor for converting to observed units
velocity_conversion_factor_per_R0=float((l_unit/t_unit)/(units.km/units.s))

# constants (in the internal units)
gravitational_constant_times_R03 = float(constants.G*m_unit*t_unit**2/l_unit**3)
speed_of_light_times_R0 = float(constants.c*(t_unit/l_unit))

def run_simulation(params):
    # parse input parameters
    R0 = params["R0"]
    start_time = params["start_time"]
    end_time = params["end_time"]
    time_steps = params["time_steps"]
    bodies = params["bodies"]

    # account for factor of R0 in l_unit
    gravitational_constant = gravitational_constant_times_R03/R0**3
    speed_of_light = speed_of_light_times_R0/R0
    velocity_conversion_factor = velocity_conversion_factor_per_R0*R0

    # set up rebound simulation
    sim = rebound.Simulation()
    rebx = reboundx.Extras(sim)
    sim.integrator = "ias15"
    sim.G = gravitational_constant
    sim.t = start_time
    
    # enable post-Newtonian corrections
    gr_effect = rebx.add("gr_full")
    gr_effect.params["c"] = speed_of_light  

    # add particles to simulation
    for body in bodies:
        sim.add(**body)
    
    sim.move_to_com()
    
    t_val = np.linspace(start_time, end_time, time_steps)
    
    # prepare output data frames
    data = {}
    for body in bodies:
        name = body["hash"]
        data[name] = pd.DataFrame(index=t_val,
            columns=["t", "t'", "x", "y", "z", "vx", "vy", "vz", "vrD"])
    
    # perform the orbit integration
    for t_obs in t_val:
        for body in bodies:
            name = body["hash"]
            p = sim.particles[rebound.hash(name)]

            # account for the light propagation delay (Roemer effect)
            sim.integrate(t_obs, exact_finish_time=1) # time of observation
            t = t_obs - (p.z/speed_of_light * (1 - p.vz/speed_of_light))
            sim.integrate(t, exact_finish_time=1) # time of emission

            # calculate the relativistic Doppler shift
            beta_costheta = p.vz/speed_of_light
            beta2 = (p.vx**2 + p.vy**2 + p.vz**2)/speed_of_light**2
            zD = (1 + beta_costheta)/np.sqrt(1 - beta2) - 1

            data[name].loc[t_obs] = {
                "t": t_obs,
                "t'": t,
                "x": -p.y,
                "y": p.x,
                "z": p.z,
                "vx": -p.vy,
                "vy": p.vx,
                "vz": p.vz * velocity_conversion_factor,
                "vrD": (zD*speed_of_light) * velocity_conversion_factor}
    
    return data
