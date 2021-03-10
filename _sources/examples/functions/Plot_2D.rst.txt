.. Python collection for CAM-chem documentation functions file, created by
   Duseong on Mon Mar 9, 2021.

====================
Plot_2D
====================

.. container::

   **Plot_2D** (self, var, lons=None, lats=None, lon_range=[-180,180], lat_range=[-90,90],
                scrip_file="", ax=None, cmap=None, projection=ccrs.PlateCarree(),
                grid_line=False, grid_line_lw=1, coast=True, country=True, state=False,
                resolution="10m", feature_line_lw=0.5, feature_color="black",
                lonlat_line=True, lon_interval=None, lat_interval=None,
                font_family="STIXGeneral", label_size=15, colorbar=True,
                log_scale=False, log_scale_min=None, diff=False, orientation="horizontal",
                shrink=0.8, pad=0.12, fraction=0.1, extend='both',
                colorticks=None, colorlabels=None, pretty_tick=True, nticks=None,
                cmax=None, cmin=None, title="", title_size=20, title_bold=False,
                unit="", unit_size=15, unit_bold=False, unit_italic=True, unit_offset=[0.0,0.0],
                verbose=False)

Plot 2D map. This function can be used for either finite volume grid or spectral element (+regional refinement) mesh. It can also be used for either global or regional plots. Both linear and log scale plots are supported as well. The jupyter notebook file with example applications is available `here <http://https://github.com/NCAR/CAM-chem/new/main/docs_sphinx/examples/functions/>`_


Parameters:
 - var (`xarray <http://xarray.pydata.org/en/stable/>`_ or any array) - A 2D (or 1D for spectral element) variable array to be plotted.
 - lons (1D array, optional) - Longitude values (1-D array) for plotting. Required for the non-xarray variable in the FV grid.
 - lats (1D array, optional) -  Latitude values (1-D array) for plotting. Required for the non-xarray variable in the FV grid.
 - lon_range (list, optional) - Used for regional plot. Ranges of longitudes to plot. e.g., [west longitude edge, east longitude edge].
 - lat_range (list, optional) - Used for regional plot. Ranges of latitudes to plot. e.g., [south latitude edge, north latitude edge].
 - scrip_file (str, optional) - A scrip filename for SE(-RR) mesh. Required for SE(-RR) plot.
 - ax (matplotlib.axes, optional) - Parent axes from which space for the plot will be drawn for advanced users. Using this keyword, Plot_2D function can be used in a more customized way. 
 - cmap (matplotlib colormap, optional) - Colormap from `matplotlib.cm <https://matplotlib.org/stable/api/cm_api.html>`_ or `user-defined colormap <https://github.com/NCAR/CAM-chem/blob/main/docs/jupyter_notebook_examples/maps/Custom_colorbar.md>`_. Default is cm.jet for normal plot and cm.bwr for difference plot.
 - projection (cartopy.crs, optional) - map projection method by `cartopy.crs <https://scitools.org.uk/cartopy/docs/latest/crs/projections.html>`_.
 - grid_line (bool, optional) - If True, the script will draw grid lines. Deafulat is False.
 - grid_line_lw (float, optional) - Line width for grid line when grid_line is True.
 - coast (bool, optional) - If True, the script will draw coastlines.
 - country (bool, optional) - If True, the script will draw country boundary lines.
 - state (bool, optional) - If True, the script will draw state/province lines.
 - resolution (str, optional) - Resolution of coast/country/state lines (10m, 50m, or 110m).
 - feature_line_lw (float, optional) - Line width for coast/country/state lines.
 - feature_color (str, optional) - Color for coast/country/state lines.
 - lonlat_line (bool, optional) - If True, the script will draw longitude & latitude lines.
 - lon_interval (float, optional) - Used for specifying longitude interval in degree. If not provided, It is automatically calculated to have 6-7 longitude lines in the plot. 
 - lat_interval (float, optional) - Used for specifying latitude interval in degree. If not provided, It is automatically calculated to have 6-7 latitude lines in the plot. 
 - font_family (str, optional) - Font family being used for the plot. Default is STIXGeneral (similar to Times New Roman).
 - label_size (integer, optional) - Label size of longitude and latitude values.
 - colorbar (bool, optional) - If True, the script will add a colorbar.
 - log_scale (bool, optional) - If True, the plot will be drawn on a log scale. If False, the plot will be drawn on a linear scale. Default is False.
 - log_scale_min (float, optional) - If provided, this value is used for the closest tick to zero. It is used for maximum tick value < 10^(-1). Ignored if both "cmin" and "cmax" are positive or if "colorticks" is specified.
 - diff (bool, optional) - If True, absolute values of cmin and cmax set to be the same.
 - orientation (str, optional) - Orientation of colorbar. Can be either "horizontal" or "vertical".
 - shrink (float, optional) - For colorbar adjustment. Fraction by which to multiply the size of the colorbar. 
 - pad (float, optional) - For colorbar adjustment. Fraction of original axis between colorbar and image axis. 
 - fraction (float, optional) - For colorbar adjustment. Fraction of original axis to use for colorbar.
 - extend (str, optional) - For colorbar adjustment. If not 'neither', make pointed ends for out-of-range values. Can be {'neither', 'both', 'min', 'max}. Default is 'both'.
 - colorticks (list, optional) - List of ticks being used for colorbar.
 - colorlabels (list, optional) - List of tick labels being used for colorbar.
 - pretty_tick (bool, optional) - If True, color ticks/labels are specially calculated inside of the code. Ignored if "colorticks" keyword is specified.
 - nticks (integer, optional) - Number of ticks in colorbar. Ignored if "colorticks" keyword is specified. 
 - cmax (float, optional) - Maximum value for the plot and colorbar. If not specified, the script will calculate the maximum value of the "var". 
 - cmin (float, optional) - Minimum value for the plot and colorbar. If not specified, the script will calculate the minimum value of the "var". 
 - title (str, optional) - If specified, the script will add a title to the plot. 
 - title_size (integer, optional) - Font size of the title. Default is 20. 
 - title_bold (bool, optional) - If True, set title font to bold. Default is False.
 - unit (str, optional) - If specified, the script will add a unit to the plot. 
 - unit_size (integer, optional) - Font size of the unit. Default is 15.
 - unit_bold (bool, optional) - If True, set the unit font to bold. 
 - unit_italic (bool, optional) - If True, set unit font to italic.
 - unit_offset (list, optional) - If provided, the script will make an adjustment to the unit position. [x-axis, y-axis]. 
 - verbose: Display detailed information on what is being done.

.. seealso::

   Example jupyter notebooks using the Plot_2D function:    


.. note::

   May not compatible with Python 2.7
