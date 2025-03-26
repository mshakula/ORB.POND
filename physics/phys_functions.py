import numpy as np


def aero_loads(dist, atm, v, C_d, A_ref, m):
    """
    Returns vector of acceleration acting on the spacecraft due to atmospheric drag.

    Args:
        dist (double): Distance from the surface of the planetary body, in km. 
        atm (TBD): Information about the density of the atmosphere of this specific body
        v (array of double): Velocity of the spacecraft, in m/s
        C_d (double, optional):
            Defaults to ____.
        A_ref (double, optional): Reference (frontal) area in m^2.
            Defaults to ____.
        m (double, optional): Mass of the spacecraft, in kg.
            Defaults to ____.

    Returns:
        drag (array of double): Vector describing acceleration on the spacecraft due to atmospheric drag.
    """

    drag = 0
    return drag