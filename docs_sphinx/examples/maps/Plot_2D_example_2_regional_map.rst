Plot a regional map from finite volume (FV) grid field (Plot_2D application)
============================================================================

.. code:: ipython3

    # By line: DSJ 10-MAR-2021
    # Script aims to:
    # - Plot a regional map with state lines
    # - Add grid lines to see the exact grids of the model

At the start of a Jupyter notebook you need to import all modules that you will use
-----------------------------------------------------------------------------------

.. code:: ipython3

    # Make sure you have downloaded "Plot_2D.py" script from Github
    from Plot_2D import Plot_2D
    import xarray as xr # To read NetCDF file

Read the sample file
--------------------

.. code:: ipython3

    # Make sure you have downloaded "sample.nc" file from Github
    ds = xr.open_dataset( 'sample.nc' )

Call Plot_2D script to plot surface CO over CONUS region
--------------------------------------------------------

.. code:: ipython3

    Plot_2D( ds['CO'][0,-1,:,:]*1e9, unit='ppbv', title='CO mixing ratio (SFC)',
             lon_range=[-130,-70], lat_range=[20,55])




.. parsed-literal::

    <Plot_2D.Plot_2D at 0x2235b2def88>




.. image:: Plot_2D_example_2_regional_map_files/Plot_2D_example_2_regional_map_7_1.png


Add state bounday lines
-----------------------

.. code:: ipython3

    Plot_2D( ds['CO'][0,-1,:,:]*1e9, unit='ppbv', title='CO mixing ratio (SFC)',
             lon_range=[-130,-70], lat_range=[20,55], state=True)




.. parsed-literal::

    <Plot_2D.Plot_2D at 0x2235bdcf488>




.. image:: Plot_2D_example_2_regional_map_files/Plot_2D_example_2_regional_map_9_1.png


Add grid lines
--------------

Sample file has a horizontal resolution of 0.9 x 1.25
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    Plot_2D( ds['CO'][0,-1,:,:]*1e9, unit='ppbv', title='CO mixing ratio (SFC)',
             lon_range=[-130,-70], lat_range=[20,55], state=True, grid_line=True, grid_line_lw=0.5 )




.. parsed-literal::

    <Plot_2D.Plot_2D at 0x2235ba70848>




.. image:: Plot_2D_example_2_regional_map_files/Plot_2D_example_2_regional_map_11_1.png

