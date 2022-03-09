#!/bin/python3

import plasmapy as pp
import astropy.units as u
import astropy.constants as ac
import scipy.constants as sc
import numpy as np
from typing import Union,Optional,Tuple
from typeguard import typechecked
from .core import *
from .laser import *
from .wave import *
from scipy.optimize import bisect

# SRS forest, three modes: laser, raman, epw
# Currently direct backscatter only
@typechecked
class srs_forest(laser_forest):
  def __init__(self,mode:str,*args,**kwargs):
    super().__init__(*args,**kwargs)
    self.omega1 = None # Raman frequency
    self.k1 = None # Raman wavenumber
    self.omega2 = None # EPW frequency
    self.k2 = None # EPW wavenumber
    self.cdamping2 = None # EPW collisonal damping
    self.ldamping2 = None # EPW Landau damping
    self.__mode_check__(mode)

  # Check mode
  def __mode_check__(self,mode:str):
    if mode not in ['fluid','kinetic']:
      raise Exception('Mode argument must be one of \'fluid\' or \'kinetic\'')
    else:
      self.mode = mode

  # Set mode routine with nullifications
  def set_mode(self,mode:str):
    self.__mode_check__(mode)
    self.omega1 = None
    self.k1 = None
    self.omega2 = None
    self.k2 = None
    self.cdamping2 = None
    self.ldamping2 = None

  # Update nullfications on inherited set routines
  def set_ndim(self,*args,**kwargs):
    super().set_ndim(*args,**kwargs)
    self.omega1 = None
    self.k1 = None
    self.omega2 = None
    self.k2 = None
    self.cdamping2 = None
    self.ldamping2 = None
  def set_electrons(self,*args,**kwargs):
    super().set_electrons(*args,**kwargs)
    self.omega1 = None
    self.k1 = None
    self.omega2 = None
    self.k2 = None
    self.cdamping2 = None
    self.ldamping2 = None
  def set_ions(self,*args,**kwargs):
    super().set_ions(*args,**kwargs)
    self.cdamping2 = None
    self.ldamping2 = None
  def set_intensity(self,*args,**kwargs):
    super().set_intensity(*args,**kwargs)

  # Get matching wavenumbers and frequencies by fluid dispersion
  def fluid_matching(self):
    # Check omega0 and k0 already set
    if self.omega0 is None:
      self.get_omega0()
    if self.k0 is None:
      self.get_k0()

    # Solve for EPW wavenumber and set other unknowns
    self.k2 = bisect(self.__bsrs__,self.k0,2*self.k0) # Look between k0 and 2k0
    self.omega2 = self.bohm_gross(self.k2,target='omega')
    self.k1 = self.k0 - self.k2
    self.omega1 = self.omega0 - self.omega2

  # Raman dispersion residual from k2
  def __bsrs__(self,k2):
    omega_ek = self.bohm_gross(k2,target='omega')
    return self.emw_dispersion_res((self.omega0-omega_ek),(self.k0-k2))

  # EPW collisional damping
  # Calculated according to Rand - Collision Damping of Electron Plasma Waves (1965)
  def get_cdamping2(self):
    if self.omega2 is None:
      if mode == 'fluid':
        self.fluid_matching()
      else:
        raise Exception('Kinetic resonance matching not implemented')
    self.cdamping2 = self.epw_coll_damping(self.omega2)

  # Get matching wavenumbers/frequencies by kinetic dispersion

  # Set wavenumbers and frequencies manually