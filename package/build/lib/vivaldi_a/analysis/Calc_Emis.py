'''
Calc_Emis.py
this code is designed for calculating emission total amount in a specific region (or global)
can be used for either finite volume or spectral element (+ regional refinement)
(1) Emission calculation (class Calc_Emis_T)

MODIFICATION HISTORY:
    Duseong Jo, 22, JAN, 2021: VERSION 1.00
    - Initial version
    Duseong Jo, 09, FEB, 2021: VERSION 1.10
    - Bug fix for non-xarray case
    Duseong Jo, 19, FEB, 2021: VERSION 1.20
    - Minor bug fix for time construction 
      before 1900 in using datetime64
    Duseong Jo, 28, FEB, 2021: VERSION 2.00
    - Now can deal with vertical coordinates
    Duseong Jo, 08, MAR, 2021: VERSION 2.01
    - Add additional unit for calculation
    Duseong Jo, 08, MAR, 2021: VERSION 2.101
    - Add addtional capability to calculate time array 
    - in case xarray can't decode time variables
    Duseong Jo, 16, MAR, 2021: VERSION 2.20
    - Add additional vertical dimension variable to deal with CAMS-AIR
'''

### Module import ###
import numpy as np
import xarray as xr
import cftime
import calendar
import datetime


class Calc_Emis_T(object):
    '''
    NAME:
           Calc_Emis_T

    PURPOSE:
           Calculate total emissions in a specific region or global

    INPUTS:
           var: an emission variable array or an xarray variable
           dimension: list. if var is not an xarray, dimension must be specified
                      e.g., dimension = ['time','lat','lon']
                            dimension = ['time','ncol']
                            dimension = ['lat','lon']
           dim_var: dictionary. if var is not an xarray, dimension must be specified
                      supported dimensions are time, lat, lon, ncol (SE) 
                      e.g., dim_var = {'time':datetime64[ns] array,
                                       'lat':[-89.95,-89.85,...,89.85,89.95],
                                       'lon':[-179.95,-179.85,...,179.85,179.95] }
                            dim_var = {'time':[2000-01-15,2000-02-15,...,2020-12-15],
                                       'ncol':[0,1,...,97417] }
           unit: unit of the provided emission array
                 e.g., unit = 'molecules/cm2/s', 'kg/m2/s'
           mw: molecular weight of the species in g/mol (e.g., 28 for CO)
               if provided, it overwrites mw of xarray (if available)
           date_range: 2-elements list with date ranges to calculate emissions
                       e.g., [2000,05,01, 2001,04,30]
           lon_range: 2-elements list with longitude ranges to calculate emissions
           lat_range: 2-elements list with latitude ranges to calculate emissions
           ndays: number of days for emission arrays when time dimension doesn't exist
           scrip_file: a scrip filename for spectral element model output 
           print_results: print results?
           ignore_warning: ignore warning?
           verbose: Display detailed information on what is being done
    '''
    
    def __init__(self, var, dimension=[], dim_var={}, unit='', mw=None,
                 date_range=[], lon_range=[], lat_range=[], 
                 ndays=31, scrip_file="", print_results=True, ignore_warning=False,
                 verbose=False):
        
        # ========================================================================
        # ===== Error check and pass input values to class-accessible values =====
        # ========================================================================
        # xarray and variable dimension check
        if type(var) in [ xr.core.dataset.Dataset, xr.core.dataarray.DataArray ]:
            self.xarray_flag = True
            
            self.var = var.values
            self.dimension = list( var.dims )
            self.dim_var = {}
            for dim in self.dimension:
                if dim in dim_var.keys():
                    self.dim_var[dim] = dim_var[dim]
                else:
                    self.dim_var[dim] = np.copy( var[dim].values )
            self.attrs = list( var.attrs.keys() )
            
            if unit != '':
                self.unit = unit.lower()
            elif 'unit' in self.attrs:
                self.unit = var.unit.lower()
            elif 'units' in self.attrs:
                self.unit = var.units.lower()
            else:  
                raise ValueError( "xarray doesn't have an unit attribute, " + \
                                  "unit keyword must be provided" )
            
            if mw != None:
                self.mw = mw
                
            elif 'molecular_weight' in self.attrs:
                if type( var.molecular_weight ) == str:
                    self.mw = np.copy( var.molecular_weight.replace('.f','') ).astype('f')
                elif type( var.molecular_weight ) in [int, float, np.float32, np.float64]:
                    self.mw = np.copy( var.molecular_weight ).astype('f')
                else:
                    raise ValueError( "Check molecular weight variable in NetCDF file!" )
            else:
                raise ValueError( "input array doesn't have an molecular weight attribute, " + \
                                  "mw keyword must be provided" )
              
                    
            if 'molecular_weight_units' in self.attrs:
                self.mw_unit = var.molecular_weight_units.lower()
            else:
                if not ignore_warning:
                    print( 'Warning: the unit of molecular weight is not available, ' + \
                           'assuming g/mol')

        else:
            self.xarray_flag = False
            self.var = np.copy( var )
            
            if dimension == []:
                raise ValueError( '"dimension" must be provided for non-xarray varaible' )
            else:
                self.dimension = dimension

            if dim_var == {}:
                raise ValueError( '"dim_var" must be provided for non-xarray varaible' )
            else:
                self.dim_var = dim_var
                
            if unit == '':
                raise ValueError( '"unit" must be provided for non-xarray varaible' )
            else:
                self.unit = unit.lower()
                
            if mw == None:
                raise ValueError( '"mw" must be provided for non-xarray varaible' )
            else:
                self.mw = mw

        # lon_range dimension check
        if lon_range == []:
            self.lon_range = [-180, 180] # make it global range
            self.region_calc = False
        else:
            self.lon_range = lon_range
            self.region_calc = True

        # lat_range dimension check
        if lat_range == []:
            self.lat_range = [-90, 90] # make it global range
            self.region_calc = False
        else:
            self.lat_range = lat_range
            self.region_calc = True
            
        
        # Check whether the grid is FV or SE
        if 'ncol' in self.dimension:
            self.grid_type = 'SE'
        elif 'lat' in self.dimension:
            self.grid_type = 'FV'
        else:
            raise ValueError( 'Check dimensions!' )
         
        # Check altitude/vertical coordinatess
        if 'altitude' in self.dimension:
            self.vert = True
            self.vert_name = 'altitude'
        elif 'level' in self.dimension:
            self.vert = True
            self.vert_name = 'level'
        else:
            self.vert = False
            
        if self.vert:

            self.vert_mid = self.dim_var[self.vert_name]

            if 'altitude_int' in self.dimension:
                self.vert_int = self.dim_var['altitude_int']
            else:
                self.vert_int = np.zeros( len(self.vert_mid)+1 )
                for vi in np.arange( len(self.vert_mid)-1 ):
                    self.vert_int[vi] = self.vert_mid[vi] - \
                                        (self.vert_mid[vi+1] - self.vert_mid[vi]) / 2.
                self.vert_int[-1] = self.vert_mid[-1] + \
                                    (self.vert_mid[-1] - self.vert_mid[-2]) / 2.
                self.vert_int[-2] = self.vert_mid[-2] + \
                                    (self.vert_mid[-2] - self.vert_mid[-3]) / 2.
            
            # Thickness
            self.vert_thick = np.zeros( len(self.vert_mid) )

            if self.xarray_flag:
                if var[self.vert_name].units == 'km':
                    self.vert_fac = 1000
                elif var[self.vert_name].units == 'm':
                    self.vert_fac = 1
                elif var[self.vert_name].units == 'cm':
                    self.vert_fac = 0.1
                else:
                    if not ignore_warning:
                        print( 'Warning: the unit of altitude is not available, ' + \
                               'assuming km')
                    self.vert_fac = 1000
            else:
                    if not ignore_warning:
                        print( 'Warning: the unit of altitude is not available, ' + \
                               'assuming km')
                    self.vert_fac = 1000                
                
            for vi in np.arange( len(self.vert_mid) ):
                self.vert_thick[vi] = (self.vert_int[vi+1] - self.vert_int[vi]) * self.vert_fac

            
        # Read scrip file in case of SE model output
        if self.grid_type == 'SE':
            if scrip_file == "":
                raise ValueError( '"scrip_file" must be specified for SE grid emission' )
            if type(scrip_file) != str:
                raise ValueError( '"scrip_file" must be provided as "string"' )
            if verbose:
                print( "Read SCRIP file:", scrip_file )
            ds_scrip = xr.open_dataset( scrip_file )
            self.dim_var['corner_lon'] = np.copy( ds_scrip.grid_corner_lon.values )
            self.dim_var['corner_lat'] = np.copy( ds_scrip.grid_corner_lat.values )
            self.dim_var['center_lon'] = np.copy( ds_scrip.grid_center_lon.values )
            self.dim_var['center_lat'] = np.copy( ds_scrip.grid_center_lat.values )
            self.grid_area_rad2 = np.copy( ds_scrip.grid_area.values )

        # Save remaining input keywords info
        self.ndays = ndays
        self.date_range = date_range
        self.scrip_file = scrip_file
        self.print_results = print_results
        self.verbose = verbose
        # === END Error check and pass input values to class-accessible values ===
        # ========================================================================


        # =======================================================================
        # ============================ Initial Setup ============================
        # =======================================================================        
        # If lon_range doesn't match longitude values, 
        # shift longitude values by 180 degree
        if self.grid_type == 'FV': # 2D FV model output
            if ( (np.min(self.lon_range) < 0) & (np.max(self.dim_var['lon']) > 180) ):
                self.dim_var['lon'][ self.dim_var['lon'] > 180. ] -= 360.
                if verbose:
                    print( "FV model: Shift longitude values by 180 degree" )
        else: # 1D SE model output
            if ( (np.min(self.lon_range) < 0) & (np.max(self.dim_var['corner_lon']) > 180) ):
                self.dim_var['corner_lon'][ self.dim_var['corner_lon'] >= 180. ] -= 360.
                self.dim_var['center_lon'][ self.dim_var['center_lon'] >= 180. ] -= 360
                if verbose:
                    print( "SE model: Shift longitude values by 180 degree" )
        # ========================== END Initial Setup ==========================
        # =======================================================================

        # construct time array
        if 'time' in self.dimension:
            self.construct_time_array()
        
        # convert emission unit first: any unit to kg/m2/s
        self.convert_unit()
        
        # calculate grid area in m2
        self.calc_area()

        # calculate emissions in Gg
        self.calc_emis()

        # print results
        if self.print_results:
            if 'time' in self.dimension:
                print( 'time range:', str(self.time_year[0]) + '-' + \
                                      str(self.time_month[0]).zfill(2) + '-' + \
                                      str(self.time_day[0]).zfill(2) + ', ' + \
                                      str(self.time_year[-1]) + '-' + \
                                      str(self.time_month[-1]).zfill(2) + '-' + \
                                      str(self.time_day[-1]).zfill(2)  )
                print( 'year, month, day, emissions [Gg]' )
                for ti, tt in enumerate(self.time_year):
                    print( str(self.time_year[ti]) + ', ' + \
                           str(self.time_month[ti]).zfill(2) + ', ' + \
                           str(self.time_day[ti]).zfill(2) + ', ' + \
                           str(self.emissions_total[ti]/1e6) )
            else:
                    print( str(self.emissions_total/1e6) )

    # ========================================================================
    # =========================== Unit conversion ============================
    # ========================================================================
    # convert any unit to kg/m2/s
    def convert_unit(self):
        Avo = 6.022e23 # molecules / mole
        
        self.conversion_factor = 1.
        if self.unit in ['molecules/cm2/s', 'molecules cm-2 s-1', 'molecules/cm^2/s']:
            self.conversion_factor *= (self.mw / 1e3) / Avo * 1e4
        elif self.unit in ['molecules/cm3/s', 'molecules cm-3 s-1']:
            self.conversion_factor *= (self.mw / 1e3) / Avo * 1e6
        elif self.unit in ['molecules/m2/s', 'molecules m-2 s-1']:
            self.conversion_factor *= (self.mw / 1e3) / Avo
        elif self.unit in ['kg/m2/s', 'kg m-2 s-1']:
            self.conversion_factor = 1.
        else:
            raise ValueError( "This unit is currently not supported: ", self.unit )
        
        self.var_kg_m2_s = self.var * self.conversion_factor    
    # ========================== END Unit conversion =========================
    # ========================================================================
    
    # ========================================================================
    # ============================ Calculate area ============================
    # ========================================================================
    def calc_area(self):
        
        Earth_rad = 6.371e6 # in m
        
        if self.grid_type == 'FV':
            if 'lat' not in self.dim_var.keys():
                raise ValueError( 'Check your dimension variables! ' + \
                                  'Latitude (lat) values are not available' )
            if 'lon' not in self.dim_var.keys():
                raise ValueError( 'Check your dimension variables! ' + \
                                  'Longitude (lon) values are not available' )              
                       
            self.grid_area = np.zeros( ( len(self.dim_var['lat']), 
                                         len(self.dim_var['lon']) ) )
            
            for jj in np.arange( len(self.dim_var['lat']) ):
                if (jj == 0) & ( (self.dim_var['lat'][jj] + 90.) < 0.001 ):
                    self.dlat = self.dim_var['lat'][jj+1] - self.dim_var['lat'][jj]
                    self.dlon = self.dim_var['lon'][jj+1] - self.dim_var['lon'][jj]
                    sedge = ( self.dim_var['lat'][jj] ) * np.pi / 180.
                    nedge = ( self.dim_var['lat'][jj] + self.dlat / 2. ) * np.pi / 180.
                elif (jj == len(self.dim_var['lat'])-1) & ( (self.dim_var['lat'][jj] - 90.) < 0.001 ):
                    self.dlat = self.dim_var['lat'][jj] - self.dim_var['lat'][jj-1]
                    self.dlon = self.dim_var['lon'][jj] - self.dim_var['lon'][jj-1]
                    sedge = ( self.dim_var['lat'][jj] - self.dlat / 2. ) * np.pi / 180.
                    nedge = ( self.dim_var['lat'][jj] ) * np.pi / 180.
                else:
                    self.dlat = self.dim_var['lat'][jj+1] - self.dim_var['lat'][jj]
                    self.dlon = self.dim_var['lon'][jj+1] - self.dim_var['lon'][jj]                    
                    sedge = ( self.dim_var['lat'][jj] - self.dlat / 2. ) * np.pi / 180.
                    nedge = ( self.dim_var['lat'][jj] + self.dlat / 2. ) * np.pi / 180.
                    
                    
                self.grid_area[jj,:] = self.dlon * (np.pi/180.) * Earth_rad**(2) \
                                       * ( np.sin(nedge) - np.sin(sedge) )
            
                
        elif self.grid_type == 'SE':
            
            Earth_area = 4 * np.pi * Earth_rad**(2)
        
            self.grid_area = self.grid_area_rad2 / np.sum( self.grid_area_rad2 ) \
                            * Earth_area
    # ============================ END Calculate area ========================
    # ========================================================================    
    
    
    # ========================================================================
    # ========================== Calculate emission ==========================
    # ========================================================================
    def calc_emis(self):
        
        if self.region_calc:
            if self.grid_type == 'FV':
            
                self.lon_inds = np.where( (self.dim_var['lon'] >= self.lon_range[0]) & \
                                          (self.dim_var['lon'] <= self.lon_range[1]) )[0]
                self.lat_inds = np.where( (self.dim_var['lat'] >= self.lat_range[0]) & \
                                          (self.dim_var['lat'] <= self.lat_range[1]) )[0]
                if 'time' in self.dimension:
                    self.emissions_total = np.zeros( len(self.dim_var['time']) )
                    if self.vert:
                        self.emissions_total_v = np.zeros( (len(self.dim_var['time']),
                                                            len(self.dim_var[self.vert_name])) )
                        for ti in self.time_inds:
                            for vi, vt in enumerate(self.dim_var[self.vert_name]):
                                self.emissions_total_v[ti,vi] = \
                                    np.sum(self.var_kg_m2_s[ti,vi, 
                                                            self.lat_inds[0]:self.lat_inds[-1]+1,
                                                            self.lon_inds[0]:self.lon_inds[-1]+1] \
                                     * self.grid_area[self.lat_inds[0]:self.lat_inds[-1]+1,
                                                      self.lon_inds[0]:self.lon_inds[-1]+1]) \
                                * self.time_nseconds[ti] * self.vert_thick[vi]
                            
                            self.emissions_total[ti] = np.sum( self.emissions_total_v[ti,:] )

                    else:
                        for ti in self.time_inds:
                            self.emissions_total[ti] = \
                              np.sum(self.var_kg_m2_s[ti,self.lat_inds[0]:self.lat_inds[-1]+1,
                                                         self.lon_inds[0]:self.lon_inds[-1]+1] \
                                     * self.grid_area[self.lat_inds[0]:self.lat_inds[-1]+1,
                                                      self.lon_inds[0]:self.lon_inds[-1]+1]) \
                              * self.time_nseconds[ti]
                        
                else:
                    if self.vert:
                        self.emissions_total_v = np.zeros( len(self.dim_var[self.vert_name]) )
                        for vi, vt in enumerate(self.dim_var[self.vert_name]):
                            self.emissions_total_v[vi] = np.sum( \
                                    self.var_kg_m2_s[vi, self.lat_inds[0]:self.lat_inds[-1]+1,
                                                         self.lon_inds[0]:self.lon_inds[-1]+1] \
                                         * self.grid_area[self.lat_inds[0]:self.lat_inds[-1]+1,
                                                          self.lon_inds[0]:self.lon_inds[-1]+1] ) \
                                         * self.ndays * 86400. * self.vert_thick[vi]
                            
                        self.emissions_total = np.sum( self.emissions_total_v )
                        
                    else:
                        self.emissions_total = np.sum( \
                                     self.var_kg_m2_s[self.lat_inds[0]:self.lat_inds[-1]+1,
                                                      self.lon_inds[0]:self.lon_inds[-1]+1] \
                                     * self.grid_area[self.lat_inds[0]:self.lat_inds[-1]+1,
                                                      self.lon_inds[0]:self.lon_inds[-1]+1] ) \
                                     * self.ndays * 86400.
                    
            elif self.grid_type == 'SE':
                self.ncol_inds = np.where( \
                                   ( self.dim_var['center_lon'] >= self.lon_range[0] ) & \
                                   ( self.dim_var['center_lon'] <= self.lon_range[-1] ) & \
                                   ( self.dim_var['center_lat'] >= self.lat_range[0] ) & \
                                   ( self.dim_var['center_lat'] <= self.lat_range[-1] ) )[0]
                if 'time' in self.dimension:
                    self.emissions_total = np.zeros( len(self.dim_var['time']) )
                    if self.vert:
                        self.emissions_total_v = np.zeros( (len(self.dim_var['time']),
                                                            len(self.dim_var[self.vert_name])) )
                        for ti in self.time_inds:
                            for vi, vt in enumerate(self.dim_var[self.vert_name]):
                                self.emissions_total_v[ti,vi] = \
                                      np.sum(self.var_kg_m2_s[ti,vi,self.ncol_inds] \
                                                   * self.grid_area[self.ncol_inds]) \
                                                   * self.time_nseconds[ti] * self.vert_thick[vi]
                            self.emissions_total[ti] = np.sum( self.emissions_total_v[ti,:] )
                    else:
                        for ti in self.time_inds:
                            self.emissions_total[ti] = np.sum(self.var_kg_m2_s[ti,self.ncol_inds] \
                                                      * self.grid_area[self.ncol_inds]) \
                                                      * self.time_nseconds[ti]
    
                else:
                    if self.vert:
                        self.emissions_total_v = np.zeros( len(self.dim_var[self.vert_name]) )
                        for vi, vt in enumerate(self.dim_var[self.vert_name]):
                            self.emissions_total_v[vi] = np.sum(self.var_kg_m2_s[vi,self.ncol_inds] \
                                                      * self.grid_area[self.ncol_inds]) \
                                                      * self.ndays * 86400. * self.vert_thick[vi]
                        self.emissions_total = np.sum( self.emissions_total_v )
                    else:
                        self.emissions_total = np.sum(self.var_kg_m2_s[self.ncol_inds] \
                                              * self.grid_area[self.ncol_inds]) \
                                              * self.ndays * 86400.

        else:
            if self.grid_type == 'FV':
                if 'time' in self.dimension:
                    self.emissions_total = np.zeros( len(self.dim_var['time']) )
                    if self.vert:
                        self.emissions_total_v = np.zeros( (len(self.dim_var['time']),
                                                            len(self.dim_var[self.vert_name])) )
                        for ti in self.time_inds:
                            for vi, vt in enumerate(self.dim_var[self.vert_name]):
                                self.emissions_total_v[ti,vi] = np.sum(self.var_kg_m2_s[ti,vi,:,:] \
                                                     * self.grid_area) * self.time_nseconds[ti] \
                                                     * self.vert_thick[vi]
                            self.emissions_total[ti] = np.sum( self.emissions_total_v[ti,:] )
                    else:
                        for ti in self.time_inds:
                            self.emissions_total[ti] = np.sum(self.var_kg_m2_s[ti,:,:] \
                                                      * self.grid_area) * self.time_nseconds[ti]
                else:
                    if self.vert:
                        self.emissions_total_v = np.zeros( len(self.dim_var[self.vert_name]) )
                        for vi, vt in enumerate(self.dim_var[self.vert_name]):
                            self.emissions_total_v[vi] = np.sum( self.var_kg_m2_s[vi,:,:] * \
                                                                 self.grid_area ) \
                                                     * self.ndays * 86400. * self.vert_thick[vi]
                        self.emissions_total = np.sum( self.emissions_total_v )
                    else:
                        self.emissions_total = np.sum( self.var_kg_m2_s * self.grid_area ) \
                                              * self.ndays * 86400.

            elif self.grid_type == 'SE':
                if 'time' in self.dimension:
                    self.emissions_total = np.zeros( len(self.dim_var['time']) )
                    if self.vert:
                        self.emissions_total_v = np.zeros( (len(self.dim_var['time']),
                                                            len(self.dim_var[self.vert_name])) )
                        for ti in self.time_inds:
                            for vi, vt in enumerate(self.dim_var[self.vert_name]):
                                self.emissions_total_v[ti,vi] = np.sum(self.var_kg_m2_s[ti,vi,:] \
                                                      * self.grid_area) * self.time_nseconds[ti] \
                                                      * self.vert_thick[vi]
                            self.emissions_total[ti] = np.sum( self.emissions_total_v[ti,:] )
                    else:
                        for ti in self.time_inds:
                            self.emissions_total[ti] = np.sum(self.var_kg_m2_s[ti,:] \
                                                      * self.grid_area) * self.time_nseconds[ti]
                else:
                    if self.vert:
                        self.emissions_total_v = np.zeros( len(self.dim_var[self.vert_name]) )
                        for vi, vt in enumerate(self.dim_var[self.vert_name]):
                            self.emissions_total_v[vi] = np.sum(self.var_kg_m2_s[vi,:] \
                                                              * self.grid_area) \
                                                    * self.ndays * 86400. * self.vert_thick[vi]
                        self.emissions_total = np.sum( self.emissions_total_v )
                    else:
                        self.emissions_total = np.sum(self.var_kg_m2_s * self.grid_area) \
                                              * self.ndays * 86400.

    # ========================== END Calculate emission ======================
    # ========================================================================    
    
    
    # ========================================================================
    # ========================= Contruct time array ==========================
    # ========================================================================
    def construct_time_array(self):
        
        # ===== Retrieve time info =====
        if self.xarray_flag:
            if type( self.dim_var['time'][0] ) == np.datetime64:
                self.time_year = \
                  self.dim_var['time'].astype('datetime64[Y]').astype('I') + 1970
                self.time_month = \
                  self.dim_var['time'].astype('datetime64[M]').astype('I') % 12 + 1
                self.time_day = \
                  ( self.dim_var['time'].astype('datetime64[D]') - \
                    self.dim_var['time'].astype('datetime64[M]') + 1 ).astype('I')

            elif type( self.dim_var['time'][0] ) in [cftime._cftime.DatetimeGregorian, 
                                                     cftime._cftime.DatetimeNoLeap]:
                self.time_year = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_month = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_day = np.zeros( len(self.dim_var['time']) ).astype('I')

                for ti, timeraw in enumerate( self.dim_var['time'] ):
                    self.time_year[ti] = timeraw.year
                    self.time_month[ti] = timeraw.month
                    self.time_day[ti] = timeraw.day
                    
            elif ( type( self.dim_var['time'][0] ) == str ) & \
                 (  len( self.dim_var['time'][0].split('-') ) == 3 ):
                self.time_year = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_month = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_day = np.zeros( len(self.dim_var['time']) ).astype('I')
                
                for ti, timeraw in enumerate( self.dim_var['time'] ):
                    self.time_year[ti], self.time_month[ti], self.time_day[ti] = \
                        np.array( self.dim_var['time'][ti].split('-') ).astype('I')
                    
            else:
                raise ValueError( 'Currently ' + str(type( self.dim_var['time'][0] )) \
                                + ' is not supported! Check type of the time dimension' )
        
        else:
            if type( self.dim_var['time'][0] ) == np.datetime64:
                self.time_year = \
                  self.dim_var['time'].astype('datetime64[Y]').astype('I') + 1970
                self.time_month = \
                  self.dim_var['time'].astype('datetime64[M]').astype('I') % 12 + 1
                self.time_day = \
                  ( self.dim_var['time'].astype('datetime64[D]') - \
                    self.dim_var['time'].astype('datetime64[M]') + 1 ).astype('I')

            elif type( self.dim_var['time'][0] ) in [cftime._cftime.DatetimeGregorian, 
                                                     cftime._cftime.DatetimeNoLeap]:
                self.time_year = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_month = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_day = np.zeros( len(self.dim_var['time']) ).astype('I')

                for ti, timeraw in enumerate( self.dim_var['time'] ):
                    self.time_year[ti] = timeraw.year
                    self.time_month[ti] = timeraw.month
                    self.time_day[ti] = timeraw.day

            elif ( type( self.dim_var['time'][0] ) == str ) & \
                 (  len( self.dim_var['time'][0].split('-') ) == 3 ):
                self.time_year = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_month = np.zeros( len(self.dim_var['time']) ).astype('I')
                self.time_day = np.zeros( len(self.dim_var['time']) ).astype('I')
                
                for ti, timeraw in enumerate( self.dim_var['time'] ):
                    self.time_year[ti], self.time_month[ti], self.time_day[ti] = \
                        np.array( self.dim_var['time'][ti].split('-') ).astype('I')
                    
            else:
                raise ValueError( 'Currently ' + str(type( self.dim_var['time'][0] )) \
                                + ' is not supported! Check type of the time dimension' )
        # ===== END Retrieve time info =====
        
        
        # ===== Calculate time array for consistency in calculation =====
        # Reference day
        Sdate = datetime.date( 1950, 1, 1 )
        
        self.ndays = np.zeros( len(self.time_year) ).astype('I')
        self.date = []
        # Number of days in this case        
        for ti, timeraw in enumerate( self.dim_var['time'] ):
            self.ndays[ti] = ( datetime.date( self.time_year[ti], self.time_month[ti], 
                                              self.time_day[ti] ) - Sdate ).days
            self.date.append( datetime.datetime( self.time_year[ti], self.time_month[ti],
                                                 self.time_day[ti] ) )
                
        # check whether emission is daily, monthly, or yearly
        if ( ( self.ndays[1] - self.ndays[0] ) > 364 ) & \
           ( ( self.ndays[1] - self.ndays[0] ) < 367 ): # yearly
            self.emis_interval = 'yearly'
            self.time_nseconds = np.zeros( len(self.time_year) )
            for iy, yy in enumerate(self.time_year):
                if calendar.isleap(yy):
                    self.time_nseconds[iy] = 366. * 86400.
                else:
                    self.time_nseconds[iy] = 365. * 86400.
            
        elif ( ( self.ndays[1] - self.ndays[0] ) > 27 ) & \
             ( ( self.ndays[1] - self.ndays[0] ) < 32 ): # monthly
            self.emis_interval = 'monthly'
            self.time_nseconds = np.zeros( len(self.time_month) )
            for im, mm in enumerate(self.time_month):
                dom = calendar.monthrange( self.time_year[im], self.time_month[im] )[1]
                self.time_nseconds[im] = dom * 86400.
        
        elif ( ( self.ndays[1] - self.ndays[0] ) > 0.9 ) & \
             ( ( self.ndays[1] - self.ndays[0] ) < 1.1 ): # daily
            self.emis_interval = 'daily'
            self.time_nseconds = np.zeros( len(self.time_day) )
            for ii, dd in enumerate(self.time_day):
                self.time_nseconds[ii] = 86400.
        
        if self.verbose:
            print( 'Emission time interval: ', self.emis_interval )
        
        
        # ===== Calculate time indices for the time slice option =====
        if self.date_range != []:
            self.date_start_year, self.date_start_month, self.date_start_day = \
                np.array( self.date_range[0].split('-') ).astype('I')
            self.date_end_year, self.date_end_month, self.date_end_day = \
                np.array( self.date_range[1].split('-') ).astype('I')
            
            self.date_start_ndays =  ( datetime.date( self.date_start_year, 
                                                      self.date_start_month, 
                                                      self.date_start_day ) - Sdate ).days
            self.date_end_ndays =  ( datetime.date( self.date_end_year, 
                                                    self.date_end_month, 
                                                    self.date_end_day ) - Sdate ).days
             
            self.time_inds = np.where( ( self.ndays >= self.date_start_ndays ) &
                                       ( self.ndays <= self.date_end_ndays ) )[0]
        else:
            self.time_inds = np.arange( len(self.ndays) )
    # ======================= END Contruct time array ========================
    # ========================================================================
    
    
    # ===== Defining __call__ method =====
    def __call__(self):
        print( '=== var ===')
        print( np.shape(var) )
