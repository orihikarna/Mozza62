import pcbnew
import copy
import math
import sys
import os
import re
from enum import Enum

##
# sys.dont_write_bytecode = True
# root_dir = os.path.join( os.path.expanduser( '~' ), 'repos/Mozza62/python' )
# if not root_dir in sys.path:
#     sys.path.append( root_dir )
##
import kad
import pnt
import vec2
import mat2

import importlib

importlib.reload( kad )
importlib.reload( pnt )
importlib.reload( vec2 )
importlib.reload( mat2 )

kad.UnitMM = True
kad.PointDigits = 3

pcb = pcbnew.GetBoard()

# alias
Strt  = kad.Straight # Straight
Dird  = kad.Directed # Directed + Offsets
ZgZg  = kad.ZigZag # ZigZag

Line        = kad.Line
Linear      = kad.Linear
Round       = kad.Round
BezierRound = kad.BezierRound
Spline      = kad.Spline
##

# in mm
VIA_Size = [(1.1, 0.6), (1.0, 0.5), (0.8, 0.4)]#, (0.7, 0.3)]

PCB_Width  = 170
PCB_Height = 155

U1_x, U1_y = 82, 95
J1_x, J1_y, J1_angle = 18, 98, 0
J2_x, J2_y, J2_angle = 130, 100, 0
J3_x, J3_y, J3_angle = 85, 118, 10
D1_x, D1_y = 62, 106

keys = {
    '11' : [91.937, -43.058, 16.910, 15.480, -21.2], # r
    '13' : [89.129, -60.205, 17.000, 17.000, -21.2], # |
    '14' : [85.528, -77.044, 17.000, 17.000, -21.2], # E
    '15' : [64.347, -125.667, 22.000, 17.000, -244.0], # R
    '21' : [112.294, -37.720, 17.000, 17.000, -6.0], # &
    '22' : [108.740, -54.440, 17.000, 17.000, -6.0], # Y
    '23' : [105.186, -71.160, 17.000, 17.000, -6.0], # H
    '24' : [101.632, -87.880, 17.000, 17.000, -6.0], # N
    '25' : [83.140, -120.626, 22.000, 17.000, -256.0], # S
    '31' : [129.201, -39.497, 17.000, 17.000, -6.0], # '
    '32' : [125.647, -56.217, 17.000, 17.000, -6.0], # U
    '33' : [122.093, -72.937, 17.000, 17.000, -6.0], # J
    '34' : [118.539, -89.657, 17.000, 17.000, -6.0], # M
    '35' : [102.571, -119.602, 22.000, 17.000, -268.0], # S
    '41' : [149.855, -44.443, 17.000, 17.000, -24.0], # (
    '42' : [145.678, -61.192, 17.000, 17.000, -24.0], # I
    '43' : [141.502, -77.942, 17.000, 17.000, -24.0], # K
    '44' : [137.326, -94.691, 17.000, 17.000, -24.0], # <
    '51' : [167.274, -52.219, 17.000, 17.000, -26.0], # )
    '52' : [162.516, -68.813, 17.000, 17.000, -26.0], # O
    '53' : [157.758, -85.406, 17.000, 17.000, -26.0], # L
    '54' : [153.000, -102.000, 17.000, 17.000, -26.0], # >
    '61' : [182.380, -65.072, 17.000, 17.000, -8.0], #  
    '62' : [177.665, -81.576, 17.000, 17.000, -8.0], # P
    '63' : [172.950, -98.081, 17.000, 17.000, -8.0], # +
    '64' : [167.402, -119.156, 22.800, 17.000, -22.0], # ?
    '65' : [133.134, -125.721, 13.700, 12.700, -6.0 + 180], # R
    '71' : [198.220, -74.508, 17.000, 17.000, -8.0], # =
    '72' : [193.506, -91.013, 17.000, 17.000, -8.0], # `
    '73' : [188.791, -107.517, 17.000, 17.000, -8.0], # *
    '82' : [209.347, -100.449, 17.000, 17.000, -8.0], # [
    '83' : [204.632, -116.954, 17.000, 17.000, -8.0], # ]
    '84' : [188.971, -130.907, 26.000, 17.000, -22.0], # _
}
EdgeCuts = [
  [55.141, 136.958], [56.201, 137.981], [57.297, 138.966], [58.427, 139.912], 
  [59.589, 140.818], [60.783, 141.683], [62.006, 142.506], [63.256, 143.287], 
  [64.533, 144.024], [65.834, 144.717], [67.159, 145.364], [68.505, 145.965], 
  [69.871, 146.519], [71.255, 147.025], [72.656, 147.481], [74.072, 147.888], 
  [74.072, 147.888], [75.502, 148.245], [76.945, 148.554], [78.403, 148.819], 
  [79.875, 149.043], [81.360, 149.230], [82.860, 149.383], [84.375, 149.506], 
  [85.904, 149.601], [87.448, 149.673], [89.007, 149.724], [90.581, 149.759], 
  [92.170, 149.780], [93.774, 149.791], [95.394, 149.794], [97.029, 149.795], 
  [97.029, 149.795], [98.680, 149.795], [100.345, 149.795], [102.021, 149.795], 
  [103.706, 149.795], [105.399, 149.795], [107.097, 149.795], [108.799, 149.795], 
  [110.501, 149.795], [112.203, 149.795], [113.901, 149.795], [115.594, 149.795], 
  [117.279, 149.795], [118.955, 149.795], [120.620, 149.795], [122.271, 149.795], 
  [122.271, 149.795], [123.907, 149.795], [125.529, 149.795], [127.139, 149.795], 
  [128.740, 149.795], [130.334, 149.795], [131.923, 149.795], [133.508, 149.795], 
  [135.092, 149.795], [136.677, 149.795], [138.266, 149.795], [139.860, 149.795], 
  [141.461, 149.795], [143.071, 149.795], [144.693, 149.795], [146.329, 149.795], 
  [146.329, 149.795], [147.980, 149.795], [149.645, 149.795], [151.321, 149.795], 
  [153.006, 149.795], [154.699, 149.795], [156.397, 149.795], [158.099, 149.795], 
  [159.801, 149.795], [161.503, 149.795], [163.201, 149.795], [164.894, 149.795], 
  [166.579, 149.795], [168.255, 149.795], [169.920, 149.795], [171.571, 149.795], 
  [171.571, 149.795], [173.206, 149.794], [174.826, 149.791], [176.430, 149.780], 
  [178.019, 149.759], [179.593, 149.724], [181.152, 149.673], [182.696, 149.601], 
  [184.225, 149.506], [185.740, 149.383], [187.240, 149.230], [188.725, 149.043], 
  [190.197, 148.819], [191.655, 148.554], [193.098, 148.245], [194.528, 147.888], 
  [194.528, 147.888], [195.944, 147.481], [197.345, 147.025], [198.729, 146.519], 
  [200.095, 145.965], [201.441, 145.364], [202.766, 144.717], [204.067, 144.024], 
  [205.344, 143.287], [206.594, 142.506], [207.817, 141.683], [209.011, 140.818], 
  [210.173, 139.912], [211.303, 138.966], [212.399, 137.981], [213.459, 136.958], 
  [213.459, 136.958], [214.482, 135.898], [215.467, 134.802], [216.413, 133.672], 
  [217.319, 132.510], [218.184, 131.317], [219.008, 130.095], [219.788, 128.844], 
  [220.525, 127.568], [221.218, 126.267], [221.865, 124.942], [222.466, 123.597], 
  [223.019, 122.231], [223.525, 120.847], [223.981, 119.446], [224.388, 118.030], 
  [224.388, 118.030], [224.743, 116.600], [225.048, 115.158], [225.302, 113.706], 
  [225.504, 112.245], [225.656, 110.777], [225.755, 109.302], [225.803, 107.824], 
  [225.800, 106.343], [225.744, 104.862], [225.636, 103.381], [225.477, 101.902], 
  [225.265, 100.427], [225.000, 98.958], [224.683, 97.496], [224.314, 96.042], 
  [224.314, 96.042], [223.892, 94.598], [223.420, 93.164], [222.903, 91.738], 
  [222.343, 90.319], [221.744, 88.907], [221.109, 87.501], [220.441, 86.099], 
  [219.745, 84.702], [219.022, 83.307], [218.278, 81.915], [217.514, 80.523], 
  [216.735, 79.132], [215.944, 77.740], [215.144, 76.347], [214.339, 74.951], 
  [214.339, 74.951], [213.531, 73.551], [212.721, 72.149], [211.910, 70.744], 
  [211.097, 69.336], [210.282, 67.925], [209.467, 66.512], [208.650, 65.097], 
  [207.832, 63.680], [207.013, 62.262], [206.193, 60.842], [205.373, 59.421], 
  [204.552, 58.000], [203.731, 56.577], [202.909, 55.154], [202.087, 53.731], 
  [202.087, 53.731], [201.266, 52.309], [200.442, 50.889], [199.614, 49.476], 
  [198.781, 48.072], [197.941, 46.681], [197.092, 45.306], [196.231, 43.950], 
  [195.358, 42.616], [194.471, 41.307], [193.567, 40.027], [192.644, 38.778], 
  [191.702, 37.564], [190.737, 36.388], [189.749, 35.253], [188.735, 34.163], 
  [188.735, 34.163], [187.695, 33.119], [186.626, 32.123], [185.531, 31.174], 
  [184.408, 30.273], [183.258, 29.419], [182.080, 28.612], [180.875, 27.853], 
  [179.642, 27.142], [178.382, 26.478], [177.095, 25.861], [175.780, 25.292], 
  [174.438, 24.770], [173.069, 24.295], [171.672, 23.868], [170.248, 23.489], 
  [170.248, 23.489], [168.797, 23.156], [167.320, 22.868], [165.819, 22.621], 
  [164.297, 22.411], [162.754, 22.237], [161.193, 22.094], [159.616, 21.980], 
  [158.024, 21.891], [156.419, 21.824], [154.804, 21.776], [153.179, 21.744], 
  [151.547, 21.724], [149.909, 21.714], [148.268, 21.710], [146.625, 21.710], 
  [146.625, 21.710], [144.982, 21.710], [143.338, 21.710], [141.695, 21.710], 
  [140.052, 21.710], [138.408, 21.710], [136.765, 21.710], [135.122, 21.710], 
  [133.478, 21.710], [131.835, 21.710], [130.192, 21.710], [128.548, 21.710], 
  [126.905, 21.710], [125.262, 21.710], [123.618, 21.710], [121.975, 21.710], 
  [121.975, 21.710], [120.332, 21.710], [118.691, 21.714], [117.053, 21.724], 
  [115.421, 21.744], [113.796, 21.776], [112.181, 21.824], [110.576, 21.891], 
  [108.984, 21.980], [107.407, 22.094], [105.846, 22.237], [104.303, 22.411], 
  [102.781, 22.621], [101.280, 22.868], [99.803, 23.156], [98.352, 23.489], 
  [98.352, 23.489], [96.928, 23.868], [95.531, 24.295], [94.162, 24.770], 
  [92.820, 25.292], [91.505, 25.861], [90.218, 26.478], [88.958, 27.142], 
  [87.725, 27.853], [86.520, 28.612], [85.342, 29.419], [84.192, 30.273], 
  [83.069, 31.174], [81.974, 32.123], [80.905, 33.119], [79.865, 34.163], 
  [79.865, 34.163], [78.851, 35.253], [77.863, 36.388], [76.898, 37.564], 
  [75.956, 38.778], [75.033, 40.027], [74.129, 41.307], [73.242, 42.616], 
  [72.369, 43.950], [71.508, 45.306], [70.659, 46.681], [69.819, 48.072], 
  [68.986, 49.476], [68.158, 50.889], [67.334, 52.309], [66.512, 53.731], 
  [66.512, 53.731], [65.691, 55.154], [64.869, 56.577], [64.048, 58.000], 
  [63.227, 59.421], [62.407, 60.842], [61.587, 62.262], [60.768, 63.680], 
  [59.950, 65.097], [59.133, 66.512], [58.318, 67.925], [57.503, 69.336], 
  [56.690, 70.744], [55.879, 72.149], [55.069, 73.551], [54.261, 74.951], 
  [54.261, 74.951], [53.456, 76.347], [52.656, 77.740], [51.865, 79.132], 
  [51.086, 80.523], [50.322, 81.915], [49.578, 83.307], [48.855, 84.702], 
  [48.159, 86.099], [47.491, 87.501], [46.856, 88.907], [46.257, 90.319], 
  [45.697, 91.738], [45.180, 93.164], [44.708, 94.598], [44.286, 96.042], 
  [44.286, 96.042], [43.917, 97.496], [43.600, 98.958], [43.335, 100.427], 
  [43.123, 101.902], [42.964, 103.381], [42.856, 104.862], [42.800, 106.343], 
  [42.797, 107.824], [42.845, 109.302], [42.944, 110.777], [43.096, 112.245], 
  [43.298, 113.706], [43.552, 115.158], [43.857, 116.600], [44.212, 118.030], 
  [44.212, 118.030], [44.619, 119.446], [45.075, 120.847], [45.581, 122.231], 
  [46.134, 123.597], [46.735, 124.942], [47.382, 126.267], [48.075, 127.568], 
  [48.812, 128.844], [49.592, 130.095], [50.416, 131.317], [51.281, 132.510], 
  [52.187, 133.672], [53.133, 134.802], [54.118, 135.898], [55.141, 136.958], 
]

SW_RJ45 = '11'
SW_RotEnc = '65'

angle_M_Comm = -18
angle_Inner_Index = -15.2

dx_Dot = -2.997559
dx_Comma = -2.997559
dx_Index = 1.786772
dx_Inner = -2.742943
dx_Pinky = 2.371815

dx_cols = [
    dx_Inner,
    dx_Index, dx_Index,
    dx_Comma,
    dx_Dot,
    dx_Pinky, dx_Pinky, dx_Pinky,
]

def is_SW( idx: str ):
    return idx not in [SW_RJ45, SW_RotEnc]

def is_L2R_key( idx: str ):
    row = idx[1]
    return row in '13'

def is_Thumb_key( idx: str ):
    row = idx[1]
    return row in '5'

def get_diode_side( idx: str ):
    return -1 if idx[0] in '123' or is_Thumb_key( idx ) else +1

def get_top_row_idx( cidx: int ):
    if cidx == 1:
        return 3
    elif cidx == 8:
        return 2
    else:
        return 1

def get_btm_row_idx( cidx: int ):
    if cidx == 7:
        return 3
    else:
        return 4

def is_top_of_col( idx: str ):
    col, row = int( idx[0] ), int( idx[1] )
    return get_top_row_idx( col ) == row

def is_btm_of_col( idx: str ):
    col, row = int( idx[0] ), int( idx[1] )
    return get_btm_row_idx( col ) == row

holes = [
    ( 16.8, 150, 90 - 16),
    ( 4.4, J1_y - 11, 90),
    ( 4.4, J1_y + 11, 90),
    ( 14, 35, -30),
    ( 66, 5, 90),
    (106, 5, 90),
    (154, 31, 36),
    (163, 84, -40),
    (J2_x - 1.6, J2_y + 10, 90),
    (68, 119.6, -64),
    # (47, 136, -46),
    #
    (65, 84.6, 90),
]


# Board Type
# class Board(Enum):
BDT = 2# Top plate
BDS = 1# Second Top plate
BDC = 0# Circuit plate
BDM = 3# Middle plate
BDB = 4# Bottom plate

BDL = -1
BDR = -1

# Edge.Cuts size
Edge_CX, Edge_CY = 0, 0
Edge_W, Edge_H = 0, 0


def make_rect( size, offset = (0, 0) ):
    FourCorners = [(0, 0), (1, 0), (1, 1), (0, 1)]
    return map( lambda pt: vec2.add( (size[0] * pt[0], size[1] * pt[1]), offset ), FourCorners )

def make_corners( key_cnrs ):
    corners = []
    for mod, offset, dangle, cnr_type, prms in key_cnrs:
        if type( mod ) == str:
            x, y, _, _, angle = keys[mod]
            # flip y
            y = -y
            offset = (offset[0], -offset[1])
        else:
            x, y, angle = mod
        # print( x, y, angle, offset )
        pos = vec2.mult( mat2.rotate( angle ), offset, (x, y) )
        corners.append( [(pos, -angle + dangle), cnr_type, prms] )
    return corners

def drawEdgeCuts( board ):
    width = 0.12

    pnts = []
    for pnt in EdgeCuts:
        if len( pnts ) == 0 or not vec2.equal( pnt, pnts[-1] ):
            pnts.append( pnt )
    if not vec2.equal( pnts[0], pnts[-1] ):
        pnts.append( pnts[0] )
    kad.add_lines( pnts, 'Edge.Cuts', width )
    return

    U1_mod = (U1_x, U1_y, 0)
    J1_mod = (J1_x, J1_y, J1_angle)
    J2_mod = (J2_x, J2_y, J2_angle)
    J3_mod = (J3_x, J3_y, J3_angle)

    midcnrs_set = []
    if True:# outer
        out_cnrs = []
        mid_cnrs = []
        # LED & J3:
        if True:# bottom right corner
            cnrs = [
                (J3_mod, (-7, 1.27), 180, BezierRound, [14]),
            ]
            for cnr in cnrs:
                out_cnrs.append( cnr )
        if True:# BDM
            cnrs = [
                # J3
                (J3_mod, (+14.8, +1.27), 180, BezierRound, [14]),
                (J3_mod, (+14.2, +1.00), 270, BezierRound, [0.2]),
                (J3_mod, (+13.6, 0),     180, BezierRound, [0.5]),
                (J3_mod, (+13.0, +1.00),  90, BezierRound, [0.5]),
                (J3_mod, (+12.4, +1.27), 180, BezierRound, [0.2]),
                # LED
                (J3_mod, (-1.5,   0), 270, BezierRound, [0.5]),
                (J3_mod, (-4, -2.27), 180, BezierRound, [0.5]),
                (J3_mod, (-5.8,   0),  90, BezierRound, [0.5]),
                (J3_mod, (-7, +1.27), 180, BezierRound, [0.5]),
            ]
            for cnr in cnrs:
                mid_cnrs.append( cnr )
        # bottom left
        cnrs = [
            ('84', (-10.0, 15.0), -30.4, Spline, [70]),
            (J1_mod, (-J1_x,  +10), 270, Round, [20]),
            (J1_mod, (-J1_x/2, +7),   0, Round, [2]),
        ]
        for cnr in cnrs:
            out_cnrs.append( cnr )
            mid_cnrs.append( cnr )
        # J1: Split
        if board in [BDL, BDR]:
            cnrs = [
                (J1_mod, (0, +USBC_Width+1), 270, Round, [0.5]),
                (J1_mod, (3, +USBC_Width  ),   0, Round, [0.5]),
                (J1_mod, (USBC_Height, 0),   270, Round, [0.5]),
                (J1_mod, (3, -USBC_Width),   180, Round, [0.5]),
                (J1_mod, (0, -USBC_Width-1), 270, Round, [0.5]),
            ]
        else:
            cnrs = [
                (J1_mod, (0, 0), 270, Round, [0.5]),
            ]
        for cnr in cnrs:
            out_cnrs.append( cnr )
        if True:# BDM
            cnrs = [
                (J1_mod, (16.8, 0), 270, Round, [0.5]),
            ]
            for cnr in cnrs:
                mid_cnrs.append( cnr )
        # top side
        cnrs = [
            (J1_mod, (-J1_x/2, -7), 180, Round, [0.5]),
            (J1_mod, (-J1_x,  -10), 270, Round, [2]),
            ('34', (-10.4, 16.8), angle_PB - angle_M, Round, [67]),
            ('71', (+26.6, 11.7), 90, Round, [67]),
            ('71', (0, -12.2), 180, Round, [16]),
        ]
        for cnr in cnrs:
            out_cnrs.append( cnr )
            mid_cnrs.append( cnr )
        # J2: USB PC
        if board in [BDL]:
            cnrs = [
                (J2_mod, (2.62, -USBC_Width-1),  90, Round, [0.5]),
                (J2_mod, (2.62-3, -USBC_Width), 180, Round, [0.5]),
                (J2_mod, (2.62-USBC_Height, 0),  90, Round, [0.5]),
                (J2_mod, (2.62-3, +USBC_Width),   0, Round, [0.5]),
                # (J2_mod, (2.62, +USBC_Width+1),  90, Round, [0.5]),
            ]
            for cnr in cnrs:
                out_cnrs.append( cnr )
        if True:# BDM
            cnrs = [
                (J2_mod, (2.62, -USBM-USBT*2-0.2),  90, Round, [0.5]),
                (J2_mod, (-USBW+2, -USBM-USBT*2),  180, Round, [0.2]),
                (J2_mod, (-USBW,   -USBM-USBT),     90, Round, [0.5]),
                (J2_mod, (-USBW+2, -USBM     ),      0, Round, [0.5]),
                (J2_mod, (2.62,    0         ),     90, Round, [0.5]),
                (J2_mod, (-USBW+2, +USBM     ),    180, Round, [0.5]),
                (J2_mod, (-USBW,   +USBM+USBT),     90, Round, [0.5]),
                (J2_mod, (-USBW+2, +USBM+USBT*2),    0, Round, [0.5]),
            ]
            for cnr in cnrs:
                mid_cnrs.append( cnr )
        # bottom right
        cnrs = [
            (J2_mod, (2.62, 10), +90, Round, [0.5]),
            (J2_mod, (-1, 14), 180, Round, [3]),
        ]
        for cnr in cnrs:
            out_cnrs.append( cnr )
            mid_cnrs.append( cnr )
        # BDM
        midcnrs_set.append( make_corners( mid_cnrs ) )
        # draw
        if board is not BDM:
            corners = make_corners( out_cnrs )
            kad.draw_closed_corners( corners, 'Edge.Cuts', width )
            if True:# PCB Size
                x0, x1 = +1e6, -1e6
                y0, y1 = +1e6, -1e6
                for (pos, _), _, _ in corners:
                    x, y = pos
                    x0 = min( x0, x )
                    x1 = max( x1, x )
                    y0 = min( y0, y )
                    y1 = max( y1, y )
                global Edge_CX, Edge_CY
                global Edge_W, Edge_H
                Edge_CX, Edge_CY = (x0 + x1) / 2, (y0 + y1) / 2
                Edge_W, Edge_H = x1 - x0, y1 - y0
                if True:
                    # print( 'Edge: (CX, CY) = ({:.2f}, {:.2f})'.format( Edge_CX, Edge_CY ) )
                    print( 'Edge: (W, H) = ({:.2f}, {:.2f})'.format( Edge_W, Edge_H ) )

    if board in [BDL, BDR, BDM]:# J3
        off_y = -1
        cnrs = [
            (J3_mod, (+14.2, off_y - 0.70), 270, BezierRound, [0.5]),
            (J3_mod, (+10.0, off_y - 1.27), 180, BezierRound, [0.5]),
            (J3_mod, (-0.50, off_y - 0.70),  90, BezierRound, [0.5]),
            (J3_mod, (+10.0, off_y - 0.00),   0, BezierRound, [0.5]),
        ]
        midcnrs_set.append( make_corners( cnrs ) )
    if board in [BDL, BDR, BDM]:# U1
        cnrs = [
            (U1_mod, (0,   -8),   0, Round, [1]),
            (U1_mod, (13.6, 0),  90, Round, [1]),
            (U1_mod, (0, 10.4), 180, Round, [1]),
            (U1_mod, (-8,   0), 270, Round, [1]),
        ]
        midcnrs_set.append( make_corners( cnrs ) )
    if board in [BDL, BDR, BDM]:# mid hole (4-fingers)
        cnrs = [
            ('14', (-8, 0), 270, BezierRound, [3]),
            ('24', (0, +8.8), 0, BezierRound, [5]),
            ('34', (0, +8.8), 0, BezierRound, [3]),
            ('54', (-9, +13.6), 90 + angle_PB, BezierRound, [3]),
            ('64', (0, +9),     angle_PB,      BezierRound, [3]),
            ('64', (+7, 0),  90, BezierRound, [3]),
            ('73', (0, +8.8), 0, BezierRound, [3]),
            ('73', (+7, 0),  90, BezierRound, [3]),
            ('72', (+6.2, -7.6), 180, BezierRound, [3]),
            ('71', (+11.4, 0), 90, BezierRound, [3]),
            ('71', (0, -7.4), 180, BezierRound, [3]),
            ('51', (-12, -4), 270, BezierRound, [3]),
            ('41', (0, -7.4), 180, BezierRound, [3]),
            ('21', (0, -7.4), 180, BezierRound, [3]),
            ('11', (-16, -5.4), 180 + angle_PB, BezierRound, [3]),
            ('91', (-7, 0),  270, BezierRound, [3]),
            ('91', (0, +8.8),  0, BezierRound, [3]),
            ('12', (-7, 4),  270, BezierRound, [3]),
            ('13', (-7, +7.0), 0, BezierRound, [3]),
        ]
        midcnrs_set.append( make_corners( cnrs ) )
    if board in [BDL, BDR, BDM]:# mid hole (thumb)
        cnrs = [
            ('84', (0, +8.6),   0, BezierRound, [4]),
            ('84', (+7.0, 0),  90, BezierRound, [4]),
            ('83', (+7.0, 0),  90, BezierRound, [4]),
            ('82', (+10, 4),    0, BezierRound, [1]),
            ('82', (+11.6, 0), 90, BezierRound, [1]),
            ('82', (0, -7.6), 180, BezierRound, [4]),
            ('82', (-7.0, 0), 270, BezierRound, [4]),
            ('83', (-7.0, 0), 270, BezierRound, [3]),
            ('84', (-7.0, 0), 270, BezierRound, [3]),
        ]
        midcnrs_set.append( make_corners( cnrs ) )
    if board in [BDL, BDR, BDM]:# draw BDM
        layers = ['Edge.Cuts'] if board == BDM else ['F.Fab']#['F.SilkS', 'B.SilkS']
        w = width if board == BDM else width * 2
        for midcnrs in midcnrs_set:
            for layer in layers:
                kad.draw_closed_corners( midcnrs, layer, w )

def load_distance_image( path ):
    with open( path ) as fin:
        data = fin.readlines()
        w = int( data[0] )
        h = int( data[1] )
        print( w, h )
        dist = []
        for y in range( h ):
            vals = data[y+2].split( ',' )
            del vals[-1]
            if len( vals ) != w:
                print( 'Error: len( vals )({}) != w({})'.format( len( vals ), w ) )
                break
            vals = map( lambda v: float( v ) / 100.0, vals )
            dist.append( vals )
    return (dist, w, h)

def get_distance( dist_image, pnt ):
    dist, w, h = dist_image
    x, y = vec2.scale( 10, vec2.sub( pnt, (Edge_CX, Edge_CY) ) )
    x, y = vec2.add( (x, y), (w / 2.0, h / 2.0) )
    x = min( max( x, 0. ), w - 1.01 )
    y = min( max( y, 0. ), h - 1.01 )
    nx = int( math.floor( x ) )
    ny = int( math.floor( y ) )
    # if nx < 0 or w <= nx + 1 or ny < 0 or h <= ny + 1:
    #     return 0
    dx = x - nx
    dy = y - ny
    d  = dist[ny][nx]     * (1 - dx) * (1 - dy)
    d += dist[ny][nx+1]   * dx       * (1 - dy)
    d += dist[ny+1][nx]   * (1 - dx) * dy
    d += dist[ny+1][nx+1] * dx       * dy
    return d

CIDX, POS, NIDX = range( 3 )

def connect_line_ends( line_ends, other_ends, curv_idx, pos, idx, layer, width ):
    # overwrite new line_end
    line_ends[idx] = (curv_idx, pos, 0)

    # connect with up/down neighbors
    for nidx in [idx-1, idx+1]:
        if nidx < 0 or len( line_ends ) <= nidx:
            continue
        # up / down neighbor
        neib = line_ends[nidx]
        if not neib:# no neibor
            continue
        if (neib[NIDX] & (1 << idx)) != 0:# already connected with this index
            #    L1-----R1      L1----
            #    C  ...---^^^ <-- cannot connect L1(right) and L2,
            #     L2--------R2    because L2 is already connected with L1(left)
            continue

        # The lines are drawn from left to right.
        # For the right line ends, reject the neighbor if there is a left end after the neighbor right end.
        # For the left line ends, reject the neighbor if there is a right end after the neighbor left end.
        if other_ends[nidx] and other_ends[nidx][CIDX] > neib[CIDX]:
            #    L1----------------------------R1
            #    C             .....-----^^^^^    <-- cannot connect R1 and R2(right),
            #     L2---------R2        L2---------R2  becuase L2(right) is on the right of R2(left)
            #          neib[CIDX] left[CIDX]
            continue
            pass
        # connect
        curr = line_ends[idx]
        line_ends[idx]  = (curr[CIDX], curr[POS], curr[NIDX] | (1 << nidx))
        line_ends[nidx] = (neib[CIDX], neib[POS], neib[NIDX] | (1 << idx))
        kad.add_line( curr[POS], neib[POS], layer, width )

def draw_top_bottom( board, sw_pos_angles ):
    if board in [BDT, BDS]:# keysw holes
        length = 13.94 if board == BDT else 14.80
        for sw_pos, angle in sw_pos_angles:
            corners = []
            for i in range( 4 ):
                deg = i * 90 + angle
                pos = vec2.scale( length / 2.0, vec2.rotate( deg ), sw_pos )
                # corners.append( [(pos, deg + 90), Round, [0.9]] )
                corners.append( [(pos, deg + 90), BezierRound, [0.9]] )
            kad.draw_closed_corners( corners, 'Edge.Cuts', 0.1 )

    if board == BDS:
        return

    if False:# screw holes
        for prm in holes:
            x, y, angle = prm
            ctr = (x, y)
            kad.add_arc( ctr, vec2.add( ctr, (2.5, 0) ), 360, 'Edge.Cuts', 0.1 )
        return

    ctr_pos_angle_vec = []
    anchors = [
        (28, 125),
        (27, 110),
        (1, -3),
        (5, +3),
        (9, -3),
        (13, +3),
        (17, 24),
        (20, 26),
        (24, 28),
    ]
    for n in range( 1, len( anchors ) ):
        anchor_a = anchors[n-1]
        anchor_b = anchors[n]
        pos_a, angle_a = sw_pos_angles[anchor_a[0]]
        pos_b, angle_b = sw_pos_angles[anchor_b[0]]
        angle_a += anchor_a[1]
        angle_b += anchor_b[1]
        if abs( angle_a - angle_b ) > 1:
            vec_a = vec2.rotate( angle_a + 90 )
            vec_b = vec2.rotate( angle_b + 90 )
            ctr, _, _ = vec2.find_intersection( pos_a, vec_a, pos_b, vec_b )
            if n == 1:
                angle_a += (angle_a - angle_b) * 1.1
            elif n + 1 == len( anchors ):
                angle_b += (angle_b - angle_a) * 1.5
            if False:
                layer = 'F.Fab'
                width = 1.0
                # print( ctr, ka, kb )
                kad.add_line( ctr, pos_a, layer, width )
                kad.add_line( ctr, pos_b, layer, width )
        else:
            ctr = None
        ctr_pos_angle_vec.append( (ctr, pos_a, angle_a, pos_b, angle_b) )
    # return

    # read distance data
    board_type = { BDT : 'T', BDB: 'B' }[board]
    dist_image = load_distance_image( '/Users/akihiro/repos/Hermit/Hermit{}/Edge_Fill.txt'.format( board_type ) )

    # draw lines
    pos_dummy = [None, None]
    pitch = 2.0
    nyrange = range( -559, 888, 16 )
    width0, width1 = 0.3, 1.3
    for ny in nyrange:
        y = ny * 0.1
        uy = float( ny - nyrange[0] ) / float( nyrange[-1] - nyrange[0] )
        if True:
            if uy < 0.5:
                uy = 2 * uy
            else:
                uy = 2 * (1 - uy)
        # base position
        idx_base = 2
        anchor_base = anchors[idx_base]
        pos_base, angle_base = sw_pos_angles[anchor_base[0]]
        angle_base += anchor_base[1]
        pos_base = vec2.mult( mat2.rotate( -angle_base ), (0, y), pos_base )
        # control points for one horizontal line
        pos_angles = [(pos_base, angle_base)]
        for dir in [-1, +1]:
            idx = idx_base
            pos_a, angle_a = pos_base, angle_base
            while 0 < idx and idx < len( ctr_pos_angle_vec ):
                idx2 = idx + dir
                if dir == -1:
                    ctr, _, angle_b, _, angle_a = ctr_pos_angle_vec[idx2]
                else:# dir == +1:
                    ctr, _, angle_a, _, angle_b = ctr_pos_angle_vec[idx]
                idx = idx2
                #
                vec_b = vec2.rotate( angle_b + 90 )
                pos_b = vec2.scale( -vec2.distance( pos_a, ctr ), vec_b, ctr )
                pos_angles.append( (pos_b, angle_b) )
                pos_a = pos_b
            if dir == -1:
                pos_angles.reverse()

        # one horizontal line with nearly constant pitch
        curv = []
        for idx, (pos_b, angle_b) in enumerate( pos_angles ):
            if idx == 0:
                curv.append( pos_b )
                continue
            if False:
                curv.append( pos_b )
            else:
                pos_a, angle_a = pos_angles[idx-1]
                # pnts = kad.calc_bezier_round_points( pos_a, vec2.rotate( angle_a ), pos_b, vec2.rotate( angle_b + 180 ), 8 )
                pnts = kad.calc_bezier_corner_points( pos_a, vec2.rotate( angle_a ), pos_b, vec2.rotate( angle_b + 180 ), pitch, ratio = 0.8 )
                for idx in range( 1, len( pnts ) ):
                    curv.append( pnts[idx] )

        gap = 0.5
        if True:# divide if close to the edge
            div = 10
            thick = width1 / 2.0 + gap
            curv2 = []
            for idx, pnt in enumerate( curv ):
                dist = get_distance( dist_image, pnt )
                if idx == 0:
                    prev_pnt = pnt
                    prev_dist = dist
                    curv2.append( pnt )
                    continue
                if max( dist, prev_dist ) > -pitch and min( dist, prev_dist ) < thick:
                    vec = vec2.sub( pnt, prev_pnt )
                    for i in range( 1, div ):
                        curv2.append( vec2.scale( i / float( div ), vec, prev_pnt ) )
                curv2.append( pnt )
                prev_pnt = pnt
                prev_dist = dist
            curv = curv2

        # draw horizontal line avoiding key / screw holes
        w_thin = 0.25
        thick_thin = w_thin / 2.0 + gap
        for lidx, layer in enumerate( ['F.Cu', 'B.Cu'] ):
            if lidx == 0:
                w = width0 + (width1 - width0) * uy
            else:
                w = width1 + (width0 - width1) * uy
            thick = w / 2.0 + gap
            num_lines = int( math.ceil( w / (w_thin * 0.96) ) )
            line_sep = (w - w_thin) / (num_lines - 1)
            line_lefts = [None for _ in range( num_lines )]
            line_rights = [None for _ in range( num_lines )]
            last_pnt = [None for _ in range( num_lines )]
            for cidx in range( 1, len( curv ) ):
                pnt_a = curv[cidx-1]
                pnt_b = curv[cidx]
                if False:
                    kad.add_line( pnt_a, pnt_b, layer, w )
                    # kad.add_arc( pnt_a, vec2.add( pnt_a, (w / 2, 0) ), 360, layer, 0.1 )
                    continue
                vec_ba = vec2.sub( pnt_b, pnt_a )
                unit_ba = vec2.normalize( vec_ba )[0]
                norm_ba = (unit_ba[1], -unit_ba[0])
                # multiple horizontal lines
                single = True
                lines = []
                for m in range( num_lines ):
                    delta = line_sep * m + w_thin / 2.0 - w / 2.0
                    q0 = vec2.scale( delta, norm_ba, pnt_a )
                    q1 = vec2.scale( delta, norm_ba, pnt_b )
                    d0 = get_distance( dist_image, q0 )
                    d1 = get_distance( dist_image, q1 )
                    if min( d0, d1 ) < thick:
                        single = False
                    if d0 >= thick_thin and d1 >= thick_thin:# single line
                        pass
                    elif d0 >= thick_thin:
                        while d1 < thick_thin - 0.01:
                            diff = thick_thin - d1
                            q1 = vec2.scale( -diff * 0.94, unit_ba, q1 )
                            d1 = get_distance( dist_image, q1 )
                        connect_line_ends( line_lefts, line_rights, cidx, q1, m, layer, w_thin )
                    elif d1 >= thick_thin:
                        while d0 < thick_thin - 0.01:
                            diff = thick_thin - d0
                            q0 = vec2.scale( +diff * 0.94, unit_ba, q0 )
                            d0 = get_distance( dist_image, q0 )
                        connect_line_ends( line_rights, line_lefts, cidx, q0, m, layer, w_thin )
                    else:# no line
                        q0 = None
                        q1 = None
                    if q0 and q1:
                        lines.append( (q0, q1) )
                        if last_pnt[m]:
                            d = vec2.distance( last_pnt[m], q0 )
                            if 0.01 < d and d < 0.8:# close tiny gap
                                kad.add_line( last_pnt[m], q0, layer, w_thin )
                        last_pnt[m] = q1

                if single:
                    kad.add_line( pnt_a, pnt_b, layer, w )
                    if not pos_dummy[lidx] and w > 1.1:
                        pos_dummy[lidx] = pnt_a
                else:
                    for (q0, q1) in lines:
                        kad.add_line( q0, q1, layer, w_thin )
                # clear line_ends when single or no line
                if single or len( lines ) == 0:
                    for m in range( num_lines ):
                        line_lefts[m] = None
                        line_rights[m] = None
    kad.set_mod_pos_angle( 'P1', pos_dummy[0], 0 )
    kad.set_mod_pos_angle( 'P2', pos_dummy[1], 0 )

def add_zone( net_name, layer_name, rect, zones ):
    return
    layer = pcb.GetLayerID( layer_name )
    zone, poly = kad.add_zone( rect, layer, len( zones ), net_name )
    zone.SetZoneClearance( pcbnew.FromMils( 20 ) )
    zone.SetMinThickness( pcbnew.FromMils( 16 ) )
    #zone.SetThermalReliefGap( pcbnew.FromMils( 12 ) )
    #zone.SetThermalReliefCopperBridge( pcbnew.FromMils( 24 ) )
    zone.Hatch()
    #
    zones.append( zone )
    #polys.append( poly )

Cu_layers = ['F.Cu', 'B.Cu']

GND = pcb.FindNet( 'GND' )
VCC = pcb.FindNet( '3V3' )

# power rails
via_led_pwr_1st = {}
wire_via_led_pwr_1st = {}
wire_via_led_pwr_2nd = {}

# led dat connection
via_led_rght = {}
wire_via_led_left = {}
wire_via_led_rght = {}

# debounce row
wire_via_dbnc_vcc = {}
wire_via_dbnc_gnd = {}

via_dbnc_row = {}
via_dbnc_col = {}

# exp vias
via_exp = {}


### Set mod positios
def place_key_switchs():
    ###
    ### Set key positios
    ###
    sw_pos_angles = []
    for idx in sorted( keys.keys() ):
        px, py, w, h, angle = keys[idx]
        sw_pos = (px, -py)
        sw_pos_angles.append( (sw_pos, 180 - angle) )
        isL2R = is_L2R_key( idx )
        isThumb = is_Thumb_key( idx )
        # SW & LED & Diode
        if True:
            # RJ45
            if idx == SW_RJ45:
                kad.set_mod_pos_angle( 'J1', vec2.scale( 6.2, vec2.rotate( -angle - 90 ), sw_pos ), angle )
                continue
            # RotaryEncoder
            if idx == SW_RotEnc:
                kad.set_mod_pos_angle( 'RE1', sw_pos, angle + 180 )
                continue
            # print( name )

            mod_sw = f'SW{idx}'
            mod_led = f'L{idx}'
            mod_cap = f'C{idx}'
            mod_dio = f'D{idx}'

            ### SW
            kad.set_mod_pos_angle( mod_sw, sw_pos, angle + 180 )
            # SW rectangle
            corners = []
            for pnt in make_rect( (w, h), (-w/2, -h/2) ):
                pt = vec2.mult( mat2.rotate( angle ), pnt, sw_pos )
                corners.append( [(pt, 0), Line, [0]] )
            kad.draw_closed_corners( corners, 'F.Fab', 0.1 )
            # wire 2-3
            kad.wire_mod_pads( [(mod_sw, '2', mod_sw, '3', 0.8, (Strt))])

            ### LED
            # original scale was 4.93
            pos = vec2.scale( 4.7, vec2.rotate( - angle - 90 ), sw_pos )
            kad.set_mod_pos_angle( mod_led, pos, angle + (180 if isL2R else 0))

            ### LED Caps
            pos = vec2.mult( mat2.rotate( angle ), (0, -7.2), sw_pos )
            kad.set_mod_pos_angle( mod_cap, pos, angle + (0 if isL2R else 180))

            ### Diode
            diode_sign = get_diode_side( idx )
            pos = vec2.mult( mat2.rotate( angle ), (-5.4 * diode_sign, 0), sw_pos )
            kad.set_mod_pos_angle( mod_dio, pos, angle - 90 )
            ### GND Vias
            # if name[0] not in ['1', '8', '9'] and name[1] not in ['1']:
            #     if board != BDC or name[0] != '7':
            #         pos = vec2.mult( mat2.rotate( angle ), (-5, 0), sw_pos )
            #         kad.add_via( pos, GND, VIA_Size[1] )

def place_mods():
    # I/O expanders
    kad.move_mods( (69.416, 95.907), -90, [
        (None, (0, 0), -21.2, [
            (f'U1', (0, 0), 0),
            (f'U2', (0, 0), 180),
            (f'C1', (0, 8), 0),
            (f'C2', (0, 8), 0),
        ] ),
    ] )

    # Debounce RRCs
    for cidx in range( 1, 9 ):
        idx = f'{cidx}4'
        lrs = get_diode_side( idx )
        mod_sw = f'SW{idx}'
        if cidx == 7:
            mod_sw = 'SW64'
            dx, dy = 11.4, -9.0
        else:
            dx, dy = 11.4, 2 * lrs
        pos, angle = kad.get_mod_pos_angle( mod_sw )
        kad.move_mods( pos, angle + 90, [
            (None, (dx, dy), 0, [
                (f'CD{cidx}', (0, -2.2 * lrs), 0),
                (f'R{cidx}1', (0,  0), 0),
                (f'R{cidx}2', (0, +2.2 * lrs), 180),
            ] ),
        ] )

    # RotEnc
    _, angle = kad.get_mod_pos_angle( 'RE1' )
    for i in range( 2 ):
        sgn = [+1, -1][i]
        cidx = [11, 12][i]
        pos = kad.calc_pos_from_pad( 'RE1', 'AB'[i], (-5, -1 * sgn) )
        kad.move_mods( pos, angle + 90 * sgn, [
            (f'CD{cidx}', (0, -1.5 * sgn), 0),
            (f'R{cidx}1', (0,  0), 0),
            (f'R{cidx}2', (0, +1.5 * sgn), 0),
        ] )

    # RotEnc diode
    _, angle = kad.get_mod_pos_angle( 'RE1' )
    pos = kad.calc_pos_from_pad( 'RE1', 'S2', (6, 0))
    kad.move_mods( pos, angle, [(f'D{SW_RotEnc}', (0, 0), 180)] )

    # RJ45 connector
    pos, angle = kad.get_mod_pos_angle( 'J1' )
    for side in range(2):
        for idx in range(4):
            kad.move_mods( pos, angle + 90, [
                (None, (4, 0), 0, [
                    (f'JP{"FB"[side]}{2 * idx + 2}', (0, 1.27 * (2 * idx - 3) * [+1, -1][side]), 0),
                ] ),
            ] )
        for idx in range(2):
            kad.move_mods( pos, angle - 90, [
                (None, (6, 0), 0, [
                    (f'JP{"FB"[side]}{4 * idx + 3}', (0, 2.54 * (2 * idx - 1) * [-1, +1][side]), 0),
                ] ),
            ] )

    # DL1
    mod_sw = 'SW21'
    _, angle = kad.get_mod_pos_angle( mod_sw )
    pos = kad.calc_pos_from_pad( mod_sw, '5', (1, 4.05) )
    kad.set_mod_pos_angle( 'DL1', pos, angle )
    return

    # dummy pads
    if board in [BDM, BDS]:
        for i in range( 2 ):
            dmy = 'P{}'.format( i + 1 )
            if kad.get_mod( dmy ):
                kad.set_mod_pos_angle( dmy, (J1_x + 20, J1_y), 0 )

    # draw mouting holes
    if True:
        for idx, prm in enumerate( holes ):
            x, y, angle = prm
            ctr = (x, y)
            hole = 'H{}'.format( idx + 1 )
            if kad.get_mod( hole ):
                kad.set_mod_pos_angle( hole, (x, y), 0 )
            else:
                corners = []
                if True:
                    hsize = [4.2, 4.86] if board in [BDL, BDR] else [4.4, 5.0]
                    for i in range( 4 ):
                        deg = i * 90 - angle
                        pos = vec2.scale( hsize[i % 2] / 2.0, vec2.rotate( deg ), ctr )
                        corners.append( [(pos, deg + 90), BezierRound, [1.2]] )
                else:
                    for i in range( 6 ):
                        deg = i * 60 - 90
                        pos = vec2.scale( 2.1, vec2.rotate( deg ), ctr )
                        corners.append( [(pos, deg + 90), BezierRound, [0.5]] )
                kad.draw_closed_corners( corners, 'Edge.Cuts', 0.2 )
                if False:
                    corners = []
                    for i in range( 6 ):
                        deg = i * 60 - 90
                        pos = vec2.scale( 2.0, vec2.rotate( deg ), ctr )
                        corners.append( [(pos, deg + 90), Linear, [0]] )
                    kad.draw_closed_corners( corners, 'F.Fab', 0.1 )

def wire_mods_exp():
    w_exp = 0.35
    w_row, r_row = 0.7, 2.0

    # GND
    wire_via_gnd = kad.add_via_relative( 'U1', '29', (0, 0), VIA_Size[1] )
    for mod_exp in ['U1', 'U2']:
        gnd_pad_nums = [6, 12, 13]
        if mod_exp == 'U1':
            gnd_pad_nums.append( 11 )
        for gnd_pad_num in gnd_pad_nums:
            base_angle = (((gnd_pad_num + 5) // 7) % 2) * 90 # not correct-worthy, but enough
            kad.wire_mod_pads( [(mod_exp, wire_via_gnd, mod_exp, str(gnd_pad_num), w_exp, (Dird, base_angle, base_angle + 90, 0))] )
    pcb.Delete( wire_via_gnd )

    # 4, 3, 2, 1, 28, ..., 18
    exp_pads = [f'{((4 - i - 1 + 28) % 28) + 1}' for i in range( 15 )]
    exp_nets = [kad.get_pad_net( 'U1', pad ) for pad in exp_pads]
    for i in range( 15 ):
        # dpos = vec2.scale( 7, vec2.rotate( 90 / 7 * i - 180 ) )
        # dpos = ((i - 7) * 1.2, (abs(i - 7) - 7) * 1.2)
        ny = abs( i - 7 )
        sy = vec2.sign( i - 7 )
        dpos = (ny * sy * 1.1, (ny**2 - 7**2) * 0.16)
        pos = kad.calc_pos_from_pad( 'U1', '29', dpos )
        net = exp_nets[i]
        via_exp[i] = kad.add_via( pos, net, VIA_Size[2])
        if ny in [0, 7]:
            prm = (Strt)
        elif ny <= 3:
            # prm = (Dird, 90, 45 * sy, 1)
            prm = (ZgZg, 90, 45 - 12 * (3 - ny), 1)
        else:
            prm = (Dird, 0, 45 + 22.5 * (ny - 2), 1)
        kad.wire_mod_pads( [('U1', exp_pads[i], 'U1', via_exp[i], 0.35, prm)] )
        kad.wire_mod_pads( [('U2', exp_pads[14-i], 'U1', via_exp[i], 0.35, prm)] )

def wire_mods_debounce():
    w_exp, r_exp = 0.44, 0.4
    w_pwr, r_pwr = 0.75, 1
    w_dbn, r_dbn = 0.6, 1
    w_row, r_row = 0.8, 2.3 # SW row
    w_col, r_col = 0.6, 0.8

    via_dbnc_vcc_conn = {}
    via_dbnc_gnd_conn = {}
    via_dbnc_vcc = {}# col: int
    via_dbnc_gnd = {}

    for cidx in range( 1, 9 ):
        mod_cd = f'CD{cidx}'
        mod_r1 = f'R{cidx}1'
        mod_r2 = f'R{cidx}2'

        lrs = get_diode_side( f'{cidx}4' )

        # row gnd and vcc vias
        dx = -1.6 * lrs
        wire_via_dbnc_vcc[cidx] = kad.add_via_relative( mod_cd, '1', (-2.8, dx), VIA_Size[1] )
        wire_via_dbnc_gnd[cidx] = kad.add_via_relative( mod_r2, '2', (+1.4, dx), VIA_Size[1] )
        via_dbnc_vcc[cidx] = kad.add_via_relative( mod_cd, '1', (-2.8 - 0.1, dx), VIA_Size[1] )
        # via_dbnc_gnd[cidx] = kad.add_via_relative( mod_r2, '2', (+1.4 + 0.1, dx), VIA_Size[1] )
        via_dbnc_vcc_conn[cidx] = kad.add_via_relative( mod_cd, '1', (0, dx), VIA_Size[1] )
        via_dbnc_gnd_conn[cidx] = kad.add_via_relative( mod_r2, '2', (0, dx), VIA_Size[1] )
        via_dbnc_row[cidx] = kad.add_via_relative( mod_cd, '2', (0.1, dx), VIA_Size[1] )
        via_dbnc_col[cidx] = kad.add_via_relative( mod_r2, '1', (0, dx), VIA_Size[1] )

        # resister and cap vias
        for layer in Cu_layers:
            kad.wire_mod_pads( [
                # debounce resisters and cap
                (mod_r1, '1', mod_r2, '1', w_col, (ZgZg, 90, 90, 0.5), layer),
                (mod_r1, '2', mod_cd, '2', w_col, (Dird, 90, 0, 0), layer),
                # res & cap pads and via
                (mod_cd, '1', mod_cd, via_dbnc_vcc_conn[cidx], w_col, (Strt), layer),
                (mod_r2, '2', mod_r2, via_dbnc_gnd_conn[cidx], w_col, (Strt), layer),
                (mod_cd, '2', mod_cd, via_dbnc_row[cidx], w_col, (Dird, 90, 0, 0), layer),
                (mod_r2, '1', mod_cd, via_dbnc_col[cidx], w_col, (Dird, 90, 0, 0), layer),
            ] )
        kad.wire_mod_pads( [
            # debounce to vcc / gnd
            (mod_cd, via_dbnc_vcc_conn[cidx], mod_cd, wire_via_dbnc_vcc[cidx], w_row, (Strt), 'B.Cu'),
            (mod_r2, via_dbnc_gnd_conn[cidx], mod_r2, wire_via_dbnc_gnd[cidx], w_row, (Strt), 'F.Cu'),
        ] )

    mod_re = 'RE1'
    for i, cidx in enumerate( [11, 12] ):
        mod_cd = f'CD{cidx}'
        mod_r1 = f'R{cidx}1'
        mod_r2 = f'R{cidx}2'

        # # row gnd and vcc vias
        via_dbnc_row[cidx] = kad.add_via_relative( mod_cd, '2', (+1.6, 0), VIA_Size[1] )
        via_dbnc_gnd[cidx] = kad.add_via_relative( mod_r2, '2', (+1.6, 0), VIA_Size[1] )

        # resister and cap vias
        for layer in Cu_layers:
            kad.wire_mod_pads( [
                # debounce resisters and cap
                (mod_r1, '1', mod_r2, '1', w_col, (Strt), layer),
                (mod_r1, '2', mod_cd, '2', w_col, (Dird, 90, 0, 0), layer),
                # res & cap pads and via
                (mod_cd, '2', mod_cd, via_dbnc_row[cidx], w_col, (Dird, 90, 0), layer),
                (mod_r2, '2', mod_r2, via_dbnc_gnd[cidx], w_col, (Dird, 90, 0), layer),
                # rotenc
                (mod_re, 'C', mod_cd, '1', w_col, (Dird, 0, 0, r_col), layer),
                (mod_re, 'AB'[i], mod_r2, '1', w_col, (Dird, 90, 90), layer),
            ] )
    # cap to rotenc vcc
    for layer in Cu_layers:
        kad.wire_mod_pads( [
            ('CD11', '1', 'CD12', '1', w_col, (Strt), layer),
        ] )

def wire_mods_col_diode():
    w_col, r_col = 0.6, 0.8

    # via
    via_dio = {}
    via_dio_col = {}

    # diode vias and wire them
    for idx in keys.keys():
        if not is_SW( idx ):
            continue
        lrs = get_diode_side( idx )  
        mod_sw = 'SW' + idx
        mod_dio = 'D' + idx
        # vias
        via_dio[idx] = kad.add_via_relative( mod_dio, '1', (-1.8, 0), VIA_Size[1] )
        via_dio_col[idx] = kad.add_via_relative( mod_dio, '1', (0, 2.0 * lrs), VIA_Size[1] )
        # wire to SW pad & diode via
        for layer in Cu_layers:
            kad.wire_mod_pads( [
                (mod_dio, '2', mod_sw, '3' if lrs > 0 else '2', w_col, (Dird, 0, 0), layer),
                (mod_dio, '1', None, via_dio[idx], w_col, (Strt), layer),
            ] )
        row = idx[1]
        if row in ['5']:
            continue
        # wire from diode via to connection via
        prm_dios = []
        if is_top_of_col( idx ):
            prm_dios.append( (Dird, 90, 0) )
        else:
            prm_dios.append( (Dird, 90, 0, r_col) )
            prm_dios.append( (Dird, 90, ([(180, 5)], 0), r_col) )
        for prm_dio in prm_dios:
            kad.wire_mod_pads( [(mod_dio, via_dio[idx], mod_dio, via_dio_col[idx], w_col, prm_dio, 'B.Cu')] )

    # RotEnc diode
    if True:
        idx = SW_RotEnc
        mod_re = 'RE1'
        mod_dio = f'D{idx}'
        via_dio[idx] = kad.add_via_relative( mod_dio, '1', (-2, 0), VIA_Size[1] )
        for layer in Cu_layers:
            kad.wire_mod_pads( [
                (mod_dio, '1', None, via_dio[idx], w_col, (Strt), layer),
                (mod_dio, '2', mod_re, 'S2', w_col, (Dird, 0, 90), layer),
            ] )

    # col lines
    for cidx in range( 1, 9 ):
        for ridx in range( 1, 4 ):
            # from (top) & to (bottom)
            top = f'{cidx}{ridx}'
            btm = f'{cidx}{ridx+1}'
            if top not in keys.keys() or not is_SW( top ):
                continue
            if btm not in keys.keys() or not is_SW( btm ):
                continue
            # route
            if btm in ['64']:
                prm_dio = (Dird, 0, 0, 20)
            elif btm in ['84']:
                prm_dio = (Dird, 0, ([(180, 6)], -50), 6)
            else:
                prm_dio = (ZgZg, 0, 30)
            dio_T = 'D' + top
            dio_B = 'D' + btm
            kad.wire_mod_pads( [(dio_T, via_dio_col[top], dio_B, via_dio_col[btm], w_col, prm_dio, 'B.Cu')] )

        mod_r = f'R{cidx}2'
        # row4 to debounce resister
        idx = f'{cidx}{get_btm_row_idx( cidx )}'
        mod_dio = f'D{idx}'
        if cidx == 7:
            prm = (Dird, 0, ([(90, 1.5), (0, 4), (-90, 5)], 0))
        else:
            prm = (Dird, 0, 90)
        kad.wire_mod_pads( [(mod_dio, via_dio_col[idx], mod_r, via_dbnc_col[cidx], w_col, prm, 'B.Cu')] )

        # thumb / RotEnc to debounce resister
        idx = f'{cidx}5'
        mod_dio = f'D{idx}'
        prm = None
        if cidx in [1, 2, 3]:
            prm = (Dird, ([(90, 2)], 0), 0, 3)
        elif idx == SW_RotEnc:
            prm = (Dird, 0, 0, 3)
        if prm != None:
            kad.wire_mod_pads( [(mod_dio, via_dio[idx], mod_r, via_dbnc_col[cidx], w_col, prm, 'B.Cu')] )

    for via in via_dio_col.values():
        pcb.Delete( via )

def wire_mods_row_led():
    w_row = 0.8 # SW row
    w_led, r_led = 0.7, 1.2 # LED power
    w_dat = 0.5 # LED dat

    dy_via_1st = 0.15
    dy_via_2nd = 0.1
    dy_via_dat = 0.12

    sep_led = 1.1
    sep_led_cnr = 1.4
    sep_led_via = 2.0

    # caps
    via_cap_vcc = {}
    via_cap_gnd = {}
    # led dat
    via_led_in  = {}
    via_led_out = {}
    # wiring corner center positions
    ctr_row_sw = {}
    ctr_led_left = {}
    ctr_led_rght = {}
    ctr_vcc_left = {}
    ctr_vcc_rght = {}

    for idx in keys.keys():
        if not is_SW( idx ):
            continue
        mod_sw = 'SW' + idx
        mod_led = 'L' + idx
        mod_cap = 'C' + idx

        isL2R = is_L2R_key( idx )
        lrx = 0 if isL2R else 1 # L/R index
        lrs = [+1, -1][lrx] # L/R sign

        ### Making Vias
        col = idx[0]
        dx = 0.8625 if col in '145' else -1.5
        via_led_pwr_1st[idx]      = kad.add_via_relative( mod_cap, '12'[lrx],   vec2.scale( lrs, (dx, -(0.05 + sep_led * 2 + dy_via_1st)) ), VIA_Size[1] )
        wire_via_led_pwr_1st[idx] = kad.add_via_relative( mod_cap, '12'[lrx],   vec2.scale( lrs, (dx, -(0.05 + sep_led * 2)) ), VIA_Size[1] )
        wire_via_led_pwr_2nd[idx] = kad.add_via_relative( mod_cap, '12'[lrx^1], vec2.scale( lrs, (1.5, -(0.05 + sep_led * 1)) ), VIA_Size[1] )
        via_cap_vcc[idx] = kad.add_via_relative( mod_cap, '1', (-1.5, dy_via_2nd * lrs), VIA_Size[1] )
        via_cap_gnd[idx] = kad.add_via_relative( mod_cap, '2', (+1.5, dy_via_2nd * lrs), VIA_Size[1] )
        via_led_in [idx] = kad.add_via_relative( mod_led, '73'[lrx], (+1.5, 0), VIA_Size[2] )
        via_led_out[idx] = kad.add_via_relative( mod_led, '15'[lrx], (-1.5, 0), VIA_Size[2] )
        via_led_rght[idx]      = kad.add_via_relative( mod_led, '13'[lrx], vec2.scale( lrs, (-3.4, sep_led_via - dy_via_dat) ), VIA_Size[2] )
        wire_via_led_rght[idx] = kad.add_via_relative( mod_led, '13'[lrx], vec2.scale( lrs, (-3.4, sep_led_via) ), VIA_Size[2] )
        wire_via_led_left[idx] = kad.add_via_relative( mod_led, '75'[lrx], vec2.scale( lrs, (+3.4, sep_led_via) ), VIA_Size[2] )

        # wiring centers
        ctr_row_sw[idx] = kad.calc_pos_from_pad( mod_sw, '5', (0, -5) )
        ctr_led_left[idx] = kad.calc_pos_from_pad( mod_cap, '12'[lrx], vec2.scale( -lrs, (3.6, sep_led * 2 + sep_led_cnr) ) )
        ctr_led_rght[idx] = kad.calc_pos_from_pad( mod_led, '13'[lrx], vec2.scale( lrs, (-3.9, sep_led_via - sep_led_cnr) ) )
        ctr_vcc_left[idx] = kad.calc_pos_from_pad( mod_sw, '1', (5.6, 1.7) )
        ctr_vcc_rght[idx] = kad.calc_pos_from_pad( mod_sw, '1', (0, -4.4) )

        ### Wiring Vias
        for lidx, layer in enumerate( Cu_layers ):
            kad.wire_mod_pads( [
                # cap pad <-> cap pwr via
                (mod_cap, '1', mod_cap, via_cap_vcc[idx], w_led, (Dird, 0, 90, 0), layer),
                (mod_cap, '2', mod_cap, via_cap_gnd[idx], w_led, (Dird, 0, 90, 0), layer),
                # led pad <-> dat via (in/out)
                (mod_led, '37'[lidx], mod_led, via_led_in [idx], w_dat, (Dird, 0, 90), layer),
                (mod_led, '15'[lidx], mod_led, via_led_out[idx], w_dat, (Dird, 0, 90), layer),
            ] )
        kad.wire_mod_pads( [
            # pwr rail vias <-> cap vias
            (mod_sw, wire_via_led_pwr_1st[idx], mod_sw, [via_cap_vcc[idx], via_cap_gnd[idx]][lrx],   w_led, (Dird, 0, 90, r_led), 'B.Cu'),
            (mod_sw, wire_via_led_pwr_2nd[idx], mod_sw, [via_cap_vcc[idx], via_cap_gnd[idx]][lrx^1], w_led, (Dird, ([(0, +1.2)], 0), 90), 'F.Cu'),
            (mod_sw, wire_via_led_pwr_2nd[idx], mod_sw, [via_cap_vcc[idx], via_cap_gnd[idx]][lrx^1], w_led, (Dird, ([(0, -1.2)], 0), 90), 'F.Cu'),
            # cap pwr via pad <-> led pad
            (mod_cap, via_cap_vcc[idx], mod_led, '48'[lrx],   w_led, (ZgZg, 90, 45), Cu_layers[lrx]),
            (mod_cap, via_cap_gnd[idx], mod_led, '26'[lrx^1], w_led, (ZgZg, 90, 45), Cu_layers[lrx^1]),
            # cap pwr via <-> sw pins
            (mod_cap, via_cap_vcc[idx], mod_sw, '54'[lrx],   w_led, (Dird, 0, +38 * lrs), Cu_layers[lrx^1]),
            (mod_cap, via_cap_gnd[idx], mod_sw, '54'[lrx^1], w_led, (Dird, 0, -38 * lrs), Cu_layers[lrx]),
            # led pad <-> sw pins
            (mod_led, '26'[lrx],   mod_sw, '54'[lrx^1], w_led, (Dird, 0, 90), Cu_layers[lrx]),
            (mod_led, '48'[lrx^1], mod_sw, '54'[lrx],   w_led, (Dird, 0, 90), Cu_layers[lrx^1]),
            # led dat via <-> dat connect vias
            (mod_led, [via_led_in[idx], via_led_out[idx]][lrx],   mod_led, wire_via_led_left[idx], w_dat, (Dird, 105, 0), 'F.Cu'),
            (mod_led, [via_led_in[idx], via_led_out[idx]][lrx^1], mod_led, wire_via_led_rght[idx], w_dat, (Dird,  75, 0), 'B.Cu'),
        ] )

    # Row horizontal lines (ROW1-4, LED Pwr)
    row_angle = 90 + 4
    for ridx in range( 1, 5 ):
        for cidx in range( 1, 8 ):
            ncidx = cidx + 1
            if cidx == 6 and ridx == 4:
                ncidx = 8
            left = f'{cidx}{ridx}'
            rght = f'{ncidx}{ridx}'
            if left not in keys.keys() or left == SW_RJ45:
                continue
            if rght not in keys.keys():
                continue
            # route
            if cidx in [2]:# straight
                prm_row = (Dird, 0, 90)
                prm_led = (Dird, 0, 90)
            elif cidx in [3, 4]:
                sangle = {3: 0, 4: 2}[cidx] # small_angle [deg]
                wctr = ctr_row_sw[rght]
                prm_row = (Dird, sangle, 0, kad.inf, wctr)
                prm_led = (Dird, sangle, 0, kad.inf, wctr)
            else:
                ### sw row
                sangle = row_angle - (0 if cidx in [1, 5] else angle_M_Comm)
                lctr = ctr_vcc_rght[left]
                rctr = ctr_vcc_left[rght]
                prm_row = (Dird, 0, ([(0, rctr)], sangle + 180), kad.inf, lctr)
                ### led
                sangle = row_angle - (angle_Inner_Index if cidx in [1] else angle_M_Comm)
                lctr = ctr_led_rght[left]
                rctr = ctr_led_left[rght]
                prm_led = (Dird, ([(180, lctr)], sangle), 0, kad.inf, rctr)
            # print( idx, nidx )
            sw_L = 'SW' + left
            sw_R = 'SW' + rght
            kad.wire_mod_pads( [
                (sw_L, '1', sw_R, '1', w_row, prm_row, 'F.Cu'),
                (sw_L, wire_via_led_rght[left], sw_R, wire_via_led_left[rght], w_dat, prm_led, 'F.Cu'),
                (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led, 'F.Cu'),
                (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led, 'F.Cu'),
            ] )
            if ridx == 4:
                kad.wire_mod_pads( [
                    (sw_L, wire_via_dbnc_vcc[cidx], sw_R, wire_via_dbnc_vcc[ncidx], w_row, prm_row, 'F.Cu'),
                    (sw_L, wire_via_dbnc_gnd[cidx], sw_R, wire_via_dbnc_gnd[ncidx], w_row, prm_row, 'F.Cu'),
                ] )

def wire_col_horz_lines():
    w_row, r_row = 0.7, 2.0 # SW row
    w_col = 0.5

    sep_y = 1.1

    exp_cidx_pad_nets = [
        (0, 4, 'ROW3'),
        (0, 3, 'ROW4'),
        (1, 2, 'COL1'),
        (1, 1, 'ROW2'),
        (2, 28, 'COL2'),
        (2, 27, 'ROW1'),
        (3, 26, 'COL3'),
        (4, 25, 'COL4'),
        (5, 24, 'COL5'),
        (6, 23, 'COL6'),
        (7, 22, 'COL7'),
        (8, 21, 'COL8'),
        (3, 20, 'COLA'),
        (3, 19, 'COLB'),
        # (9, 18, 'ROW5'),
    ]

    mod_exp = 'U1'

    # horizontal col lines
    y_top_wire_via = {}
    y_btm_wire_via = {}
    wire_via_col_horz_set = {}
    for cidx in range( 1, 9 ):
        lrs = get_diode_side( f'{cidx}4' )
        lrx = (lrs + 1) / 2
        mod_cd = f'CD{cidx}'
        # wire vias
        wire_via_col_horz = {}
        n = 0
        for cidx0, pad, net_name in exp_cidx_pad_nets:
            if cidx > cidx0:
                continue
            offset_y = 0.15
            if cidx == 1:
                offset_y += sep_y * 5
            offset_y += sep_y * lrx
            net = kad.get_pad_net( f'U1', f'{pad}' )
            dx = -1.6 * lrs * (1 - lrx)
            if cidx == 1:
                dx -= 2
            dy = offset_y + sep_y * n
            pos = kad.calc_pos_from_pad( mod_cd, '2', (dy, dx) )
            wire_via_col_horz[net_name] = kad.add_via( pos, net, VIA_Size[2] )
            y_top_wire_via[cidx] = offset_y
            y_btm_wire_via[cidx] = dy
            # exp pos
            if cidx == 1 and net_name == 'COL4':
                exp_pos = kad.calc_pos_from_pad( mod_cd, '2', (dy, 8) )
                print( f'{exp_pos = }' )
            # rotenc COLA / COLB
            if cidx == cidx0:
                if net_name == 'COLA' or net_name == 'COLB':
                    lctr = kad.calc_pos_from_pad( mod_cd, '2', (offset_y + sep_y * 9, 0) )
                    if net_name == 'COLA':
                        idx = 11
                        prm = (Dird, 90, 0, kad.inf, lctr)
                    else:
                        idx = 12
                        prm = (Dird, 90, ([(-90, sep_y + 0.2)], 0), kad.inf, lctr)
                    kad.wire_mod_pads( [(mod_cd, wire_via_col_horz[net_name], f'CD{idx}', via_dbnc_row[idx], w_row, prm)] )
            n += 1
        wire_via_col_horz_set[cidx] = wire_via_col_horz
        if cidx == 1:
            kad.wire_mod_pads( [
                (mod_exp, via_exp[2], 'CD1', via_dbnc_row[1], w_row, (Dird, 0, 90, r_row), 'B.Cu'),
            ] )
        else:
            kad.wire_mod_pads( [
                (mod_cd, via_dbnc_row[cidx], mod_cd, wire_via_col_horz_set[cidx][f'COL{cidx}'], w_row, (Dird, 0, 90), 'F.Cu'),
            ] )

    for cidx in range( 1, 8 ):
        cidxL = cidx
        cidxR = cidx + 1
        # route
        mod_cdL = f'CD{cidxL}'
        mod_cdR = f'CD{cidxR}'
        mod_rL = f'R{cidxL}1'
        mod_rR = f'R{cidxR}1'
        ctr_dy = sep_y * 3
        if cidx in [1, 3]:
            lctr = kad.calc_pos_from_pad( mod_cdL, '2', (y_top_wire_via[cidxL] - ctr_dy, -2) )
            rctr = kad.calc_pos_from_pad( mod_cdR, '2', (y_btm_wire_via[cidxR] + ctr_dy, 3) )
            if cidx in[1]:
                prm_row = (Dird, 90, -90, kad.inf, lctr)
            else:
                prm_row = (Dird, 90, -90, kad.inf, rctr)
        elif cidx in [2, 4, 6]:
            lctr = kad.calc_pos_from_pad( mod_cdL, '2', (y_top_wire_via[cidxL] - ctr_dy, 0) )
            rctr = kad.calc_pos_from_pad( mod_cdR, '2', (y_btm_wire_via[cidxR] + ctr_dy, 3) )
            if cidx in [2]:
                prm_row = (Dird, 90, ([(-90, rctr)], -55), kad.inf, lctr)
            else:
                prm_row = (Dird, ([(90, lctr)], 180 - 55), -90, kad.inf, rctr)
        elif cidx in [5, 7]:
            lctr = kad.calc_pos_from_pad( mod_cdL, '2', (y_btm_wire_via[cidxL] + ctr_dy, 0) )
            rctr = kad.calc_pos_from_pad( mod_cdR, '2', (y_top_wire_via[cidxR] - ctr_dy, 0) )
            prm_row = (Dird, ([(90, lctr)], 55), -90, kad.inf, rctr)
        # wires
        if cidxL not in wire_via_col_horz_set: continue
        if cidxR not in wire_via_col_horz_set: continue
        for _, _, net in exp_cidx_pad_nets:
            if net not in wire_via_col_horz_set[cidxL]: continue
            if net not in wire_via_col_horz_set[cidxR]: continue
            wire_via_L = wire_via_col_horz_set[cidxL][net]
            wire_via_R = wire_via_col_horz_set[cidxR][net]
            kad.wire_mod_pads( [(mod_rL, wire_via_L, mod_rR, wire_via_R, w_row, prm_row, 'F.Cu')] )
    for idx, (cidx, pad, net) in enumerate( exp_cidx_pad_nets ):
        if cidx <= 1:
            continue
        if idx not in via_exp:
            continue
        kad.wire_mod_pads( [(mod_exp, via_exp[idx], mod_exp, wire_via_col_horz_set[1][net], w_row, (Strt), 'F.Cu')] )

    for vias in wire_via_col_horz_set.values():
        for via in vias.values():
            pass
            pcb.Delete( via )

def wire_row_vert_lines():
    w_row, r_row = 0.7, 2.0 # SW row

    mod_exp = 'U1'
    kad.wire_mod_pads( [
        (mod_exp, via_exp[0], 'SW13', '1', w_row, (Dird, 0, 0, r_row), 'B.Cu'),
        (mod_exp, via_exp[1], 'SW14', '1', w_row, (Dird, 0, 0, r_row), 'B.Cu'),
        (mod_exp, via_exp[14], 'SW15', '1', w_row, (Dird, 0, 0, r_row)),
    ] )

def wire_mods_led_ends():
    w_led, r_led = 0.7, 2 # LED power
    w_dat = 0.5 # LED dat

    # between rows at right ends
    for left, rght in [('71', '82'), ('83', '84')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        lcnr = kad.calc_pos_from_pad( sw_L, '4', (-0.4, +0.6))
        if left == '71':
            rcnr = kad.calc_pos_from_pad( sw_R, '4', (2.4, 5.4))
            prm_led_dat = (Dird, ([(180, 3)], 120), 90, r_led)
            prm_led_pwr = (Dird, ([(180, lcnr)], 120), ([(180, rcnr)], -90), kad.inf, rcnr)
        elif left == '83':
            rcnr = kad.calc_pos_from_pad( sw_L, '2', (-0.4, -2.8))
            prm_led_dat = (Dird, ([(180, 3.2), (90, 18)], 0), 0, r_led)
            prm_led_pwr = (Dird, ([(180, lcnr), (90, rcnr)], 0), 180, r_led)
        else:
            assert False
        kad.wire_mod_pads( [
            (sw_L, wire_via_led_rght[left], sw_R, wire_via_led_rght[rght], w_dat, prm_led_dat, 'B.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led_pwr, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led_pwr, 'F.Cu'),
        ] )

    # between rows at left ends
    for left, rght in [('22', '13')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        # lcnr = kad.calc_pos_from_pad( sw_L, '4', (-0.4, +0.6))
        # rcnr = kad.calc_pos_from_pad( sw_R, '4', (2.4, 5.4))
        prm_led_dat = (Dird, 0, ([(-90, 3.6), (180, 11.8)], 90), 2)
        prm_led_pwr_12 = (Dird, 0, ([(0, 4), (-90, 2.4), (180, 8.0)], 90), 1)
        prm_led_pwr_21 = (Dird, 0, ([(180, 7.6)], 90), 1)
        kad.wire_mod_pads( [
            (sw_L, wire_via_led_left[left], sw_R, wire_via_led_left[rght], w_dat, prm_led_dat, 'B.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led_pwr_12, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led_pwr_21, 'F.Cu'),
        ] )

    # row4 --> thumb
    for left, rght in [('14', '15')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        lctr = kad.calc_pos_from_pad( 'SW14', '5', (+2, 0))
        rctr = kad.calc_pos_from_pad( 'SW15', '4', (-8, 0))
        prm_led = (Dird, ([(0, lctr)], 60), ([(180, rctr)], 135), kad.inf, lctr)
        kad.wire_mod_pads( [
            (sw_L, wire_via_led_left[left], sw_R, wire_via_led_rght[rght], w_dat, prm_led, 'F.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led, 'F.Cu'),
        ] )

def wire_mods_row_led_thumb():
    w_row, r_row = 0.8, 2 # SW row
    w_led, r_led = 0.7, 1.2 # LED power
    w_dat = 0.5 # LED dat

    # thumbs
    for left, rght in [('15', '25'), ('25', '35')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        prm_row = (Dird, 0, ([(180, 7.4)], 90), r_led)
        prm_led_dat = (Dird, ([(0, 2.4)], 90), ([(-90, 4)], 0), 2)
        prm_led_pwr_1st = (Dird, ([(0, 8.5)], 90), 0, r_led)
        prm_led_pwr_2nd = (Dird, ([(0, 11)], 90), 0, r_led)
        kad.wire_mod_pads( [
            (sw_L, '1', sw_R, '1', w_row, prm_row, 'F.Cu'),
            (sw_L, wire_via_led_left[left], sw_R, wire_via_led_rght[rght], w_dat, prm_led_dat, 'F.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led_pwr_1st, 'B.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led_pwr_2nd, 'F.Cu'),
        ] )

    # thumb and RotEnd
    kad.wire_mod_pads( [
        ('SW35', '1', 'RE1', 'S1', w_row, (Dird, 0, ([(180, 3), (-90, 12)], 0), r_row), 'F.Cu')
    ] )

    # left, rght = '25', '35'
    # sw_L, sw_R = f'SW{left}', f'SW{rght}'
    # lcnr = kad.calc_pos_from_pad( sw_L, '4', (-0.4, +0.6))
    # rcnr = kad.calc_pos_from_pad( sw_L, '2', (-0.4, -4.8))
    # prm_led_dat = (Dird, ([(180, 3.2), (90, 18)], 0), 0, 2)
    # prm_led_pwr = (Dird, ([(180, lcnr), (90, rcnr)], 0), 180, 2)
    # kad.wire_mod_pads( [
    #     # (sw_L, via_led_rght[left], sw_R, via_led_rght[rght], w_dat, prm_led_dat, 'B.Cu'),
    #     (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_2nd[rght], w_led, prm_led_pwr, 'F.Cu'),
    #     (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_1st[rght], w_led, prm_led_pwr, 'F.Cu'),
    # ] )

def remove_temporary_vias():
    for idx, via in wire_via_led_pwr_1st.items():
        pcb.Delete( via )
    for idx, via in wire_via_led_pwr_2nd.items():
        pcb.Delete( via )
    for idx, via in wire_via_led_left.items():
        pcb.Delete( via )
    for idx, via in wire_via_led_rght.items():
        pcb.Delete( via )
    for vias in [wire_via_dbnc_vcc, wire_via_dbnc_gnd]:
        for via in vias.values():
            pcb.Delete( via )

### Ref
def setRefs( board ):
    # GraphicalItems
    for mod in pcb.GetFootprints():
        ref = mod.Reference()
        val = mod.Value()
        val.SetVisible( False )
        # ref.SetVisible( False )
    return
    if board == BDC:
        refs = [
            (6.4, -90, 180, ['J1']),
            (4,  -110,  90, ['U1']),
            (1.8, -90, 180, ['R6']),
            (1.8, +90,   0, ['R7', 'R1', 'C1', 'D1']),
        ]
    else:# key holes
        refs = [ (0, 0, None, ['H{}'.format( idx ) for idx in range( 1, 13 )]) ]
    # sw
    if board in [BDL, BDR]:
        for name in keys:
            refs.append( (1.6, [-90, +90][board], [180, 0][board], ['D' + name]) )
            if name in R2L:
                refs.append( (4.0, [180, 0][board], 0, ['CL' + name]) )
                refs.append( (4.3, [0, 180][board], [-90, +90][board], ['L' + name]) )
            else:
                refs.append( (4.0, [0, 180][board], 180, ['CL' + name]) )
                refs.append( (4.3, [180, 0][board], [+90, -90][board], ['L' + name]) )
    # debounce
    if board in [BDL, BDR]:
        tangle = [180, 0][board]
        for idx in range( 1, 10 ):
            name = str( idx )
            refs.append( (3.3, 180, tangle, ['C' + name + '1']) )
            refs.append( (3.3, 180, tangle, ['R{}1'.format( idx )]) )
            refs.append( (3.3, 180, tangle, ['R{}2'.format( idx )]) )
    for offset_length, offset_angle, text_angle, mod_names in refs:
        for mod_name in mod_names:
            mod = kad.get_mod( mod_name )
            if mod == None:
                continue
            pos, angle = kad.get_mod_pos_angle( mod_name )
            ref = mod.Reference()
            if text_angle == None:
                ref.SetVisible( False )
            else:
                ref.SetTextSize( pcbnew.wxSizeMM( 1.1, 1.1 ) )
                ref.SetThickness( pcbnew.FromMM( 0.18 ) )
                pos_ref = vec2.scale( offset_length, vec2.rotate( - (offset_angle + angle) ), pos )
                ref.SetPosition( pnt.to_unit( vec2.round( pos_ref, 3 ), True ) )
                ref.SetTextAngle( text_angle * 10 )
                ref.SetKeepUpright( False )
    # J3
    if board == BDL:
        pads = ['GND', 'nRST', 'CLK', 'DIO', 'TX', 'RX']
    else:
        pads = []
    for idx, text in enumerate( pads ):
        pos = kad.get_pad_pos( 'J3', '{}'.format( idx + 1 ) )
        pos = vec2.scale( 1.6, vec2.rotate( -90 - J3_angle ), pos )
        kad.add_text( pos, J3_angle, text, ['F.SilkS', 'B.SilkS'][board], (0.8, 0.8), 0.15,
            pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER  )

def main():
    # board type
    filename = pcb.GetFileName()
    # print( f'{filename = }' )
    m = re.search( r'/Mozza([^/]*)\.kicad_pcb', filename )
    assert m

    boardname = m.group( 1 )
    # print( f'{boardname = }' )

    board = None
    for bname, btype in [('C', BDC), ('T', BDT), ('B', BDB), ('M', BDM), ('S', BDS)]:
        if boardname[0] == bname:
            board = btype
            break
    assert board != None

    if board in [BDC, BDM, BDS]:
        kad.add_text( (120, 24), 0, '  Mozza62{} by orihikarna 2023/03/08  '.format( bname ),
            'F.Cu', (1.2, 1.2), 0.2,
            pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER )

    # place & route
    place_key_switchs()
    place_mods()
    if board in [BDC]:
        wire_mods_exp()
        wire_mods_debounce()
        wire_mods_col_diode()
        wire_mods_row_led()
        wire_col_horz_lines()
        wire_row_vert_lines()
        wire_mods_led_ends()
        wire_mods_row_led_thumb()
        remove_temporary_vias()

    setRefs( board )
    drawEdgeCuts( board )
    return

    for name in keys.keys():
        col = int( name[0] )
        row = int( name[1] )
        # if col == 8:
        #     if board == BDL:
        #         R2L.append( name )
        #     elif board == BDR:
        #         L2R.append( name )
        # else:
        #     if row in [1, 3]:
        #         L2R.append( name )
        #     else:
        #         R2L.append( name )

    # return

    ### zones
    zones = []
    if board in [BDC, BDM, BDS]:
        add_zone( 'GND', 'F.Cu', make_rect( (PCB_Width, PCB_Height) ), zones )
        add_zone( 'GND', 'B.Cu', make_rect( (PCB_Width, PCB_Height) ), zones )

    # draw top & bottom patterns
    if board in [BDT, BDB, BDS]:
        draw_top_bottom( board, sw_pos_angles )



if __name__=='__main__':
    kad.removeDrawings()
    kad.removeTracksAndVias()
    main()
    pcbnew.Refresh()
