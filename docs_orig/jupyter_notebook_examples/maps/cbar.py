'''
cbar.py
read colorbar file from NCL
and make cmap for python

MODIFICATION HISTORY:
    dsj, 16, MAY, 2015: VERSION 1.00
'''
import numpy as np
import matplotlib.colors as matcl
import os

class Cbar(object):
    '''
    NAME:
           Cbar

    PURPOSE:
           Read and Make Colormap for python

    INPUTS:
           Colormap name
    '''

    def __init__(self, Cname='', addwhite0=False, addwhitem=False):
        self.name = Cname

        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        
        CBT = np.genfromtxt( dir_path + '/cbar/' + self.name + '.rgb' ) / 255.
        CBT2 = list(map( matcl.rgb2hex, CBT ))
        self.cmap = matcl.ListedColormap(CBT2, self.name )



