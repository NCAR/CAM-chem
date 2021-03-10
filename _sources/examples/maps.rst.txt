.. Python collection for CAM-chem documentation maps file, created by
   rrb on Mon Feb 15, 2021.

=======
Maps
=======

This section describes some ways to plot model output on maps.

.. |map_img| image:: maps/plot_map_basic_files/plot_map_basic_5_0.png
   :width: 200px
.. |map_co| image:: maps/plot_map_basic_co_files/plot_map_basic_co_9_0.png
   :width: 200px
.. |map_co_cbar| image:: maps/plot_map_basic_co_cbar_files/plot_map_basic_co_cbar_9_0.png
   :width: 200px

  
.. list-table::
   :widths: 20 20 20 20
   :header-rows: 0

   * - | `map outlines <maps/plot_map_basic.html>`_
       | |map_img|
     - | alternate projection
       |
     - | `model output as contours <maps/plot_map_basic_co.html>`_
       | |map_co|
     - | `define contour levels <maps/plot_map_basic_co_cbar.html>`_
       | |map_co_cbar|
   * - | remove while stripe at dateline
       |
     - | zoom into region
       |
     - | add location points
       |
     - | add observation values at points
       |
   * - | convert to column values
       |
     - | gridded satellite data
       |
     - | difference plot
       |
     - | using the basemap library/package
       |

.. toctree::
   :hidden:
   :maxdepth: 1

   Map outline <maps/plot_map_basic>
   Plot Tracer <maps/plot_map_basic_co>
   Adjust contours <maps/plot_map_basic_co_cbar>


------------

Examples using the `Plot_2D function <functions/Plot_2D.html>`_

.. |Plot_2D_ex1| image:: maps/Plot_2D_example_1_global_map_files/Plot_2D_example_1_global_map_15_1.png
   :width: 200px
.. |Plot_2D_ex2| image:: maps/Plot_2D_example_2_regional_map_files/Plot_2D_example_2_regional_map_9_1.png
   :width: 200px
.. |Plot_2D_ex3| image:: maps/Plot_2D_example_3_SE_RR_map_files/Plot_2D_example_3_SE_RR_map_15_1.png
   :width: 200px
   
.. list-table::
   :widths: 20 20 20 20
   :header-rows: 0

   * - | `Global map [FV grid] <maps/Plot_2D_example_1_global_map.html>`_
       | |Plot_2D_ex1|
     - | `Regional map [FV grid] <maps/Plot_2D_example_2_regional_map.html>`_
       | |Plot_2D_ex2|
     - | `Global/Regional map [SE(-RR) grid] <maps/Plot_2D_example_3_SE_RR_map.html>`_
       | |Plot_2D_ex3|
     - | Log scale map
       |
   * - | Adding a marker on a map
       |
     - | Multi-panel with PLot_2D
       |
     - | TBD
       |
     - | TBD
       |


.. toctree::
   :hidden:
   :maxdepth: 1

   Plot2D: Global FV <maps/Plot_2D_example_1_global_map>
   Plot2D: Regional FV <maps/Plot_2D_example_2_regional_map>
   Plot2D: Regional SE <maps/Plot_2D_example_3_SE_RR_map>


