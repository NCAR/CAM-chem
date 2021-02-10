'''
map.py
this code is designed for 2d map plotting

MODIFICATION HISTORY:
    dsj, 15, MAY, 2015: VERSION 1.00
    dsj, 19, MAY, 2015: VERSION 1.10
                       - update settings for auto-colorbar
    dsj, 30, MAY, 2015: VERSOIN 1.20
                       - add several options
    dsj, 09, JUN, 2015: VERSION 1.30
                       - add overlay plot function
    dsj, 08, JUL, 2015: VERSION 1.40
                       - bug fix for maxorder value & add unitoffset
    dsj, 29, JUL, 2015: VERSION 1.50
                       - add options for grid interval
    dsj, 24, FEB, 2016: VERSION 1.80
                       - add pcolormesh option (use_pcolor)
    dsj, 24, MAR, 2016: VERSION 1.81
                       - add without colorbar option
    dsj, 25, MAR, 2016: VERSION 1.82
                       - add options in overlay function
    dsj, 25, MAR, 2016: VERSION 1.90
                       - modify pcolormesh option for representing model grid point
    dsj, 25, NOV, 2018: VERSION 1.91
                       - add colorbar label option for vertical colorbar
    dsj, 26, MAR, 2019: VERSION 1.92
                       - add fillcontinents keyword
    dsj, 27, MAR, 2019: VERSION 1.93
                       - add matrix operation keyword for the speed-up of overlay function
    dsj, 19, AUG, 2019: VERSION 1.94
                       - buf fix for using pcolormesh option: not displaying right and up edge maps
'''

import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pdb


class Tvmap(object):
    '''
    NAME:
           Tvmap

    PURPOSE:
           plotting 2D map image

    INPUTS:
           data -> 2-D array of values to be plotted as a color map
                   The first dimension is latitude, the second is longitude
           lons -> longitude values
           lats -> latitude values
           fill_lon_edge -> fill data values for lon=180.
                            It is needed only for the global plot case
           noparallel -> suppress latitude line
           nomeridian -> suppress longitude line
           loninterval -> interval for longitudes
           latinterval -> interval for latitudes
           nocoast -> suppress coastal line
           fillcontinents -> fill continents
           nogxlabel -> No longitude labels
           nogylabel -> No latitude labels
           ticksize -> longitude & latitude tick label size
           unit -> unit
           unitoffset -> adjust unit position
           maxdata -> maxdata for plotting
           mindata -> mindata for plotting
           nocbar -> draw map without colorbar
           colorlabels -> tick labels in colorbar
           colorticks -> tick points in colorbar
           use_pcolor -> turn off contourf and turn on pcolormesh
           ltext = text in left upper side of the figure
           rtext = text in right upper side of the figure
           diff = Flag for the difference map
           states = United States Boundaries
           around = around for colorbar max & min
           basemapkwds = keyword-value pair dictionary for basemap
           contourfkwds = keyword-value pair dictionary for contourf
           colorbarkwds = keyword-value pair dictionary for colorbar
    '''

    def __init__(self, data, lons=0, lats=0, fill_lon_edge=True,
                 noparallel=False,nomeridian=False,nocoast=False,
                 nocountries=False, fillcontinents=False,
                 loninterval=60, latinterval=30, 
                 nogylabel=False, nogxlabel=False, use_pcolor=False,
                 ticksize=12, unit='', unitsize=17, unitoffset=[0.,0.],
                 cbsize=0, division=21, Nticks=11, nocbar=False,
                 maxdata='None', mindata='None', colorlabels=0,
                 colorticks=0, ltext='', rtext='',
                 ltextsize=12, rtextsize=12, diff=False, 
                 states=False, around=True,
                 basemapkwds={}, contourfkwds={}, colorbarkwds={} ):

        self.imx = np.shape(data)[1]
        self.jmx = np.shape(data)[0]
        self.max = np.max(data)
        self.min = np.min(data)
        self.mean = np.mean(data)

        # Error check for data dimension
        if np.ndim(data) != 2:
            raise ValueError( 'data must be a 2-D array' )
        else:
            self.data = data

        # Construct lons & lats when lons & lats are not explicitly passed
        if np.ndim(lons) == 0:
            lons = np.linspace(-180,180,self.imx+1)[0:self.imx]
        if np.ndim(lats) == 0:
            lats = np.linspace(-90,90,self.jmx)

        # Error check for lons & lats
        # lons must have the same # of elements as the 1st dim of data
        if np.shape(data)[1] != np.shape(lons)[0]:
            raise ValueError( "'lons' is not compatible with 'data'!" )
        elif np.ndim(lons) != 1:
            raise ValueError( "'lons' must be a 1-D vector!" )
        else:
            self.lons = lons
            
        # lats must have the same # of elements as the 2st dim of data
        if np.shape(data)[0] != np.shape(lats)[0]:
            raise ValueError( "'lats' is not compatible with 'data'!" )
        elif np.ndim(lats) != 1:
            raise ValueError( "'lats' must be a 1-D vector!" )        
        else:
            self.lats = lats

        # Fill longitude edge
        if fill_lon_edge: self.lonedge()
        
        # Call Basemap
        basemapkwds['llcrnrlon'] = self.lons[0]
        basemapkwds['llcrnrlat'] = self.lats[0]
        basemapkwds['urcrnrlon'] = self.lons[-1]
        basemapkwds['urcrnrlat'] = self.lats[-1]


        m = Basemap(**basemapkwds)
        
        # longitude & latitude setting
        lon,lat = np.meshgrid( self.lons, self.lats )
        x, y = m(lon, lat)

        # Map settings
        if not nocoast: m.drawcoastlines()
        if not nocountries: m.drawcountries()
        if fillcontinents: m.fillcontinents()

        if nogylabel:
            gylabel = [0,0,0,0]
        else:
            gylabel = [1,0,0,0]

        if nogxlabel:
            gxlabel = [0,0,0,0]
        else:
            gxlabel = [0,0,0,1]

        if not noparallel: m.drawparallels(np.arange(-90.,91.,latinterval),
                                           labels=gylabel, size=ticksize,
                                           weight='semibold')
        if not nomeridian: m.drawmeridians(np.arange(-120.,181.,loninterval),
                                           labels=gxlabel, size=ticksize,
                                           weight='semibold')

        if states: m.drawstates()

        # Set max and min value of colorbar
        if self.max ==0:
            maxorder = 0
        else:
            maxorder = np.floor( np.log10(np.abs(self.max)) ).astype(int)
       
        if maxdata == 'None':
            if maxorder < 0:
                if around:
                   maxdata = np.around( self.max, decimals=-maxorder )
                else:
                   maxdata = self.max
            else:
                if around:
                   maxdata = np.around( self.max )
                else:
                   maxdata = self.max

        if mindata == 'None':
            if maxorder < 0:
                mindata = np.around( self.min, decimals=-maxorder )
            else:
                mindata = np.around( self.min )        

        if diff:
            if abs(maxdata) > abs(mindata):
                mindata = -maxdata
            elif abs(maxdata) < abs(mindata):
                maxdata = -mindata


        self.cmax = maxdata
        self.cmin = mindata

        
        # Contour settings
        if use_pcolor:      # pcolormesh
            contourfkwds['vmax'] = maxdata
            contourfkwds['vmin'] = mindata
        else:      # contourf
            if not 'levels' in contourfkwds:
                contourfkwds['levels'] = np.linspace(mindata,maxdata,division)
            if not 'extend' in contourfkwds:
                contourfkwds['extend'] = 'both'

        if use_pcolor:
#            x2,y2 = np.meshgrid( np.arange(np.min(self.lons),
#                                       np.max(self.lons)+lons[1]-lons[0],
#                                       lons[1]-lons[0]) - (lons[1]-lons[0])/2.,
#                                 np.arange(np.min(self.lats),
#                                       np.max(self.lats)+lats[1]-lats[0],
#                                       lats[1]-lats[0]) - (lats[1]-lats[0])/2. )

            dx_r4 = np.float16(self.lons[1]-self.lons[0])
            dy_r4 = np.float16(self.lats[1]-self.lats[0])

            tmplons = np.linspace(\
              np.float16(self.lons.min()), np.float16(self.lons.max())+dx_r4, \
              np.size(self.lons) + 1)- dx_r4/2.
            tmplats = np.linspace(\
              np.float16(self.lats.min()), np.float16(self.lats.max())+dy_r4, \
              np.size(self.lats) + 1)- dy_r4/2.

            x2,y2 = np.meshgrid(tmplons,tmplats)


            cf = m.pcolormesh( x2, y2, self.data, latlon=True, 
                               **contourfkwds )
            #cf.axis( [x2.min(),x2.max(),y2.min(),y2.max() ] )
            
        else:
            cf = m.contourf( x, y, self.data, **contourfkwds )            
 
        # Colorbar settings
        if cbsize == 0: cbsize = ticksize

        if not 'orientation' in colorbarkwds:
            colorbarkwds['orientation'] = 'horizontal'
        if not 'pad' in colorbarkwds:
            colorbarkwds['pad'] = 0.10
        if not 'extend' in colorbarkwds:
            colorbarkwds['extend'] = 'both'

        colorbarkwds['fraction'] = 0.05

        if np.ndim(colorlabels) == 0:
            if maxorder < 0:
                if around:
                   colorlabels = np.around( np.linspace(mindata,maxdata,Nticks),
                                            decimals=-maxorder )
                else:
                   colorlabels = np.linspace(mindata,maxdata,Nticks)
            else:
                if around:
                   colorlabels = np.around( np.linspace(mindata,maxdata,Nticks) )
                else:
                   colorlabels = np.linspace(mindata,maxdata,Nticks)



        if np.ndim(colorticks) == 0:
            if maxorder < 0:
                if around:
                   colorticks = np.around( np.linspace(mindata,maxdata,Nticks),
                                            decimals=-maxorder )
                else:
                   colorticks = np.linspace(mindata,maxdata,Nticks)
                                           

            else:
                if around:
                   colorticks = np.around( np.linspace(mindata,maxdata,Nticks) )
                else:
                   colorticks = np.linspace(mindata,maxdata,Nticks)


        if nocbar==True:
            print('without cbar')
            self.cf = cf
        else:
            pc = plt.colorbar(**colorbarkwds)
            # pc.set_label(unit,size=cbsize)
       
            pc.set_ticks(colorticks)
            if colorbarkwds['orientation'] == 'vertical':
                pc.ax.set_yticklabels( colorlabels,
                                       size=cbsize, style='italic', weight='semibold' )
            else:
                pc.ax.set_xticklabels( colorlabels,
                                       size=cbsize, style='italic', weight='semibold' )
            pc.update_ticks

            self.colorticks = colorticks
            self.colorlabels = colorlabels

            plt.text( 1.01+unitoffset[0], 1.0+unitoffset[1], unit,
                      ha='left', va='top',
                      weight='semibold', #style='italic',
                      transform=pc.ax.transAxes,
                      size=unitsize )

            # save colorbar properties
            if not use_pcolor:
                self.tcolors = cf.tcolors
            self.boundaries = pc.boundaries
        
        #texts
        plt.text( self.lons[0], self.lats[-1], ltext, ha='left', va='bottom',
                  weight='semibold', style='italic', fontsize=ltextsize )
        plt.text( self.lons[-1], self.lats[-1], rtext, ha='right', va='bottom',
                  weight='semibold', style='italic', fontsize=rtextsize )
        
        # Clear dictionaries
        contourfkwds.clear()
        colorbarkwds.clear()
        basemapkwds.clear()

    def lonedge(self):

        self.data = np.concatenate( ( self.data,
                                      np.swapaxes([self.data[:,-1]],0,1) ),
                                      axis=1 )
        self.lons = np.linspace(-180,180,self.imx+1)



    def overlay(self, Obsdata, Obslons, Obslats, plotkwds={}, setcolor=False,
                matrix_operation=False, colors=[]):

        if setcolor==True:
            if matrix_operation==True:
                plt.plot( Obslons, Obslats, color=colors[0], **plotkwds )

            else:
                for i in np.arange( len(Obsdata) ):
                    plt.plot( Obslons[i],Obslats[i],color=colors[i],
                              **plotkwds )
            


        else:
            cvalues = self.tcolors
            boundaries = self.boundaries
        
            Indices = []
            for d in Obsdata:
                Indices.append( np.max( np.where( d > boundaries ) ) )

            # Keyword settings
            if not 'marker' in plotkwds:
                plotkwds['marker'] = 'o'
            if not 'markersize' in plotkwds:
                plotkwds['markersize'] = 12

            for i, Ind in enumerate(Indices):
                plt.plot( Obslons[i],Obslats[i],color=cvalues[Ind][0][0:3],
                          **plotkwds )
            






'''
class Tvmap(object):
'''
'''
    NAME:
           Tvmap

    PURPOSE:
           plotting 2D map image

    INPUTS:
           data -> 2-D array of values to be plotted as a color map
                   The first dimension is latitude, the second is longitude
           lons -> longitude values
           lats -> latitude values
           fill_lon_edge -> fill data values for lon=180.
                            It is needed only for the global plot case
           noparallel -> suppress latitude line
           nomeridian -> suppress longitude line
           loninterval -> interval for longitudes
           latinterval -> interval for latitudes
           nocoast -> suppress coastal line
           fillcontinents -> fill continents
           nogxlabel -> No longitude labels
           nogylabel -> No latitude labels
           ticksize -> longitude & latitude tick label size
           unit -> unit
           unitoffset -> adjust unit position
           maxdata -> maxdata for plotting
           mindata -> mindata for plotting
           nocbar -> draw map without colorbar
           colorlabels -> tick labels in colorbar
           colorticks -> tick points in colorbar
           use_pcolor -> turn off contourf and turn on pcolormesh
           ltext = text in left upper side of the figure
           rtext = text in right upper side of the figure
           diff = Flag for the difference map
           states = United States Boundaries
           around = around for colorbar max & min
           basemapkwds = keyword-value pair dictionary for basemap
           contourfkwds = keyword-value pair dictionary for contourf
           colorbarkwds = keyword-value pair dictionary for colorbar
'''
'''
    def __init__(self, data, lons=0, lats=0, fill_lon_edge=True,
                 noparallel=False,nomeridian=False,nocoast=False,
                 nocountries=False, fillcontinents=False,
                 loninterval=60, latinterval=30, 
                 nogylabel=False, nogxlabel=False, use_pcolor=False,
                 ticksize=12, unit='', unitsize=17, unitoffset=[0.,0.],
                 cbsize=0, division=21, Nticks=11, nocbar=False,
                 maxdata='None', mindata='None', colorlabels=0,
                 colorticks=0, ltext='', rtext='',
                 ltextsize=12, rtextsize=12, diff=False, 
                 states=False, around=True,
                 basemapkwds={}, contourfkwds={}, colorbarkwds={} ):

        self.imx = np.shape(data)[1]
        self.jmx = np.shape(data)[0]
        self.max = np.max(data)
        self.min = np.min(data)
        self.mean = np.mean(data)

        # Error check for data dimension
        if np.ndim(data) != 2:
            raise ValueError( 'data must be a 2-D array' )
        else:
            self.data = data

        # Construct lons & lats when lons & lats are not explicitly passed
        if np.ndim(lons) == 0:
            lons = np.linspace(-180,180,self.imx+1)[0:self.imx]
        if np.ndim(lats) == 0:
            lats = np.linspace(-90,90,self.jmx)

        # Error check for lons & lats
        # lons must have the same # of elements as the 1st dim of data
        if np.shape(data)[1] != np.shape(lons)[0]:
            raise ValueError( "'lons' is not compatible with 'data'!" )
        elif np.ndim(lons) != 1:
            raise ValueError( "'lons' must be a 1-D vector!" )
        else:
            self.lons = lons
            
        # lats must have the same # of elements as the 2st dim of data
        if np.shape(data)[0] != np.shape(lats)[0]:
            raise ValueError( "'lats' is not compatible with 'data'!" )
        elif np.ndim(lats) != 1:
            raise ValueError( "'lats' must be a 1-D vector!" )        
        else:
            self.lats = lats

        # Fill longitude edge
        if fill_lon_edge: self.lonedge()
        
        # Call Basemap
        basemapkwds['llcrnrlon'] = self.lons[0]
        basemapkwds['llcrnrlat'] = self.lats[0]
        basemapkwds['urcrnrlon'] = self.lons[-1]
        basemapkwds['urcrnrlat'] = self.lats[-1]


        m = Basemap(**basemapkwds)
        
        # longitude & latitude setting
        lon,lat = np.meshgrid( self.lons, self.lats )
        x, y = m(lon, lat)

        # Map settings
        if not nocoast: m.drawcoastlines()
        if not nocountries: m.drawcountries()
        if fillcontinents: m.fillcontinents()

        if nogylabel:
            gylabel = [0,0,0,0]
        else:
            gylabel = [1,0,0,0]

        if nogxlabel:
            gxlabel = [0,0,0,0]
        else:
            gxlabel = [0,0,0,1]

        if not noparallel: m.drawparallels(np.arange(-90.,91.,latinterval),
                                           labels=gylabel, size=ticksize,
                                           weight='semibold')
        if not nomeridian: m.drawmeridians(np.arange(-120.,181.,loninterval),
                                           labels=gxlabel, size=ticksize,
                                           weight='semibold')

        if states: m.drawstates()

        # Set max and min value of colorbar
        if self.max ==0:
            maxorder = 0
        else:
            maxorder = np.floor( np.log10(np.abs(self.max)) ).astype(int)
       
        if maxdata == 'None':
            if maxorder < 0:
                if around:
                   maxdata = np.around( self.max, decimals=-maxorder )
                else:
                   maxdata = self.max
            else:
                if around:
                   maxdata = np.around( self.max )
                else:
                   maxdata = self.max

        if mindata == 'None':
            if maxorder < 0:
                mindata = np.around( self.min, decimals=-maxorder )
            else:
                mindata = np.around( self.min )        

        if diff:
            if abs(maxdata) > abs(mindata):
                mindata = -maxdata
            elif abs(maxdata) < abs(mindata):
                maxdata = -mindata


        self.cmax = maxdata
        self.cmin = mindata

        
        # Contour settings
        if use_pcolor:      # pcolormesh
            contourfkwds['vmax'] = maxdata
            contourfkwds['vmin'] = mindata
        else:      # contourf
            if not 'levels' in contourfkwds:
                contourfkwds['levels'] = np.linspace(mindata,maxdata,division)
            if not 'extend' in contourfkwds:
                contourfkwds['extend'] = 'both'

        if use_pcolor:
            x2,y2 = np.meshgrid( np.arange(np.min(self.lons),
                                       np.max(self.lons)+lons[1]-lons[0],
                                       lons[1]-lons[0]) - (lons[1]-lons[0])/2.,
                                 np.arange(np.min(self.lats),
                                       np.max(self.lats)+lats[1]-lats[0],
                                       lats[1]-lats[0]) - (lats[1]-lats[0])/2. )

            cf = m.pcolormesh( x2, y2, self.data, latlon=True, 
                               **contourfkwds )
            #cf.axis( [x2.min(),x2.max(),y2.min(),y2.max() ] )
            
        else:
            cf = m.contourf( x, y, self.data, **contourfkwds )            
 
        # Colorbar settings
        if cbsize == 0: cbsize = ticksize

        if not 'orientation' in colorbarkwds:
            colorbarkwds['orientation'] = 'horizontal'
        if not 'pad' in colorbarkwds:
            colorbarkwds['pad'] = 0.10
        if not 'extend' in colorbarkwds:
            colorbarkwds['extend'] = 'both'

        colorbarkwds['fraction'] = 0.05

        if np.ndim(colorlabels) == 0:
            if maxorder < 0:
                if around:
                   colorlabels = np.around( np.linspace(mindata,maxdata,Nticks),
                                            decimals=-maxorder )
                else:
                   colorlabels = np.linspace(mindata,maxdata,Nticks)
            else:
                if around:
                   colorlabels = np.around( np.linspace(mindata,maxdata,Nticks) )
                else:
                   colorlabels = np.linspace(mindata,maxdata,Nticks)



        if np.ndim(colorticks) == 0:
            if maxorder < 0:
                if around:
                   colorticks = np.around( np.linspace(mindata,maxdata,Nticks),
                                            decimals=-maxorder )
                else:
                   colorticks = np.linspace(mindata,maxdata,Nticks)
                                           

            else:
                if around:
                   colorticks = np.around( np.linspace(mindata,maxdata,Nticks) )
                else:
                   colorticks = np.linspace(mindata,maxdata,Nticks)


        if nocbar==True:
            print 'without cbar'
            self.cf = cf
        else:
            pc = plt.colorbar(**colorbarkwds)
            # pc.set_label(unit,size=cbsize)
       
            pc.set_ticks(colorticks)
            if colorbarkwds['orientation'] == 'vertical':
                pc.ax.set_yticklabels( colorlabels,
                                       size=cbsize, style='italic', weight='semibold' )
            else:
                pc.ax.set_xticklabels( colorlabels,
                                       size=cbsize, style='italic', weight='semibold' )
            pc.update_ticks

            self.colorticks = colorticks
            self.colorlabels = colorlabels

            plt.text( 1.01+unitoffset[0], 1.0+unitoffset[1], unit,
                      ha='left', va='top',
                      weight='semibold', #style='italic',
                      transform=pc.ax.transAxes,
                      size=unitsize )

            # save colorbar properties
            if not use_pcolor:
                self.tcolors = cf.tcolors
            self.boundaries = pc.boundaries
        
        #texts
        plt.text( self.lons[0], self.lats[-1], ltext, ha='left', va='bottom',
                  weight='semibold', style='italic', fontsize=ltextsize )
        plt.text( self.lons[-1], self.lats[-1], rtext, ha='right', va='bottom',
                  weight='semibold', style='italic', fontsize=rtextsize )
        
        # Clear dictionaries
        contourfkwds.clear()
        colorbarkwds.clear()
        basemapkwds.clear()

    def lonedge(self):

        self.data = np.concatenate( ( self.data,
                                      np.swapaxes([self.data[:,-1]],0,1) ),
                                      axis=1 )
        self.lons = np.linspace(-180,180,self.imx+1)



    def overlay(self, Obsdata, Obslons, Obslats, plotkwds={}, setcolor=False,
                matrix_operation=False, colors=[]):

        if setcolor==True:
            if matrix_operation==True:
                plt.plot( Obslons, Obslats, color=colors[0], **plotkwds )

            else:
                for i in np.arange( len(Obsdata) ):
                    plt.plot( Obslons[i],Obslats[i],color=colors[i],
                              **plotkwds )
            


        else:
            cvalues = self.tcolors
            boundaries = self.boundaries
        
            Indices = []
            for d in Obsdata:
                Indices.append( np.max( np.where( d > boundaries ) ) )

            # Keyword settings
            if not 'marker' in plotkwds:
                plotkwds['marker'] = 'o'
            if not 'markersize' in plotkwds:
                plotkwds['markersize'] = 12

            for i, Ind in enumerate(Indices):
                plt.plot( Obslons[i],Obslats[i],color=cvalues[Ind][0][0:3],
                          **plotkwds )
            
'''
