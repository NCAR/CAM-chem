'''
Regridding_ESMF.py
this code is designed for regridding between finite volume grid and spectral element mesh
(1) Add_bound values of FV grids for mass conserving regridding (class Add_bounds)
(2) Regrid FV grid values to SE-RR grid values

MODIFICATION HISTORY:
    Duseong Jo, 18, FEB, 2021: VERSION 1.00
    - Initial version
    Duseong Jo, 19, FEB, 2021: VERSION 2.00
    - Adding Regridding capability
    Duseong Jo, 22, FEB, 2021: VERSION 2.10
    - Debuging field setup error from xarray
    Duseong Jo, 23, FEB, 2021: VERSION 3.00
    - Adding writing NetCDF capability
    Duseong Jo, 23, FEB, 2021: VERSION 3.10
    - Bug fix for bilinear regridding
    Duseong Jo, 25, FEB, 2021: VERSION 3.20
    - Bug fix in case input xarray has unit/mw information 
    - in some sectors but not in other sectors
    Duseong Jo, 26, FEB, 2021: VERSION 4.00
    - Update for compatability with very large dataset (>5 GB)
    Duseong Jo, 26, FEB, 2021: VERSION 5.00
    - Adding a speed-up flag for handling very large dataset    
    Duseong Jo, 26, FEB, 2021: VERSION 5.10
    - Adding a custom option for datatype of NetCDF file
    Duseong Jo, 27, FEB, 2021: VERSION 5.20
    - Adding some global attributes for more information
    Duseong Jo, 08, MAR, 2021: VERSION 5.30
    - Adding a flexibiltiy for different grid SE-RR description files
    Duseong Jo, 12, MAR, 2021: VERSION 6.00
    - Adding a flexibility for slicing xarray variables
    Duseong Jo, 17, MAR, 2021: VERSION 6.10
    - To deal with the case that xarray is unable to decode time
    Duseong Jo, 18, MAR, 2021: VERSION 6.20
    - Changing default NetCDF format for compatibility with CESM
    Duseong Jo, 19, MAR, 2021: VERSION 6.30
    - To include info variables with additional dimensions
    Duseong Jo, 22, MAR, 2021: VERSION 6.31
    - Minor bug fix for time dimension check
    Duseong Jo, 26, MAR, 2021: VERSION 6.32
    - Minor bug fix for dealing with large dataset > 60 GB
    Duseong Jo, 07, APR, 2021: VERSION 6.40
    - Bug fix for FV -> FV grid case
    Duseong Jo, 07, APR, 2021: VERSION 6.41
    - Adding an error diagnostic when reading molecular weights
    Duseong Jo, 06, MAY, 2021: VERSION 6.42
    - In case the dimension of the xarray variable is not explicitly defined
    Duseong Jo, 24, SEP, 2021: VERSION 7.00
    - Adding a scale factor keyword 
'''

### Module import ###
import numpy as np
import xarray as xr
import ESMF
import datetime, time, os
import cftime
from netCDF4 import Dataset
import subprocess
from Calc_Emis import Calc_Emis_T


class Add_bounds(object):
    '''
    NAME:
           Add_bounds

    PURPOSE:
           Create new grid information files with longitude/latitude bounds
           in order to be used in mass conservative regridding 

    INPUTS:
           filename: NetCDF file name that has longitude/latitude centers
           newfilename: If provided, this variable will be used for new filename
           creation_date: If True, creation date will be added in the filename
           nc_file_format: NetCDF file format to be used in NetCDF4 library
           verbose: Display detailed information on what is being done  
    '''
    
    def __init__(self, filename, newfilename=None, creation_date=True,
                 nc_file_format='NETCDF3_64BIT_DATA', verbose=False):
        
        # ========================================================================
        # ============= Pass input values to class-accessible values =============
        # ========================================================================
        self.filename = filename
        self.newfilename = newfilename
        self.creation_date = creation_date
        self.verbose = verbose
        # =========== END Pass input values to class-accessible values ===========
        # ========================================================================
        
        # =======================================================================
        # ============================ Initial Setup ============================
        # =======================================================================        
        if self.newfilename != None:
            self.gridfilename = self.newfilename
        else:
            extension_loc = self.filename.find('.nc')
            if extension_loc == -1:
                raise ValueError( 'Check the extension of the file!\n' + \
                                  'Currently only ".nc*" is supported')
            else:                
                self.gridfilename = self.filename[:extension_loc] + '_gridinfo' + \
                                    self.filename[:extension_loc]
            
        if self.creation_date:
            extension_loc = self.gridfilename.find('.nc')

            date_now = datetime.datetime.now()
            YMD = str(date_now.year).zfill(4) + str(date_now.month).zfill(2) + \
                  str(date_now.day).zfill(2)

            self.gridfilename = self.gridfilename[:extension_loc] + '_c' + YMD + \
                                self.gridfilename[extension_loc:]            
        # ========================== END Initial Setup ==========================
        # =======================================================================
        
        # =======================================================================
        # ================ Read the file and save grid info file ================
        # =======================================================================
        ds_in = xr.open_dataset( self.filename, decode_times=False )
        
        # === Open file for grid description === 
        fid = Dataset( self.gridfilename, 'w', format=nc_file_format )
        
        # === create dimension variables ===
        fid.createDimension( 'lat', len(ds_in['lat'].values) )
        fid.createDimension( 'lon', len(ds_in['lon'].values) )
        fid.createDimension( 'bound', 2 )
        
        # === write dimension variables ===
        latvar = fid.createVariable( 'lat', 'f4', ('lat',) )
        lonvar = fid.createVariable( 'lon', 'f4', ('lon',) )
        
        # === copy values ===
        latvar[:] = ds_in['lat'].values
        lonvar[:] = ds_in['lon'].values
        
        
        # === copy attributes ===
        for key in list( ds_in['lat'].attrs.keys() ):
            latvar.setncattr( key, ds_in['lat'].attrs[key] )
        latvar.setncattr( 'bounds', 'lat_bnds' )
        for key in list( ds_in['lon'].attrs.keys() ):
            lonvar.setncattr( key, ds_in['lon'].attrs[key] )
        lonvar.setncattr( 'bounds', 'lon_bnds' )
        
        
        # === create Variables - lon_bnds and lat_bnds ===
        latbndvar = fid.createVariable( 'lat_bnds', 'f8', ('lat','bound') )
        lonbndvar = fid.createVariable( 'lon_bnds', 'f8', ('lon','bound') )
        
       
        # === calculate bounds for longitudes and latitudes ===
        lat_bounds = np.zeros( (len(latvar), 2 ) )
        lon_bounds = np.zeros( (len(lonvar), 2 ) )
        
        lat_interval = ds_in['lat'].values[1] - ds_in['lat'].values[0]
        lon_interval = ds_in['lon'].values[1] - ds_in['lon'].values[0]
        
        lat_bounds[:,0] = ds_in['lat'].values - lat_interval / 2.
        lat_bounds[:,1] = ds_in['lat'].values + lat_interval / 2.
        
        lon_bounds[:,0] = ds_in['lon'].values - lon_interval / 2.
        lon_bounds[:,1] = ds_in['lon'].values + lon_interval / 2.
            
        # === copy values ===
        latbndvar[:] = lat_bounds
        lonbndvar[:] = lon_bounds      
        
        # === Set global attributes ===
        fid.created_by = "Python ESMF function for CAM-chem/MUSICA (Regridding_ESMF.py)"
        fid.original_file = self.filename
        fid.file_creation_time = str( datetime.datetime.now() )
        user_name = subprocess.getoutput( 'echo "$USER"')
        host_name = subprocess.getoutput( 'hostname -f' )
        fid.username = user_name + ' on ' + host_name   
        
        fid.close()
        # ============== END Read the file and save grid info file ==============
        # =======================================================================
        
        
    # ===== Defining __call__ method =====
    def __call__(self):
        print( '=== filename ===')
        print( np.shape(self.filename) )
        
        
        
class Regridding(object):
    '''
    NAME:
           Regridding

    PURPOSE:
           Regridding fields (e.g. emissions, meteorological data, model output, etc.)
           Both finite volume grid and spectral element (with regional refinement) are supported
           Also, it can save regridded fields to NetCDF file
           
    INPUTS:
           var_array: a variable array or xarray variable to be regridded
           fields: a list which has field names in var_array (for xarray case)
                   if xarray has multiple fields, only specified fields provided in this keyword
                   will be processed
           add_fields: list, for additional fields that are not needed to be regridded,
                       but if a user wants to save additional fields in addition to regridded fields. 
                       Must be xarray variable as it also includes attributes
           dimension: list. if var is not an xarray, dimension must be specified
                      e.g., dimension = ['time','lat','lon'] for FV
                            dimension = ['any','any2','lat','lon'] for FV
                            dimension = ['any','ncol'] for SE(-RR)
           dim_var: dictionary. if var_array is not an xarray, dimension must be specified
                             only used for saving NetCDF dimensions if save_file=True
                      e.g., dim_var = {'time':datetime64[ns] array,
                                       'lat':[-89.95,-89.85,...,89.85,89.95],
                                       'lon':[-179.95,-179.85,...,179.85,179.95] }
                            dim_var = {'time':[2000-01-15,2000-02-15,...,2020-12-15],
                                       'ncol':[0,1,...,97417] }
                            dim_var = {'any':['aa','bb','cc',...'zz'],
                                       'ncol':[0,1,...,97417] }
           src_grid_file: grid filename for source field
           dst_grid_file: grid filename for destination field
           wgt_file: weight filename. use the existing weight file (save_weight_file=False)
                                      or create new weight file (save_weight_file=True)
           save_wgt_file: if true, create new weight file
           save_wgt_file_only: if true, save weight file only (not regridding)
           no_wgt_file: if true, doesn't create weight file (useful for one-time regridding)
           creation_date: if true, add the creation date to the end of the filename
           method: regridding method - "Bilinear", 
                                       High-order patch recovery ("Patch"), 
                                       Nearest source to destination ("Nearest_StoD"),
                                       Nearest destination to source ("Nearest_DtoS"),
                                       First-order conservative ("Conserve"),
                                       Second-order conservative ("Conserve_2nd") are supported
           save_results: if True, save the regridded fileds to NetCDF file
           datatype: 'f8' (double) or 'f4' (float)
                     dimension and basic information variables are fixed to f8
           nc_file_format: NetCDF file format to be used in NetCDF4 library
           speed_up: if True, speed up regridding, but doesn't return the results to python shell
                     Good for very large dataset and saving NetCDF file in terms of speed and memory
           dst_file: NetCDF filename for results
           check_results: if true, calculate total of source and destination field
                          can be useful especially for emission processing
           mw: in case check_results=True. To calculate global emission total
           unit: in case check_results=True. To calculate global emission total
           scale_factor: custom scale factor for output
           check_timings: if true, measure time spent for regridding
           ignore_warning: if true, ignore warning messages
           verbose: display detailed information on what is being done
    '''
    
    def __init__(self, var_array, fields=[], add_fields=[], dimension=[], dim_var={}, 
                 src_grid_file=None, dst_grid_file=None, wgt_file=None, save_wgt_file=False,
                 save_wgt_file_only=False, method="Conserve", save_results=True, speed_up=True,
                 datatype='f4',nc_file_format='NETCDF3_64BIT_DATA', dst_file=None, 
                 creation_date=True, check_results=False, mw=None, unit=None, scale_factor=1,
                 check_timings=True, ignore_warning=False, verbose=False):
        # =========================================================================
        # ===== Check errors and Pass input values to class-accessible values =====
        # =========================================================================
        if check_timings:
            self.Sdate = datetime.datetime.now()
            print( 'Initialization start: ', self.Sdate )
        
        # Print warning for speed_up flag when results are not saved
        if (not save_results) & (speed_up):
            print( "Warning: results will not be returned to the shell if speed_up=True" )
            print( "The speed_up flag is turned to False" )
            print( "If you meant to save resulting NetCDF file, turn on the save_results flag")
            self.speed_up = False
        else:
            self.speed_up = speed_up

        # xarray, lon, and lat check
        if type(var_array) in [ xr.core.dataset.Dataset, xr.core.dataarray.DataArray ]:
            self.xarray_flag = True
            self.time_decoded = True
            if 'time' in list( var_array.dims ):
                if type( var_array['time'].values[0] ) not in [cftime._cftime.DatetimeGregorian]:
                    if ('calendar' in dir( var_array['time'] ) ) | \
                       ( ('time' in list(var_array.dims) ) & \
                         ('time' not in list(var_array.coords) ) ) | \
                       ( ( np.dtype( var_array['time'].values[0] ).name ) in ['float32', 'float64'] ):
                        self.time_decoded = False
            else:
                self.time_decoded = False
            
            if type(var_array) in [ xr.core.dataset.Dataset ]:
                self.var_array = var_array
            elif type(var_array) in [ xr.core.dataarray.DataArray ]:
                self.var_array = {var_array.name:var_array}
                for dim in var_array.dims:
                    self.var_array[dim] = var_array[dim]
            
            ncol_check = 'ncol' in list(var_array.dims)
            lat_check = 'lat' in list(var_array.dims)
            lon_check = 'lon' in list(var_array.dims)
            if ( (ncol_check + lat_check + lon_check) < 0.01 ) | \
               ( (ncol_check + lat_check + lon_check) > 2.01 ):
                raise ValueError('check "lon"/"lat"/"ncol" dimensions!' + '\n' + \
                                 'FV model should have "lon" & "lat" dimensions' + '\n' + \
                                 'SE(-RR) model should have "ncol" dimension' )
            else:
                if ( ncol_check == 1 ):
                    self.src_type = 'SE'
                elif (lat_check == 1) & (lon_check ==1):
                    self.src_type = 'FV'
                    self.lon = var_array.lon.values
                    self.lat = var_array.lat.values
                else:
                    raise ValueError('check "lon"/"lat"/"ncol" dimensions!' + '\n' + \
                                     'FV model should have "lon" & "lat" dimensions' + '\n' + \
                                     'SE(-RR) model should have "ncol" dimension' )
                
                self.dim_var = {}
                # Fields and dimensions
                self.fields_file = []
                if type(var_array) in [ xr.core.dataset.Dataset ]:
                    fields_tmp = list( var_array.data_vars )
                elif type(var_array) in [ xr.core.dataarray.DataArray ]:
                    fields_tmp = [ var_array.name ]
                
                for fld in fields_tmp:
                    if fld not in ['lon_bnds', 'lat_bnds', 'time_bnds', 
                                   'lon', 'lat', 'time', 'date', 'datesec',
                                   'crs', 'gridcell_area', 'area']:
                        self.fields_file.append(fld)
                if fields == []:
                    self.fields = self.fields_file
                else:
                    self.fields = fields

                self.var = {}
                for fld in self.fields:
                    if self.speed_up:
                        self.var[fld] = self.var_array[fld]
                    else:
                        self.var[fld] = self.var_array[fld].values

                # Doesn't consider the case that each variable has each different dimension
                if dimension != []:
                    self.dimension = dimension
                else:
                    self.dimension = self.var_array[fld].dims

                # dimension values of var array
                if dim_var != {}:
                    self.dim_var = dim_var
                else:
                    for dim in self.dimension:
                        self.dim_var[dim] = var_array[dim].values

            if mw == None:
                Existence_check = True
                for fld in self.fields_file:
                    if 'molecular_weight' in self.var_array[fld].attrs.keys():
                        if type( self.var_array[fld].molecular_weight ) == str:
                            self.mw = np.copy( self.var_array[fld].molecular_weight.replace('.f','') ).astype('f')
                        elif type( self.var_array[fld].molecular_weight ) in [int, float, np.float32, np.float64]:
                            self.mw = np.copy( self.var_array[fld].molecular_weight ).astype('f')
                        else:
                            raise ValueError( 'Check the type of molecular weight value!\n' + \
                                              'Currently those are supported: str, int, float, np.float32, np.float64' )
                        Existence_check = False
                        break
                if check_results & Existence_check:
                    raise ValueError('If you want check results at the end of the calculation,\n' + \
                                     'please provide mw of species. the input xarray does not have' + \
                                     '"molecular_weight" attribute' )                    
            else:
                self.mw = mw
                    
            if check_results or save_results:
                if unit == None:
                    Exsistence_check = True
                    for fld in self.fields_file:
                        if 'unit' in self.var_array[fld].attrs.keys():
                            self.unit = self.var_array[fld].unit.lower()
                            Exsistence_check = False
                            break
                        elif 'units' in self.var_array[fld].attrs.keys():
                            self.unit = self.var_array[fld].units.lower()
                            Exsistence_check = False
                            break
                    if Exsistence_check:
                        raise ValueError('If you want check or save results at the end of the calculation,\n' + \
                                         'please provide unit of species. the input xarray does not have' + \
                                         '"unit" or "units" attribute' )
                else:
                    self.unit = unit

        else: # non-xarray, only one field calculation is upported for non-xarray case
            self.xarray_flag = False
            
            self.var = var_array
            if dimension == []:
                raise ValueError( '"dimension" must be provided for non-xarray values!' )
            else:
                self.dimension = dimension
            
            if (dim_var == {}) & (save_results):
                raise ValueError( '"dim_var" must be provided if you want to save results' + \
                                  'to NetCDF from non-xarray source values!' )
            else:
                self.dim_var = dim_var

            ncol_check = 'ncol' in dimension
            lat_check = 'lat' in dimension
            lon_check = 'lon' in dimension
            if ( (ncol_check + lat_check + lon_check) < 0.01 ) | \
               ( (ncol_check + lat_check + lon_check) > 2.01 ):
                raise ValueError('check "lon"/"lat"/"ncol" dimensions!' + '\n' + \
                                 'FV model should have "lon" & "lat" dimensions' + '\n' + \
                                 'SE(-RR) model should have "ncol" dimension' )
            else:             
                if ( ncol_check == 1 ):
                    self.src_type = 'SE'
                elif (lat_check == 1) & (lon_check ==1):
                    self.src_type = 'FV'
                    self.lon = self.dim_var['lon']
                    self.lat = self.dim_var['lat']
                else:
                    raise ValueError('check "lon"/"lat"/"ncol" dimensions!' + '\n' + \
                                     'FV model should have "lon" & "lat" dimensions' + '\n' + \
                                     'SE(-RR) model should have "ncol" dimension' )          

            if check_results:
                if (mw == None) | (unit == None):
                    raise ValueError('mw and unit must be provided for checking results')
                else:
                    self.mw = mw
                    self.unit = unit

            self.fields = []
        
        # grid file names check
        if src_grid_file == None:
            raise ValueError( 'Source grid file ("src_grid_file") must be provided' )
        else:
            self.src_grid_file = src_grid_file
        if dst_grid_file == None:
            raise ValueError( 'Destination grid file ("dst_grid_file") must be provided' )
        else:
            self.dst_grid_file = dst_grid_file
        if wgt_file == None:
            raise ValueError( 'Grid Weight filename ("wgt_file") must be provided' )
        else:
            self.wgt_file = wgt_file
        if save_results:
            if dst_file == None:
                raise ValueError( 'Filename for regridded fields ("dst_file") must be provided' )
            else:
                self.dst_file = dst_file
         
        # regridding_method
        if method.lower() == "bilinear":
            self.method = ESMF.RegridMethod.BILINEAR
        elif method.lower() == "patch":
            self.method = ESMF.RegridMethod.PATCH
        elif method.lower() == "nearest_stod":
            self.method = ESMF.RegridMethod.NEAREST_STOD
        elif method.lower() == "nearest_dtos":
            self.method = ESMF.RegridMethod.NEAREST_DTOS
        elif method.lower() == "conserve":
            self.method = ESMF.RegridMethod.CONSERVE
        elif method.lower() == "conserve_2nd":
            self.method = ESMF.RegridMethod.CONSERVE_2ND
        else:
            raise ValueError( 'Check method! - ', method + ' is not available' )
        if verbose:
            print( 'Regridding method used: ' + method )
        
        # add creation date if creation_date=True
        self.creation_date = creation_date
        if creation_date:
            if save_wgt_file:
                extension_loc = self.wgt_file.find('.nc')
                date_now = datetime.datetime.now()
                self.YMD = str(date_now.year).zfill(4) + str(date_now.month).zfill(2) + \
                           str(date_now.day).zfill(2)

                self.wgt_file = self.wgt_file[:extension_loc] + '_c' + self.YMD + \
                                self.wgt_file[extension_loc:]
            
            if save_results:
                extension_loc = self.dst_file.find('.nc')
                date_now = datetime.datetime.now()
                self.YMD = str(date_now.year).zfill(4) + str(date_now.month).zfill(2) + \
                           str(date_now.day).zfill(2)

                self.dst_file = self.dst_file[:extension_loc] + '_c' + self.YMD + \
                                self.dst_file[extension_loc:]                
        
        self.add_fields          = add_fields
        self.save_wgt_file       = save_wgt_file
        self.save_wgt_file_only  = save_wgt_file_only
        self.save_results        = save_results
        self.datatype            = datatype
        self.nc_file_format      = nc_file_format
        self.creation_date       = creation_date
        self.check_results       = check_results
        self.check_timings       = check_timings
        self.scale_factor        = scale_factor
        self.ignore_warning      = ignore_warning
        self.verbose             = verbose
        # === END Check errors and Pass input values to class-accessible values ===
        # =========================================================================

        # =======================================================================
        # ============================ Initial setup ============================
        # =======================================================================
        # Check whether destination grid is FV or SE(-RR)
        dst_grid_info = xr.open_dataset( self.dst_grid_file )
        if ('lat' in list( dst_grid_info.dims )) & \
           ('lon' in list( dst_grid_info.dims )):
            self.dst_type = 'FV'
        elif list( dst_grid_info.coords.keys() ) == []:
            if len( dst_grid_info['grid_dims'].values ) == 1:
                self.dst_type = 'SE'
            elif len( dst_grid_info['grid_dims'].values ) == 2:
                self.dst_type = 'FV'
            else:
                raise ValueError( 'Check "grid_dims" in destination grid file!' + '\n' + \
                                  'It should be 1 (SE) or 2 (FV) dimensions' )
        else:
            raise ValueError( 'Check destination grid file!' + '\n' + \
                              'Something wrong with lat/lon/ncol information' )
        
        # Setup dimension & shape of destination array
        xdst_grid = xr.open_dataset( self.dst_grid_file )
        
        self.dst_dim = []
        self.dst_shape = []
        self.dst_dim_loop = []
        self.dst_shape_loop = []
        for di, dim in enumerate(self.dimension):
            if dim in ['lat','lon','ncol']:
                continue
            else:
                self.dst_dim.append( dim )
                self.dst_dim_loop.append( dim )
                if self.fields != []:
                    self.dst_shape.append( np.shape(self.var[self.fields[0]])[di] )
                    self.dst_shape_loop.append( np.shape(self.var[self.fields[0]])[di] )
                else:
                    self.dst_shape.append( np.shape(self.var)[di] )
                    self.dst_shape_loop.append( np.shape(self.var)[di] )
                
        if self.dst_type == 'FV':
            self.dst_dim.append('lat')
            self.dst_shape.append( len(xdst_grid['lat'].values) )
            self.dst_dim.append('lon')
            self.dst_shape.append( len(xdst_grid['lon'].values) )
        elif self.dst_type == 'SE':
            self.dst_dim.append('ncol')
            self.dst_shape.append( len( xdst_grid.grid_size ) )

        # Setup destination array
        if not self.speed_up:
            if self.xarray_flag:
                self.var_dst = {}
                for fld in self.fields:
                    self.var_dst[fld] = np.zeros( self.dst_shape )
            else:
                self.var_dst = np.zeros( self.dst_shape )
            
        if self.check_timings:
            self.Edate = datetime.datetime.now()
            print( 'Initialization end: ', self.Edate )
            print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                           time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
            print( '========================================================================')
        # ========================== END Initial setup ==========================
        # =======================================================================
        # Call regridding function using ESMF
        self.call_ESMF()
        
    def call_ESMF(self):
        # =======================================================================
        # ==================== Generate regridding operator =====================
        # =======================================================================
        if self.check_timings:
            self.Sdate = datetime.datetime.now()
            print( 'Grid/Field setup start: ', self.Sdate )
        
        # === Construct FV grid or SE(-RR) mesh ===
        # === Create a field on the center stagger locations of the source/destination grid
        # === or Create a field on the nodes of the source/destination mesh
        # Source grid
        if self.src_type == 'FV':
            #if self.method in [ESMF.RegridMethod.BILINEAR]:
            #    self.src_grid = ESMF.Grid( filename=self.src_grid_file, 
            #                               filetype=ESMF.FileFormat.GRIDSPEC )
            #else:
            self.src_grid = ESMF.Grid( filename=self.src_grid_file, 
                                       filetype=ESMF.FileFormat.GRIDSPEC,
                                       add_corner_stagger=True )
            self.src_field = ESMF.Field( self.src_grid, name='srcfield', 
                                         staggerloc=ESMF.StaggerLoc.CENTER )
        elif self.src_type == 'SE':
            self.src_grid = ESMF.Mesh( filename=self.src_grid_file, 
                                       filetype=ESMF.FileFormat.SCRIP )
            #if self.method in [ESMF.RegridMethod.BILINEAR,
            #                   ESMF.RegridMethod.PATCH,
            #                   ESMF.RegridMethod.NEAREST_STOD]:
            #    self.src_field = ESMF.Field( self.src_grid, name='srcfield',
            #                             meshloc=ESMF.MeshLoc.NODE )
            #else:
            self.src_field = ESMF.Field( self.src_grid, name='srcfield',
                                         meshloc=ESMF.MeshLoc.ELEMENT )
        # Destination grid
        if self.dst_type == 'FV':
            self.dst_grid = ESMF.Grid( filename=self.dst_grid_file, 
                                       filetype=ESMF.FileFormat.GRIDSPEC,
                                       add_corner_stagger=True )
            self.dst_field = ESMF.Field( self.dst_grid, name='dstfield', 
                                         staggerloc=ESMF.StaggerLoc.CENTER )
        elif self.dst_type == 'SE':
            self.dst_grid = ESMF.Mesh( filename=self.dst_grid_file, 
                                       filetype=ESMF.FileFormat.SCRIP )

            #if self.method in [ESMF.RegridMethod.BILINEAR,
            #                   ESMF.RegridMethod.PATCH,
            #                   ESMF.RegridMethod.NEAREST_STOD]:
            #    self.dst_field = ESMF.Field( self.dst_grid, name='dstfield',
            #                                 meshloc=ESMF.MeshLoc.NODE )                
            #else:
            self.dst_field = ESMF.Field( self.dst_grid, name='dstfield',
                                             meshloc=ESMF.MeshLoc.ELEMENT )
        
        if self.check_timings:
            self.Edate = datetime.datetime.now()
            print( 'Grid/Field setup end: ', self.Edate )
            print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                           time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
            print( '========================================================================')
            
        if self.save_wgt_file: 
            if self.check_timings:
                self.Sdate = datetime.datetime.now()
                print( 'Generating weight start: ', self.Sdate )

            try:
                self.regrid = ESMF.Regrid( self.src_field, self.dst_field, 
                                          filename=self.wgt_file, regrid_method=self.method )
            except:
                print( "Regridding failed: adding unmappaed_action")
                self.regrid = ESMF.Regrid( self.src_field, self.dst_field, 
                                          filename=self.wgt_file, regrid_method=self.method,
                                          unmapped_action=ESMF.UnmappedAction.IGNORE)               
            # Some possible options
            # unmapped_action=ESMF.UnmappedAction.IGNORE
            # ignore_degenerate=True

            if self.check_timings:
                self.Edate = datetime.datetime.now()
                print( 'Generating weight end: ', self.Edate )
                print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                               time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
                print( '========================================================================')
            if self.save_wgt_file_only:
                return
        else:
            if self.check_timings:
                self.Sdate = datetime.datetime.now()
                print( 'Read regridding weight start: ', self.Sdate )
            self.regrid = ESMF.RegridFromFile( self.src_field, self.dst_field, self.wgt_file )
            if self.check_timings:
                self.Edate = datetime.datetime.now()
                print( 'Read regridding weight end: ', self.Edate )
                print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                               time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
                print( '========================================================================')
        
        # ================== END Generate regridding operator ===================
        # =======================================================================
               
        if not self.speed_up:   
            # =======================================================================
            # ============================= Regridding ==============================
            # =======================================================================            
            if self.check_timings:
                self.Sdate = datetime.datetime.now()
                print( 'Regridding start: ', self.Sdate )

            self.N_loops = len( self.dst_dim_loop )
            if self.fields == []:
                if self.N_loops == 0:
                    if self.src_type == 'FV':
                        self.src_field.data[...] = np.swapaxes( self.var, 0, 1 )
                        self.var_dst[:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                    elif self.src_type == 'SE':
                        self.src_field.data[...] = self.var
                        self.var_dst[:] = self.regrid( self.src_field, self.dst_field ).data
                elif self.N_loops == 1:
                    for ii in np.arange( self.dst_shape_loop[0] ):
                        if self.src_type == 'FV':
                            self.src_field.data[...] = np.swapaxes( self.var[ii,:,:], 0, 1)
                            self.var_dst[ii,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                        elif self.src_type == 'SE':
                            self.src_field.data[...] = self.var[ii,:]
                            self.var_dst[ii,:] = self.regrid( self.src_field, self.dst_field ).data
                elif self.N_loops == 2:
                    for ii in np.arange( self.dst_shape_loop[0] ):
                        for jj in np.arange( self.dst_shape_loop[1] ):
                            if self.src_type == 'FV':
                                self.src_field.data[...] = np.swapaxes( self.var[ii,jj,:,:], 0, 1)
                                self.var_dst[ii,jj,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                            elif self.src_type == 'SE':
                                self.src_field.data[...] = self.var[ii,jj,:]
                                self.var_dst[ii,jj,:] = self.regrid( self.src_field, self.dst_field ).data
                else:
                    raise ValueError( 'Check number of dimensions in the destination field' )
            else:
                for fld in self.fields:
                    if self.N_loops == 0:
                        if self.src_type == 'FV':
                            self.src_field.data[...] = np.swapaxes( self.var[fld], 0, 1 )
                            self.var_dst[fld][:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                        elif self.src_type == 'SE':
                            self.src_field.data[...] = self.var[fld]
                            self.var_dst[fld][:] = self.regrid( self.src_field, self.dst_field ).data
                    elif self.N_loops == 1:
                        for ii in np.arange( self.dst_shape_loop[0] ):
                            if self.src_type == 'FV':
                                self.src_field.data[...] = np.swapaxes( self.var[fld][ii,:,:], 0, 1)
                                self.var_dst[fld][ii,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                            elif self.src_type == 'SE':
                                self.src_field.data[...] = self.var[fld][ii,:]
                                self.var_dst[fld][ii,:] = self.regrid( self.src_field, self.dst_field ).data
                    elif self.N_loops == 2:
                        for ii in np.arange( self.dst_shape_loop[0] ):
                            for jj in np.arange( self.dst_shape_loop[1] ):
                                if self.src_type == 'FV':
                                    self.src_field.data[...] = np.swapaxes( self.var[fld][ii,jj,:,:], 0, 1)
                                    self.var_dst[fld][ii,jj,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                                elif self.src_type == 'SE':
                                    self.src_field.data[...] = self.var[fld][ii,jj,:]
                                    self.var_dst[fld][ii,jj,:] = self.regrid( self.src_field, self.dst_field ).data
                    else:
                        raise ValueError( 'Check number of dimensions in the destination field' )

            if self.check_timings:
                self.Edate = datetime.datetime.now()
                print( 'Regridding end: ', self.Edate )
                print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                               time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
                print( '========================================================================')

            # =========================== END Regridding ============================
            # =======================================================================

            # =======================================================================
            # ==== Check results - total emission for the first and last indices ====
            # =======================================================================
            if self.check_results:
                xsrc_grid = xr.open_dataset( self.src_grid_file )
                xdst_grid = xr.open_dataset( self.dst_grid_file )
                if self.src_type == 'FV':
                    src_dim_var = { 'lat':xsrc_grid['lat'].values,
                                    'lon':xsrc_grid['lon'].values }
                    src_FV_kwds = {'dimension':['lat','lon'],
                                   'dim_var':src_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }
                elif self.src_type == 'SE':
                    src_dim_var = { 'ncol':xsrc_grid.grid_size.values }
                    src_SE_kwds = {'scrip_file':self.src_grid_file,
                                   'dimension':['ncol'],
                                   'dim_var':src_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }                
                if self.dst_type == 'FV':
                    dst_dim_var = { 'lat':xdst_grid['lat'].values,
                                    'lon':xdst_grid['lon'].values }
                    dst_FV_kwds = {'dimension':['lat','lon'],
                                   'dim_var':dst_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }
                elif self.dst_type == 'SE':
                    dst_dim_var = { 'ncol':xdst_grid.grid_size.values }
                    dst_SE_kwds = {'scrip_file':self.dst_grid_file,
                                   'dimension':['ncol'],
                                   'dim_var':dst_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }

                if self.fields == []:
                    if self.N_loops == 0:
                        if self.src_type == 'FV':
                            SRC_EMIS = Calc_Emis_T( self.var, **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS = Calc_Emis_T( self.var, **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS = Calc_Emis_T( self.var_dst, **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS = Calc_Emis_T( self.var_dst, **dst_SE_kwds )
                        print( 'Source total for the block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS.emissions_total) ) )
                        print( 'Destination total for the block [g]: ' + \
                                "{:.2e}".format(np.around(DST_EMIS.emissions_total) ) )
                    elif self.N_loops == 1:
                        if self.src_type == 'FV':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,:,:], **src_FV_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,:,:], **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,:], **src_SE_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,:], **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:,:], **dst_FV_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:,:], **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:], **dst_SE_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:], **dst_SE_kwds )
                        print( 'Source total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                        print( 'Destination total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                        print( 'Source total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                        print( 'Destination total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )
                    elif self.N_loops == 2:
                        if self.src_type == 'FV':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,0,:,:], **src_FV_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,-1,:,:], **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,0,:], **src_SE_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,-1,:], **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:,:], **dst_FV_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:,:], **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:], **dst_SE_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:], **dst_SE_kwds )
                        print( 'Source total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                        print( 'Destination total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                        print( 'Source total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                        print( 'Destination total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )
                else:
                    for fld in self.fields:
                        print( '========================================================================')
                        print( 'Fields: ', fld )
                        print( '------------------------------------------------------------------------')
                        if self.N_loops == 0:
                            if self.src_type == 'FV':
                                SRC_EMIS = Calc_Emis_T( self.var[fld], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS = Calc_Emis_T( self.var[fld], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS = Calc_Emis_T( self.var_dst[fld], **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS = Calc_Emis_T( self.var_dst[fld], **dst_SE_kwds )
                            print( 'Source total for the block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS.emissions_total) ) )
                            print( 'Destination total for the block [g]: ' + \
                                    "{:.2e}".format(np.around(DST_EMIS.emissions_total) ) )
                        elif self.N_loops == 1:
                            if self.src_type == 'FV':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,:,:], **src_FV_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,:,:], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,:], **src_SE_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,:], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[fld][0,:,:], **dst_FV_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[fld][-1,:,:], **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[fld][0,:], **dst_SE_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[fld][-1,:], **dst_SE_kwds )
                            print( 'Source total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                            print( 'Destination total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                            print( 'Source total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                            print( 'Destination total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )  
                        elif self.N_loops == 2:
                            if self.src_type == 'FV':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,0,:,:], **src_FV_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,-1,:,:], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,0,:], **src_SE_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,-1,:], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[fld][0,0,:,:], **dst_FV_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[fld][-1,-1,:,:], **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[fld][0,0,:], **dst_SE_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[fld][-1,-1,:], **dst_SE_kwds )
                            print( 'Source total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                            print( 'Destination total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                            print( 'Source total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                            print( 'Destination total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )

            # == END Check results - total emission for the first and last indices ==
            # =======================================================================                        

            # =======================================================================
            # ===================== Save results to NetCDF file =====================
            # =======================================================================
            if self.save_results:
                if self.check_timings:
                    self.Sdate = datetime.datetime.now()
                    print( 'Saving NetCDF file start: ', self.Sdate )

                # load grid decsription files
                xdst_grid = xr.open_dataset( self.dst_grid_file )

                # Open NetCDF file for writing
                fid = Dataset( self.dst_file, 'w', format=self.nc_file_format )

                # ===== Create dimensions =====
                for di, dimname in enumerate(self.dst_dim):
                    if dimname == 'time':
                        # unlimited time dimension
                        fid.createDimension( dimname )
                        self.construct_time_array()
                    else:
                        fid.createDimension( dimname, self.dst_shape[di] )

                    # write dimension variables
                    dimvar = fid.createVariable( dimname, 'f8', (dimname,) )
                    if dimname in ['lon','lat']:
                        dimvar[:] = np.copy( xdst_grid[dimname].values )
                    elif dimname in ['ncol']:
                        dimvar[:] = np.copy( xdst_grid.grid_size.values )
                    elif dimname  == 'time':
                        dimvar[:] = self.time_array
                    else:
                        dimvar[:] = np.copy( self.var_array[dimname].values )

                    # Add attributes for dimensions
                    if dimname in ['lon','lat']:
                        for key in list( xdst_grid[dimname].attrs.keys() ):
                            dimvar.setncattr( key, xdst_grid[dimname].attrs[key] )
                    elif dimname in ['ncol']:
                        1
                    elif dimname == 'time':
                        if not self.time_decoded:
                            for key in list( self.var_array[dimname].attrs.keys() ):
                                dimvar.setncattr( key, self.var_array[dimname].attrs[key] )
                        else:
                            dimvar.setncattr( 'units', self.tunits )
                            dimvar.setncattr( 'calendar', 'standard' )
                    else:
                        for key in list( self.var_array[dimname].attrs.keys() ):
                            dimvar.setncattr( key, self.var_array[dimname].attrs[key] )

                # additional dimension for info variables
                for afld in self.add_fields:
                    for adim in afld.dims:
                        if adim in self.dst_dim:
                            continue
                        else:
                            fid.createDimension( adim, len(afld[adim]) )                            

                # ===== Create Variables (fields) =====
                # Add additional fields for SE(-RR) model output
                if self.dst_type == 'SE':
                    var_tmp = fid.createVariable( 'lon', 'f8', ('ncol',) )
                    var_tmp[:] = xdst_grid.grid_center_lon.values
                    var_tmp.setncattr( 'long_name', 'longitude' )
                    var_tmp.setncattr( 'units', 'degrees_east' )

                    var_tmp = fid.createVariable( 'lat', 'f8', ('ncol',) )
                    var_tmp[:] = xdst_grid.grid_center_lat.values
                    var_tmp.setncattr( 'long_name', 'latitude' )
                    var_tmp.setncattr( 'units', 'degrees_north' )

                    if 'grid_area' in xdst_grid.data_vars:
                        var_tmp = fid.createVariable( 'area', 'f8', ('ncol',) )
                        var_tmp[:] = xdst_grid.grid_area.values
                        var_tmp.setncattr( 'long_name', 'area weights' )
                        var_tmp.setncattr( 'units', 'radians^2' )

                    if 'rrfac' in xdst_grid.data_vars:
                        var_tmp = fid.createVariable( 'rrfac', 'f8', ('ncol',) )
                        var_tmp[:] = xdst_grid.rrfac.values
                        var_tmp.setncattr( 'units', 'neXX/ne30' )
                    

                # Add regridded fields to NetCDF file
                if self.fields == []:
                    var_tmp = fid.createVariable( 'regridded_field', self.datatype, self.dst_dim )
                    var_tmp[:] = self.var_dst * self.scale_factor
                    if self.xarray_flag:
                        for key in list( self.var_array.attrs.keys() ):
                            if key in ['molecular_weight', 'molecular_weights']:
                                if self.mw == None:
                                    var_tmp.setncattr( key, self.var_array.attrs[key] )
                                else:
                                    var_tmp.setncattr( key, self.mw )
                            elif key in ['unit', 'units']:
                                if self.unit == None:
                                    var_tmp.setncattr( key, self.var_array.attrs[key] )
                                else:
                                    var_tmp.setncattr( key, self.unit )
                            else:
                                var_tmp.setncattr( key, self.var_array.attrs[key] )
                else:
                    for fld in self.fields:
                        var_tmp = fid.createVariable( fld, self.datatype, self.dst_dim )
                        var_tmp[:] = self.var_dst[fld] * self.scale_factor
                        if self.xarray_flag:
                            for key in list( self.var_array[fld].attrs.keys() ):
                                if key in ['molecular_weight', 'molecular_weights']:
                                    if self.mw == None:
                                        var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                                    else:
                                        var_tmp.setncattr( key, self.mw )
                                elif key in ['unit', 'units']:
                                    if self.unit == None:
                                        var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                                    else:
                                        var_tmp.setncattr( key, self.unit )
                                else:
                                    var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                # ===== END Create Variables (fields) =====

                # ===== Global attributes =====
                if (self.xarray_flag) & (self.fields != []) :
                    for key in list( self.var_array.attrs.keys() ):
                        fid.setncattr( key, self.var_array.attrs[key] )
                        
                fid.comment_regridding = '===== Below are created from regridding script ====='
                fid.regridded_by = 'Regridding_ESMF.py tool using ESMPy (ESMF)'
                fid.regridding_time = str( datetime.datetime.now() )
                fid.source_grid = self.src_grid_file
                fid.destination_grid = self.dst_grid_file
                user_name = subprocess.getoutput( 'echo "$USER"')
                host_name = subprocess.getoutput( 'hostname -f' )
                fid.regridding_username = user_name + ' on ' + host_name
                # ===== END Global attributes =====

                fid.close() # close file

                if self.check_timings:
                    self.Edate = datetime.datetime.now()
                    print( 'Saving NetCDF file end: ', self.Edate )
                    print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                                   time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
                    print( '========================================================================')


            # =================== END Save results to NetCDF file ===================
            # =======================================================================
        else:
            # =======================================================================
            # =============== Speed up: change order of calculation =================
            # =======================================================================
            # Open NetCDF files to write -> set dimensions -> regridding for each field
            # -> save each field -> release memory -> repeat -> close file
            
            if self.check_timings:
                self.SdateA = datetime.datetime.now()
                print( 'Saving NetCDF file / regridding start: ', self.SdateA )

            # load grid decsription files
            xdst_grid = xr.open_dataset( self.dst_grid_file )
            
            # Open NetCDF file for writing
            fid = Dataset( self.dst_file, 'w', format=self.nc_file_format )
            
            # ===== Create dimensions =====
            for di, dimname in enumerate(self.dst_dim):
                if dimname == 'time':
                    # unlimited time dimension
                    fid.createDimension( dimname )
                    self.construct_time_array()
                else:
                    fid.createDimension( dimname, self.dst_shape[di] )

                # write dimension variables
                dimvar = fid.createVariable( dimname, 'f8', (dimname,) )
                if dimname in ['lon','lat']:
                    dimvar[:] = np.copy( xdst_grid[dimname].values )
                elif dimname in ['ncol']:
                    dimvar[:] = np.copy( xdst_grid.grid_size.values )
                elif dimname  == 'time':
                    dimvar[:] = self.time_array
                else:
                    dimvar[:] = np.copy( self.var_array[dimname].values )

                # Add attributes for dimensions
                if dimname in ['lon','lat']:
                    for key in list( xdst_grid[dimname].attrs.keys() ):
                        dimvar.setncattr( key, xdst_grid[dimname].attrs[key] )
                elif dimname in ['ncol']:
                    1
                elif dimname == 'time':
                    if not self.time_decoded:
                        for key in list( self.var_array[dimname].attrs.keys() ):
                            dimvar.setncattr( key, self.var_array[dimname].attrs[key] )
                    else:
                        dimvar.setncattr( 'units', self.tunits )
                        dimvar.setncattr( 'calendar', 'standard' )
                else:
                    for key in list( self.var_array[dimname].attrs.keys() ):
                        dimvar.setncattr( key, self.var_array[dimname].attrs[key] )
                
            # additional dimension for info variables
            for afld in self.add_fields:
                for adim in afld.dims:
                    if adim in self.dst_dim:
                        continue
                    else:
                        fid.createDimension( adim, len(afld[adim]) )    
                            
            # ===== Create Variables (fields) =====
            # Add additional fields for SE(-RR) model output
            if self.dst_type == 'SE':
                var_tmp = fid.createVariable( 'lon', 'f8', ('ncol',) )
                var_tmp[:] = xdst_grid.grid_center_lon.values
                var_tmp.setncattr( 'long_name', 'longitude' )
                var_tmp.setncattr( 'units', 'degrees_east' )

                var_tmp = fid.createVariable( 'lat', 'f8', ('ncol',) )
                var_tmp[:] = xdst_grid.grid_center_lat.values
                var_tmp.setncattr( 'long_name', 'latitude' )
                var_tmp.setncattr( 'units', 'degrees_north' )

                if 'grid_area' in xdst_grid.data_vars:
                    var_tmp = fid.createVariable( 'area', 'f8', ('ncol',) )
                    var_tmp[:] = xdst_grid.grid_area.values
                    var_tmp.setncattr( 'long_name', 'area weights' )
                    var_tmp.setncattr( 'units', 'radians^2' )

                if 'rrfac' in xdst_grid.data_vars:
                    var_tmp = fid.createVariable( 'rrfac', 'f8', ('ncol',) )
                    var_tmp[:] = xdst_grid.rrfac.values
                    var_tmp.setncattr( 'units', 'neXX/ne30' )                  

            # Additional fields to be saved along with regridded fields
            if self.add_fields != []:
                for afld in self.add_fields:
                    var_tmp = fid.createVariable( afld.name, np.dtype( afld.values.flat[0] ).name,
                                                  afld.dims )
                    var_tmp[:] = afld.values[:]
                    for key in list( afld.attrs.keys() ):
                        var_tmp.setncattr( key, afld.attrs[key] )
                    
            # Add regridded fields to NetCDF file
            # =======================================================================
            # ============================= Regridding ==============================
            # ======================================================================= 
            if self.check_timings:
                self.Sdate = datetime.datetime.now()
                print( 'Regridding start: ', self.Sdate )

            if self.check_results:
                xsrc_grid = xr.open_dataset( self.src_grid_file )
                xdst_grid = xr.open_dataset( self.dst_grid_file )
                if self.src_type == 'FV':
                    src_dim_var = { 'lat':xsrc_grid['lat'].values,
                                    'lon':xsrc_grid['lon'].values }
                    src_FV_kwds = {'dimension':['lat','lon'],
                                   'dim_var':src_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }
                elif self.src_type == 'SE':
                    src_dim_var = { 'ncol':xsrc_grid.grid_size.values }
                    src_SE_kwds = {'scrip_file':self.src_grid_file,
                                   'dimension':['ncol'],
                                   'dim_var':src_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }                
                if self.dst_type == 'FV':
                    dst_dim_var = { 'lat':xdst_grid['lat'].values,
                                    'lon':xdst_grid['lon'].values }
                    dst_FV_kwds = {'dimension':['lat','lon'],
                                   'dim_var':dst_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }
                elif self.dst_type == 'SE':
                    dst_dim_var = { 'ncol':xdst_grid.grid_size.values }
                    dst_SE_kwds = {'scrip_file':self.dst_grid_file,
                                   'dimension':['ncol'],
                                   'dim_var':dst_dim_var,
                                   'unit':self.unit,
                                   'mw':self.mw,
                                   'print_results':False,
                                   'ignore_warning':True }

            self.N_loops = len( self.dst_dim_loop )
            if self.fields == []:
                # Regridding
                self.var_dst = np.zeros( self.dst_shape )
                if self.N_loops == 0:
                    if self.src_type == 'FV':
                        self.src_field.data[...] = np.swapaxes( self.var, 0, 1 )
                    elif self.src_type == 'SE':
                        self.src_field.data[...] = self.var
                    if self.dst_type == 'FV':
                        self.var_dst[:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                    elif self.dst_type == 'SE':
                        self.var_dst[:] = self.regrid( self.src_field, self.dst_field ).data
                    
                    if self.check_results:
                        if self.src_type == 'FV':
                            SRC_EMIS = Calc_Emis_T( self.var, **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS = Calc_Emis_T( self.var, **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS = Calc_Emis_T( self.var_dst, **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS = Calc_Emis_T( self.var_dst, **dst_SE_kwds )
                        print( 'Source total for the block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS.emissions_total) ) )
                        print( 'Destination total for the block [g]: ' + \
                                "{:.2e}".format(np.around(DST_EMIS.emissions_total) ) )
                        
                elif self.N_loops == 1:
                    for ii in np.arange( self.dst_shape_loop[0] ):
                        if self.src_type == 'FV':
                            self.src_field.data[...] = np.swapaxes( self.var[ii,:,:], 0, 1)
                        elif self.src_type == 'SE':
                            self.src_field.data[...] = self.var[ii,:]
                        if self.dst_type == 'FV':
                            self.var_dst[ii,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                        elif self.dst_type == 'SE':
                            self.var_dst[ii,:] = self.regrid( self.src_field, self.dst_field ).data
                        
                    if self.check_results:
                        if self.src_type == 'FV':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,:,:], **src_FV_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,:,:], **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,:], **src_SE_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,:], **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:,:], **dst_FV_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:,:], **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:], **dst_SE_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:], **dst_SE_kwds )
                        print( 'Source total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                        print( 'Destination total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                        print( 'Source total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                        print( 'Destination total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )
                        
                elif self.N_loops == 2:
                    for ii in np.arange( self.dst_shape_loop[0] ):
                        for jj in np.arange( self.dst_shape_loop[1] ):
                            if self.src_type == 'FV':
                                self.src_field.data[...] = np.swapaxes( self.var[ii,jj,:,:], 0, 1)
                            elif self.src_type == 'SE':
                                self.src_field.data[...] = self.var[ii,jj,:]
                            if self.dst_type == 'FV':
                                self.var_dst[ii,jj,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                            elif self.dst_type == 'SE':
                                self.var_dst[ii,jj,:] = self.regrid( self.src_field, self.dst_field ).data
                    
                    if self.check_results:
                        if self.src_type == 'FV':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,0,:,:], **src_FV_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,-1,:,:], **src_FV_kwds )
                        elif self.src_type == 'SE':
                            SRC_EMIS_S = Calc_Emis_T( self.var[0,0,:], **src_SE_kwds )
                            SRC_EMIS_E = Calc_Emis_T( self.var[-1,-1,:], **src_SE_kwds )
                        if self.dst_type == 'FV':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:,:], **dst_FV_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:,:], **dst_FV_kwds )
                        elif self.dst_type == 'SE':
                            DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:], **dst_SE_kwds )
                            DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:], **dst_SE_kwds )
                        print( 'Source total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                        print( 'Destination total for the first block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                        print( 'Source total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                        print( 'Destination total for the last block [g]: ' + \
                                "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )   
                else:
                    raise ValueError( 'Check number of dimensions in the destination field' )               
                
                # NetCDF
                var_tmp = fid.createVariable( 'regridded_field', self.datatype, self.dst_dim )
                var_tmp[:] = self.var_dst * self.scale_factor
                if self.xarray_flag:
                    for key in list( self.var_array.attrs.keys() ):
                        if key in ['molecular_weight', 'molecular_weights']:
                            if self.mw == None:
                                var_tmp.setncattr( key, self.var_array.attrs[key] )
                            else:
                                var_tmp.setncattr( key, self.mw )
                        elif key in ['unit', 'units']:
                            if self.unit == None:
                                var_tmp.setncattr( key, self.var_array.attrs[key] )
                            else:
                                var_tmp.setncattr( key, self.unit )
                        else:
                            var_tmp.setncattr( key, self.var_array.attrs[key] )
                del self.var_dst
            else:
                for fld in self.fields:
                    if self.check_results:
                        print( '========================================================================')
                        print( 'Fields: ', fld )
                        print( '------------------------------------------------------------------------')
                        
                    # Regridding
                    self.var_dst = np.zeros( self.dst_shape, dtype=self.datatype )
                    if self.N_loops == 0:
                        if self.src_type == 'FV':
                            self.src_field.data[...] = np.swapaxes( self.var[fld], 0, 1 )
                        elif self.src_type == 'SE':
                            self.src_field.data[...] = self.var[fld]
                        if self.dst_type == 'FV':
                            self.var_dst[:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                        elif self.dst_type == 'SE':
                            self.var_dst[:] = self.regrid( self.src_field, self.dst_field ).data
                        
                        if self.check_results:
                            if self.src_type == 'FV':
                                SRC_EMIS = Calc_Emis_T( self.var[fld], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS = Calc_Emis_T( self.var[fld], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS = Calc_Emis_T( self.var_dst, **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS = Calc_Emis_T( self.var_dst, **dst_SE_kwds )
                            print( 'Source total for the block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS.emissions_total) ) )
                            print( 'Destination total for the block [g]: ' + \
                                    "{:.2e}".format(np.around(DST_EMIS.emissions_total) ) )

                            
                    elif self.N_loops == 1:
                        for ii in np.arange( self.dst_shape_loop[0] ):
                            if self.src_type == 'FV':
                                self.src_field.data[...] = np.swapaxes( self.var[fld][ii,:,:], 0, 1)
                            elif self.src_type == 'SE':
                                self.src_field.data[...] = self.var[fld][ii,:]
                            if self.dst_type == 'FV':
                                self.var_dst[ii,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1 )
                            elif self.dst_type == 'SE':
                                self.var_dst[ii,:] = self.regrid( self.src_field, self.dst_field ).data
                            
                        if self.check_results:
                            if self.src_type == 'FV':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,:,:], **src_FV_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,:,:], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,:], **src_SE_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,:], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:,:], **dst_FV_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:,:], **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[0,:], **dst_SE_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,:], **dst_SE_kwds )
                            print( 'Source total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                            print( 'Destination total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                            print( 'Source total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                            print( 'Destination total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )  
                            
                    elif self.N_loops == 2:
                        for ii in np.arange( self.dst_shape_loop[0] ):
                            for jj in np.arange( self.dst_shape_loop[1] ):
                                if self.src_type == 'FV':
                                    self.src_field.data[...] = np.swapaxes( self.var[fld][ii,jj,:,:], 0, 1)
                                elif self.src_type == 'SE':
                                    self.src_field.data[...] = self.var[fld][ii,jj,:]
                                if self.dst_type == 'FV':
                                    self.var_dst[ii,jj,:] = np.swapaxes( self.regrid( self.src_field, self.dst_field ).data, 0, 1)
                                elif self.dst_type == 'SE':
                                    self.var_dst[ii,jj,:] = self.regrid( self.src_field, self.dst_field ).data
                                
                        if self.check_results:
                            if self.src_type == 'FV':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,0,:,:], **src_FV_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,-1,:,:], **src_FV_kwds )
                            elif self.src_type == 'SE':
                                SRC_EMIS_S = Calc_Emis_T( self.var[fld][0,0,:], **src_SE_kwds )
                                SRC_EMIS_E = Calc_Emis_T( self.var[fld][-1,-1,:], **src_SE_kwds )
                            if self.dst_type == 'FV':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:,:], **dst_FV_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:,:], **dst_FV_kwds )
                            elif self.dst_type == 'SE':
                                DST_EMIS_S = Calc_Emis_T( self.var_dst[0,0,:], **dst_SE_kwds )
                                DST_EMIS_E = Calc_Emis_T( self.var_dst[-1,-1,:], **dst_SE_kwds )
                            print( 'Source total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_S.emissions_total) ) )
                            print( 'Destination total for the first block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_S.emissions_total) ) )
                            print( 'Source total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(SRC_EMIS_E.emissions_total) ) )
                            print( 'Destination total for the last block [g]: ' + \
                                    "{:.2e}".format( np.around(DST_EMIS_E.emissions_total) ) )

                    else:
                        raise ValueError( 'Check number of dimensions in the destination field' )                
                    # NetCDF
                    var_tmp = fid.createVariable( fld, self.datatype, self.dst_dim )
                    var_tmp[:] = self.var_dst * self.scale_factor
                    if self.xarray_flag:
                        for key in list( self.var_array[fld].attrs.keys() ):
                            if key in ['molecular_weight', 'molecular_weights']:
                                if self.mw == None:
                                    var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                                else:
                                    var_tmp.setncattr( key, self.mw )
                            elif key in ['unit', 'units']:
                                if self.unit == None:
                                    var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                                else:
                                    var_tmp.setncattr( key, self.unit )
                            else:
                                var_tmp.setncattr( key, self.var_array[fld].attrs[key] )
                                
                    del self.var_dst
                    
            # ===== END Create Variables (fields) =====

            if self.check_timings:
                self.Edate = datetime.datetime.now()
                print( 'Regridding end: ', self.Edate )
                print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                               time.gmtime( (self.Edate - self.Sdate).seconds ) ) )
                print( '========================================================================')


            # ===== Global attributes =====
       
            if type(self.var_array) in [ xr.core.dataset.Dataset, dict ]:
                if type(self.var_array) in [ xr.core.dataarray.Dataset ]:
                    for key in list( self.var_array.attrs.keys() ):
                        fid.setncattr( key, self.var_array.attrs[key] )
                source_file_info = self.var_array[fld].encoding['source']
            
            fid.comment_regridding = '===== Below are created from regridding script ====='
            fid.regridded_by = 'Regridding_ESMF.py tool using ESMPy (ESMF)'
            fid.regridding_time = str( datetime.datetime.now() )     
            if type(self.var_array) in [ xr.core.dataset.Dataset, dict ]:
                fid.source_file = source_file_info
            fid.source_grid = self.src_grid_file
            fid.destination_grid = self.dst_grid_file
            user_name = subprocess.getoutput( 'echo "$USER"')
            host_name = subprocess.getoutput( 'hostname -f' )
            fid.regridding_username = user_name + ' on ' + host_name
                
            # ===== END Global attributes =====

            fid.close() # close file

            if self.check_timings:
                self.EdateA = datetime.datetime.now()
                print( 'Saving NetCDF file / regridding end: ', self.EdateA )
                print( time.strftime( "Time spent: %M minutes and %S seconds" , 
                               time.gmtime( (self.EdateA - self.SdateA).seconds ) ) )
                print( '========================================================================')
                
    # ===== Defining __call__ method =====
    def __call__(self):
        print( '=== filename ===')
        print( np.shape(self.filename) )


    # ===== Construct Time array ====
    def construct_time_array(self):

        self.tunits = 'days since 1950-01-01 00:00:00'
        
        # ===== Retrieve time info =====
        if self.xarray_flag:
            if not self.time_decoded:
                self.time_array = self.var_array['time'].values
                return
            else:
                if type( self.var_array['time'].values[0] ) == np.datetime64:
                    self.time_year = self.var_array['time'].values.astype('datetime64[Y]').astype('int') + 1970
                    self.time_month = self.var_array['time'].values.astype('datetime64[M]').astype('int') % 12 + 1
                    self.time_day = ( self.var_array['time'].values.astype('datetime64[D]') - \
                                      self.var_array['time'].values.astype('datetime64[M]') + 1 ).astype('int')

                elif type( self.var_array['time'].values[0] ) in [cftime._cftime.DatetimeGregorian, 
                                                               cftime._cftime.DatetimeNoLeap]:
                    self.time_year = np.zeros( len(self.var_array['time']) ).astype('int')
                    self.time_month = np.zeros( len(self.var_array['time']) ).astype('int')
                    self.time_day = np.zeros( len(self.var_array['time']) ).astype('int')

                    for ti, timeraw in enumerate( self.var_array['time'].values ):
                        self.time_year[ti] = timeraw.year
                        self.time_month[ti] = timeraw.month
                        self.time_day[ti] = timeraw.day

                else:
                    raise ValueError( 'Currently ' + str(type( self.var_array['time'].values[0] )) \
                                    + ' is not supported! Check type of the time dimension' )
        
        else:
            if type( self.var_array['time'][0] ) == np.datetime64:
                self.time_year = self.var_array['time'].astype('datetime64[Y]').astype('int') + 1970
                self.time_month = self.var_array['time'].astype('datetime64[M]').astype('int') % 12 + 1
                self.time_day = ( self.var_array['time'].astype('datetime64[D]') - \
                                  self.var_array['time'].astype('datetime64[M]') + 1 ).astype('int')

            elif type( self.var_array['time'][0] ) in [cftime._cftime.DatetimeGregorian, 
                                                           cftime._cftime.DatetimeNoLeap]:
                self.time_year = np.zeros( len(self.var_array['time']) ).astype('int')
                self.time_month = np.zeros( len(self.var_array['time']) ).astype('int')
                self.time_day = np.zeros( len(self.var_array['time']) ).astype('int')

                for ti, timeraw in enumerate( self.var_array['time'] ):
                    self.time_year[ti] = timeraw.year
                    self.time_month[ti] = timeraw.month
                    self.time_day[ti] = timeraw.day

            else:
                raise ValueError( 'Currently ' + str(type( self.var_array['time'].values[0] )) \
                                + ' is not supported! Check type of the time dimension' )
        # ===== END Retrieve time info =====
        
        
        # ===== Calculate time array for NetCDF file save =====
        # Reference day
        Syear, Smonth, Sday = self.tunits.split(' ')[2].split('-')
        Sdate = datetime.date( int(Syear), int(Smonth), int(Sday) )
        
        # Number of days in this case
        if self.xarray_flag:
            self.time_array = np.zeros( len(self.var_array['time'].values) ).astype('f8')
        else:
            self.time_array = np.zeros( len(self.var_array['time']) ).astype('f8')
        
        if self.xarray_flag:
            for ti, timeraw in enumerate( self.var_array['time'].values ):
                self.time_array[ti] = ( datetime.date( self.time_year[ti], self.time_month[ti], 
                                                       self.time_day[ti] ) - Sdate ).days
        else:
            for ti, timeraw in enumerate( self.var_array['time'] ):
                self.time_array[ti] = ( datetime.date( self.time_year[ti], self.time_month[ti], 
                                                       self.time_day[ti] ) - Sdate ).days
        
        
        if self.verbose:
            print( '== Total length of time: ', len(self.time_array) )
            print( '---- from: ', self.time_year[0], self.time_month[0], 
                                  self.time_day[0], self.time_array[0] )
            print( '----   to: ', self.time_year[-1], self.time_month[-1], 
                                  self.time_day[-1], self.time_array[-1] )
            
        # ===== END Calculate time array for NetCDF file save =====
