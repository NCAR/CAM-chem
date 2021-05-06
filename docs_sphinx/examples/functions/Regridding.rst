.. Python collection for CAM-chem documentation functions file, created by
   Duseong on Fri Apr 23, 2021.

====================
Regridding
====================

.. container::

   **Regridding** (self, var_array, fields=[], add_fields=[], dimension=[], dim_var={}, src_grid_file=None, dst_grid_file=None, wgt_file=None, save_wgt_file=False, save_wgt_file_only=False, method="Conserve", save_results=True, speed_up=True, datatype='f4', nc_file_format='NETCDF3_64BIT_DATA', dst_file=None, creation_date=True, check_results=False, mw=None, unit=None, check_timings=True, ignore_warning=False, verbose=False)

Regrid fields (e.g., emission, meteorological data, model output, etc.) between finite volume grid and spectral element mesh. This program relies on `ESMPy <https://earthsystemmodeling.org/esmpy/>`_ tool. There are several `regridding methods <https://earthsystemmodeling.org/regrid/#regridding-methods>`_ If you use earlier ESMPy version (<8.1.0), only conservative regridding methods are supported due to some errors in calling ESMPy functions on Cheyenne and Casper machines, but it might work on other machines. The function will be available as a PIP package soon with jupyter notebook examples. 


Parameters:
 - var_array (`xarray <http://xarray.pydata.org/en/stable/>`_ or any array) - A 2D (or 1D for spectral element) array. Basically it should have longitude and latitude dimensions, and up to 2 more dimensions are supported (e.g., time and altitude dimensions).
 - fields (list, optional) - a list that has field names in var_array (for the case of using xarray). If a xarray has multiple fields, only specified fields provided in this keyword will be processed. 
 - add_fields (list, optional) - for additional fields that are not needed to be regridded, but if a user wants to save additional fields in addition to regridded fields. 
 - dimension (list, optional) - If var_array is not an xarray, dimension must be provided for var_array. e.g., dimension = ['time','lat','lon']; ['any','any2','lat','lon']; ['any','ncol']
 - dim_var (dictionary, optional) - If var_array is not an xarray, dim_var must be provided for dimension variables. e.g.,  dim_var = {'time':datetime64[ns] array, 'lat':[-89.95,-89.85,...,89.85,89.95], 'lon':[-179.95,-179.85,...,179.85,179.95] }
 - src_grid_file (str) - grid/mesh filename for source field. 
 - dst_grid_file (str) - grid/mesh filename for destination field. 
 - wgt_file (str) - weight filename. use the existing weight file (save_weight_file=False) or create new weight file (save_weight_file=True)
 - save_wgt_file (bool) - If true, create new weight file
 - save_wgt_file_only (bool) - if true, save wegith file only (not regridding)
 - no_wgt_file (bool) - if true, the script will not create weight file (useful for one-time regridding)
 - creation_date (bool) - If true, add the creation date to the end of the filename
 - method (str) - regridding method: "Bilinear", High-order patch recovery ("Patch"), Nearest source to destination ("Nearest_StoD"), Nearest destination to source ("Nearest_DtoS"), First-order conservative ("Conserve"), Second-order conservative ("Conserve_2nd"). More information are available at: https://earthsystemmodeling.org/regrid/#regridding-methods. 
 - save_results (bool, optional) - If True, save the regridded fields to the NetCDF file.
 - datatype (str) - Can be 'f8' (double) or 'f4' (float). Datatypes of dimension and basic information variables are fixed to f8. 
 - nc_file_format (str) - NetCDF file formmat to be used in NetCDF4 library. Default is NETCDF3_64BIT_DATA for compatability with CESM. 
 - speed_up (bool, optional) - If true, speed up regridding, but it doesn't return the results to python shell. Good for very large dataset and saving NetCDF file in terms of speed and memory. 
 - dst_file (str, optional) - NetCDF filename for resulting regridded fields
 - check_results (bool, optional) - If true, calculate the total of source and destination field. It can be useful especially for emission processing.
 - mw (float, optional) - In case check_results=True. To calculate emission total
 - unit (str, optional) - In case check_results=True. To calculate emission total.
 - check_timings (bool, optional) - If true, measure time spent for regridding
 - ignore_warning (bool, optional) - If true, ignore warning messages. 
 - verbose (bool, optional) - If true, display detailed information on what is being done.

.. seealso::

   Example jupyter notebooks using the Regridding function will be available soon. 

.. note::

   May not compatible with Python 2.7

