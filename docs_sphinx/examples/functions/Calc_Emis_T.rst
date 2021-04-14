.. Python collection for CAM-chem documentation functions file, created by
   Duseong on Mon Apr 5, 2021.

====================
Calc_Emis_T
====================

.. container::

      **Calc_Emis_T** (var, dimension=[], dim_var={}, unit='', mw=None, date_range=[], lon_range=[], lat_range=[], ndays=31, scrip_file="", print_results=True, ignore_warning=False, verbose=False)

Calculate the emission total of species. This function can be used for either finite volume grid or spectral element (+regional refinement) mesh. It can also be used for either global or regional emission total. 


Parameters:
 - var (`xarray <http://xarray.pydata.org/en/stable/>`_ or any array) - A 2D (or 1D for spectral element) emission array. Basically it should have longitude and latitude dimensions, but time and altitude dimensions are also supported. If time dimension is provided, the function will calculate timeseries. If altitude dimension is provided, the function will calculate vertically-integrated emission total. 
 - dimension (list, optional) - if var is not an xarray, the dimension must be specified. supported dimensions are time, altitude, lat, lon, and ncol (SE).
 - dim_var (dict, optional) - in case that var is not an xarray, dictionary with each dimension info must be provided. e.g., dim_var = {'time':datetime64[ns] array, 'lat':[-89.95,-89.85,...,89.85,89.95], 'lon':[-179.95,-179.85,...,179.85,179.95] }
 - unit (str, optional) - the unit of the provided emission array. e.g., unit = 'molecules/cm2/s', 'kg/m2/s'. No need to be provided if var is an xarray which has 'unit' attribute in it. 
 - mw (float, optional) - molecular weight of the specis in g/mol (e.g., 28 for CO). If provided, it overwrites mw of xarray attribute (if available)
 - date_range (list, optional) - 2-element list with date ranges to calculate emissions in a specific time window. e.g., ['2000-05-01', '2001-04-30']. 
 - lon_range (list, optional) - 2-element list with longitude ranges to calculate emissions in a specific longitude range. e.g., [100, 150]
 - lat_range (list, optional) - 2-element list with latitude ranges to calculate emissions in a specific latitude range. e.g., [20, 50]
 - ndays (int, optional) - number of days for emission arrays when a time dimension doesn't exist. i.e. to provide whether the emission is daily, monthly, or yearly, etc. 
 - scrip_file (str, optional) - a scrip filename for a spectral model mesh to provide grid area information.
 - print_results (bool, optional) - If True, display results after the calculation. 
 - ignore_warning (bool, optional) - If True, the function will not print warning messages. 
 - verbose (bool, optional) - If True, display detailed information on what is being done. 


.. seealso::

   Example jupyter notebooks using the Calc_Emis_T function will be available soon.


.. note::

   May not compatible with Python 2.7
