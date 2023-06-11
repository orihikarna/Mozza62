import pcbnew
import json
import math
import re
from kadpy import kad, pnt, vec2, mat2, distance as dist

import importlib

importlib.reload(kad)
importlib.reload(pnt)
importlib.reload(vec2)
importlib.reload(mat2)

kad.UnitMM = True
kad.PointDigits = 3

pcb = pcbnew.GetBoard()

# alias
Strt = kad.Straight  # Straight
Dird = kad.Directed  # Directed + Offsets
ZgZg = kad.ZigZag  # ZigZag

Line = kad.Line
Linear = kad.Linear
Round = kad.Round
BezierRound = kad.BezierRound
LinearRound = kad.LinearRound
Spline = kad.Spline


# in mm
VIA_Size = [(1.2, 0.6), (1.15, 0.5), (0.92, 0.4), (0.8, 0.3)]

mod_props = {}

PCB_Width = 189
PCB_Height = 132

keys = {
    '11': [91.452, -41.958, 16.910, 15.480, -21.2],  # r
    '13': [89.129, -60.205, 17.000, 17.000, -21.2],  # |
    '14': [85.528, -77.044, 17.000, 17.000, -21.2],  # E
    '15': [64.347, -125.667, 22.000, 17.000, -244.0],  # R
    '21': [112.294, -37.720, 17.000, 17.000, -6.0],  # &
    '22': [108.740, -54.440, 17.000, 17.000, -6.0],  # Y
    '23': [105.186, -71.160, 17.000, 17.000, -6.0],  # H
    '24': [101.632, -87.880, 17.000, 17.000, -6.0],  # N
    '25': [83.140, -120.626, 22.000, 17.000, -256.0],  # S
    '31': [129.201, -39.497, 17.000, 17.000, -6.0],  # '
    '32': [125.647, -56.217, 17.000, 17.000, -6.0],  # U
    '33': [122.093, -72.937, 17.000, 17.000, -6.0],  # J
    '34': [118.539, -89.657, 17.000, 17.000, -6.0],  # M
    '35': [102.571, -119.602, 22.000, 17.000, -268.0],  # S
    '41': [149.855, -44.443, 17.000, 17.000, -24.0],  # (
    '42': [145.678, -61.192, 17.000, 17.000, -24.0],  # I
    '43': [141.502, -77.942, 17.000, 17.000, -24.0],  # K
    '44': [137.326, -94.691, 17.000, 17.000, -24.0],  # <
    '51': [167.274, -52.219, 17.000, 17.000, -26.0],  # )
    '52': [162.516, -68.813, 17.000, 17.000, -26.0],  # O
    '53': [157.758, -85.406, 17.000, 17.000, -26.0],  # L
    '54': [153.000, -102.000, 17.000, 17.000, -26.0],  # >
    '61': [182.380, -65.072, 17.000, 17.000, -8.0],
    '62': [177.665, -81.576, 17.000, 17.000, -8.0],  # P
    '63': [172.950, -98.081, 17.000, 17.000, -8.0],  # +
    '64': [167.402, -119.156, 22.800, 17.000, -22.0],  # ?
    '65': [133.134, -125.721, 13.700, 12.700, -186.0],  # R
    '71': [198.220, -74.508, 17.000, 17.000, -8.0],  # =
    '72': [193.506, -91.013, 17.000, 17.000, -8.0],  # `
    '73': [188.791, -107.517, 17.000, 17.000, -8.0],  # *
    '82': [209.347, -100.449, 17.000, 17.000, -8.0],  # [
    '83': [204.632, -116.954, 17.000, 17.000, -8.0],  # ]
    '84': [188.971, -130.907, 26.000, 17.000, -22.0],  # _
}

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
    None,
    dx_Inner,
    dx_Index, dx_Index,
    dx_Comma,
    dx_Dot,
    dx_Pinky, dx_Pinky, dx_Pinky,
]

unit = 17
Lx = unit * 2.97
Ly = unit * 2.97 * (math.sqrt(3)/2)
org = None


def is_SW(idx: str):
    return idx not in [SW_RJ45, SW_RotEnc]


def is_L2R_key(idx: str):
    row = idx[1]
    return row in '13' or idx in ['25']


def get_diode_side(idx: str):
    return -1 if idx[0] in '123' else +1


def get_top_row_idx(cidx: int):
    if cidx == 1:
        return 3
    elif cidx == 8:
        return 2
    else:
        return 1


def get_btm_row_idx(cidx: int):
    if cidx == 7:
        return 3
    else:
        return 4


# Board Type
# class Board(Enum):
BDT = 0  # Top
BDS = 1  # Spacer
BDC = 4  # Circuit
BDM = 2  # Middle
BDB = 3  # Bottom

# Edge.Cuts size
Edge_CX, Edge_CY = 0, 0
Edge_W, Edge_H = 0, 0


def add_zone(net_name, layer_name, rect):
    layer = pcb.GetLayerID(layer_name)
    zone, poly = kad.add_zone(rect, layer, net_name)
    #
    settings = pcb.GetZoneSettings()
    settings.m_ZoneClearance = pcbnew.FromMils(12)
    pcb.SetZoneSettings(settings)
    #
    zone.SetMinThickness(pcbnew.FromMils(16))
    # zone.SetThermalReliefGap( pcbnew.FromMils( 12 ) )
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMils(16))
    # zone.Hatch()
    #
    # polys.append( poly )


def draw_edge_cuts(board):
    def make_corners(key_cnrs):
        corners = []
        for mod, offset, dangle, cnr_type, prms in key_cnrs:
            if False:
                pos = kad.calc_pos_from_mod(mod, offset)
                angle = kad.get_mod_angle(mod)
            else:
                _pos, angle, layer = mod_props[mod]
                vec = offset
                if layer == 'B.Cu':
                    vec = (vec[0], -vec[1])
                pos = vec2.mult(mat2.rotate(angle), vec, _pos)
            corners.append([(pos, -angle + dangle), cnr_type, prms])
        return corners

    width = 0.12

    # region outer edge
    Radius = Ly
    cnrs = [
        ((vec2.add(org, (Lx * (-2 + 1/2), -Ly)), +120), Round, [Radius]),
        ((vec2.add(org, (0, Ly)), 0), Round, [Radius]),
        ((vec2.add(org, (Lx * (+2 - 1/2), -Ly)), -120), Round, [Radius]),
        ((vec2.add(org, (0, -Ly*2)), 180), Round, [Radius]),
    ]
    kad.draw_closed_corners(cnrs, 'Edge.Cuts', width)
    if False:  # PCB Size
        x0, x1 = +1e6, -1e6
        y0, y1 = +1e6, -1e6
        for (pos, _), _, _ in corners:
            x, y = pos
            x0 = min(x0, x)
            x1 = max(x1, x)
            y0 = min(y0, y)
            y1 = max(y1, y)
        global Edge_CX, Edge_CY
        global Edge_W, Edge_H
        Edge_CX, Edge_CY = (x0 + x1) / 2, (y0 + y1) / 2
        Edge_W, Edge_H = x1 - x0, y1 - y0
        if True:
            # print( 'Edge: (CX, CY) = ({:.2f}, {:.2f})'.format( Edge_CX, Edge_CY ) )
            print('Edge: (W, H) = ({:.2f}, {:.2f})'.format(Edge_W, Edge_H))
    # endregion

    midcnrs_set = []
    midarcs = []
    # region key holes
    for idx in sorted(keys.keys()):
        if not is_SW(idx):
            continue
        mod_sw = f'SW{idx}'
        for bd, sz, r in [(BDT, 13.96, 0.9)]:  # , (BDS, 15, 1.6)]:
            hsz = sz / 2
            cnrs = [
                (mod_sw, (0, -hsz),   0, BezierRound, [r]),
                (mod_sw, (+hsz, 0),  90, BezierRound, [r]),
                (mod_sw, (0, +hsz), 180, BezierRound, [r]),
                (mod_sw, (-hsz, 0), 270, BezierRound, [r]),
            ]
            midcnrs_set.append((make_corners(cnrs), [bd]))
        pos = mod_props[mod_sw][0]
        midarcs.append((pos, 5.2/2, [BDB]))
    # endregion
    # region RJ45
    mod_rj = 'J1'
    r = 1.4
    w = 9
    cnrs = [
        (mod_rj, (0, +14.6),   0, BezierRound, [r]),
        (mod_rj, (+w, 0),  90, BezierRound, [r]),
        (mod_rj, (0, -2), 180, BezierRound, [r]),
        (mod_rj, (-w, 0), 270, BezierRound, [r]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDT, BDS]))
    for sign in [+1, -1]:
        dx = 5.715 * sign
        dy = 8.89
        hw = (2.0 + 0.4 + 1.27)/2
        hh = (3.4 + 0.4)/2
        r = 1.5
        cnrs = [
            (mod_rj, (dx, dy+hh),   0, BezierRound, [r]),
            (mod_rj, (dx+hw, dy),  90, BezierRound, [r]),
            (mod_rj, (dx, dy-hh), 180, BezierRound, [r]),
            (mod_rj, (dx-hw, dy), 270, BezierRound, [r]),
        ]
        midcnrs_set.append((make_corners(cnrs), [BDB]))
    # endregion
    # region U1, U2
    mod_exp = 'U1'
    r = 6.5
    cnrs = [
        (mod_exp, (0, -5),   0, BezierRound, [r]),
        (mod_exp, (+7, 3),  90, BezierRound, [r]),
        (mod_exp, (0, 10), 180, BezierRound, [r]),
        (mod_exp, (-9, 3), 270, BezierRound, [2]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDM]))
    r = 2
    cnrs = [
        (mod_exp, (0, -5),   0, BezierRound, [r]),
        (mod_exp, (+5, 0),  90, BezierRound, [r]),
        (mod_exp, (0, +5), 180, BezierRound, [r]),
        (mod_exp, (-5, 0), 270, BezierRound, [2]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDS]))
    # endregion
    # region RotEnc
    mod_re = 'RE1'
    r = 1.4
    cnrs = [
        (mod_re, (0, -8.0),   0, BezierRound, [r]),
        (mod_re, (4, -6.5),  90, BezierRound, [r]),
        (mod_re, (8, -5.0),   0, BezierRound, [r]),
        ('D65', (0, 2),     180, BezierRound, [r]),
        (mod_re, (8, +5.0), 180, BezierRound, [r]),
        (mod_re, (4, +6.5),  90, BezierRound, [r]),
        (mod_re, (0, +8.0), 180, BezierRound, [r]),
        #
        (mod_re, (-4, +6.5), 270, BezierRound, [r]),
        (mod_re, (-8, +5.0), 180, BezierRound, [r]),
        ('CD11', (0, -2),      0, BezierRound, [r]),
        (mod_re, (-8, -5.0),   0, BezierRound, [r]),
        (mod_re, (-4, -6.5), 270, BezierRound, [r]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDM]))
    #
    r = 2
    w, h = 9, 7.6
    cnrs = [
        (mod_re, (0, -h),   0, BezierRound, [r]),
        (mod_re, (+w, 0),  90, BezierRound, [r]),
        (mod_re, (0, +h), 180, BezierRound, [r]),
        (mod_re, (-w, 0), 270, BezierRound, [r]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDS, BDT]))
    #
    for sign in [+1, -1]:
        dy = 5.6 * sign
        hw = (2.0 + 0.8)/2
        hh = (2.0 + 0.4 + 1.6)/2
        r = 1.0
        cnrs = [
            (mod_re, (0, dy-hh),   0, BezierRound, [r]),
            (mod_re, (+hw, dy),   90, BezierRound, [r]),
            (mod_re, (0, dy+hh), 180, BezierRound, [r]),
            (mod_re, (-hw, dy),  270, BezierRound, [r]),
        ]
        midcnrs_set.append((make_corners(cnrs), [BDB]))
    # endregion
    mod_rj = 'J1'
    # region switch area (separation)
    hsz = 7.5
    d_sw = hsz
    r = 1
    cnrs = [
        ('SW21', (0, d_sw), 180, BezierRound, [r]),
        ('SW41', (0, d_sw), 180, BezierRound, [r]),
        ('SW51', (0, d_sw), 180, BezierRound, [r]),
        ('SW61', (hsz-0.5, d_sw+r+1.5), 270, BezierRound, [r]),
        ('SW61', (0, d_sw), 180, BezierRound, [r]),
        ('SW71', (8.5, d_sw+r+2.5), 270, BezierRound, [r]),
        ('SW71', (0, d_sw), 180, BezierRound, [r]),
        # right
        ('SW71', (-d_sw, 0), 270, BezierRound, [r]),
        ('SW82', (0, d_sw), 180, BezierRound, [r]),
        ('SW82', (-d_sw, 0), 270, BezierRound, [r]),
        ('SW83', (-8, -8), 310, BezierRound, [r]),
        # bottom right
        ('SW84', (0, -d_sw), 0, BezierRound, [r]),
        ('SW64', (d_sw, 0), 90, BezierRound, [r]),
        ('SW54', (0, -d_sw), 0, BezierRound, [r]),
        ('SW44', (0, -d_sw), 0, BezierRound, [r]),
        ('SW24', (0, -d_sw), 0, BezierRound, [r]),
        ('SW24', (d_sw, -4), 90, BezierRound, [r]),
        # bottom left
        ('SW14', (0, -d_sw), 0, BezierRound, [r]),
        # left
        ('SW13', (d_sw, 0), 90, BezierRound, [r]),
        ('SW13', (0, d_sw), 180, BezierRound, [r]),
        # top left
        ('SW13', (-d_sw+0.5, 9), 90, BezierRound, [r]),
        ('SW21', (d_sw, 0), 90, BezierRound, [r]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDS]))
    # endregion
    d = 2.4
    hsz = 8.5
    d_sw = hsz + d
    # region switch area (middle)
    r = 2
    d_dbnc = 3
    cnrs = [
        ('SW21', (0, d_sw), 180, BezierRound, [16]),
        ('SW41', (0, d_sw), 180, BezierRound, [r]),
        ('SW51', (0, d_sw), 180, BezierRound, [r]),
        ('SW61', (4, d_sw+r+1.5), 270, BezierRound, [r]),
        ('SW61', (0, d_sw), 180, BezierRound, [r]),
        ('SW71', (hsz-d, d_sw+r+2.5), 270, BezierRound, [r]),
        ('SW71', (0, d_sw), 180, BezierRound, [r]),
        # right
        ('SW71', (-d_sw, 0), 270, BezierRound, [8]),
        ('SW82', (0, d_sw), 180, BezierRound, [r]),
        ('SW82', (-d_sw, 0), 270, BezierRound, [r]),
        ('SW83', (-8, -8), 310, BezierRound, [r]),
        # bottom right
        ('R81', (d_dbnc, -2), 90, BezierRound, [r]),
        ('R81', (1.8, 4), 90 + 30, BezierRound, [r]),
        ('R71', (d_dbnc, 0), 90, BezierRound, [r]),
        ('R61', (0, 6), 90 + 45, BezierRound, [r]),
        #
        ('R51', (d_dbnc, 0), 90, BezierRound, [r]),
        ('R41', (d_dbnc, 0), 90, BezierRound, [r]),
        ('R31', (d_dbnc, 0), 90, BezierRound, [r]),
        ('R21', (0, 8), 90 + 40, BezierRound, [r]),
        # bottom left
        ('R11', (d_dbnc, -2), 90, BezierRound, [r]),
        ('R11', (0, 6), 90 + 45, BezierRound, [r]),
        # left
        ('SW13', (d_sw, 0), 90, BezierRound, [r]),
        # top left
        (mod_rj, (9, 12.6), 0, BezierRound, [r]),
        ('C3', (0, -1.5), 0, BezierRound, [r]),
        # (mod_rj, (7, -4), 120, BezierRound, [r]),
    ]
    midcnrs_set.append((make_corners(cnrs), [BDM]))
    # endregion
    # region thumb key hole
    for bd, d, r in [(BDM, 2.4, 4)]:  # , (BDS, 0, 1.6)]:
        d_sw = hsz + d
        cnrs = [
            ('SW15', (0, d_sw), 180, BezierRound, [r]),
            ('SW15', (-d_sw, 4), 270, BezierRound, [r]),
            ('SW25', (-d_sw, 4), 270, BezierRound, [r]),
            ('SW35', (-d_sw, 0), 270, BezierRound, [r]),
            ('SW35', (0, -d_sw),   0, BezierRound, [r]),
            ('SW35', (+d_sw, 0),  90, BezierRound, [r]),
            ('SW25', (+d_sw, 7),  90, BezierRound, [r]),
            ('SW15', (+d_sw, 5),  90, BezierRound, [r]),
        ]
        midcnrs_set.append((make_corners(cnrs), [bd]))
    # endregion
    for midcnrs, boards in midcnrs_set:
        for bd in boards:
            if board == bd:
                kad.draw_closed_corners(midcnrs, 'Edge.Cuts', width)
            elif board == BDC:
                layer = f'User.{bd+1}'
                kad.draw_closed_corners(midcnrs, layer, width * 2)
    for ctr, rad, boards in midarcs:
        pos = vec2.add(ctr, (rad, 0))
        for bd in boards:
            if board == bd:
                kad.add_arc(ctr, pos, 360, 'Edge.Cuts', width)
            elif board == BDC:
                layer = f'User.{bd+1}'
                kad.add_arc(ctr, pos, 360, layer, width * 2)


def draw_bottom():
    layer = 'F.Cu'

    if True: # rulearea (keepout)
        div = 12
        # div = 3
        r = Ly/div * 0.12
        d = Ly/div * 0.24
        def add_onigiri_area(pos, angle, layer):
            pnts = []
            for idx, base0 in enumerate([0, 120, 240]):
                base = base0 + angle
                ctr = vec2.scale(d, vec2.rotate(base + 60))
                for deg in range(0, 120 + 1, 12):
                    rad = vec2.scale(r, vec2.rotate(base + deg))
                    pnts.append(vec2.add(ctr, rad))
            pnts = [vec2.add(pos, pt) for pt in pnts]
            pnts = [kad.pnt.to_unit(vec2.round(pt, kad.PointDigits), kad.UnitMM) for pt in pnts]
            area = pcb.AddArea(None, GND.GetNetCode(), pcb.GetLayerID(layer), pnts[0], pcbnew.ZONE_BORDER_DISPLAY_STYLE_DIAGONAL_EDGE)
            area.SetIsRuleArea(True)
            # area.SetDoNotAllowTracks(no_tracks)
            # area.SetDoNotAllowVias(no_vias)
            area.SetDoNotAllowCopperPour(True)
            poly = area.Outline()
            for idx, pt in enumerate(pnts):
                if idx == 0:
                    continue
                poly.Append(pt[0], pt[1])
        for y in range(-2*div, div+1):
            for x in range(-4*div, 4*div+1):
                parity = (x + y) % 2
                sign = parity * 2 - 1
                # pos = vec2.add(org, (Lx/div/2 * x, d/3 * sign + Ly/div*(y - 0.5)))
                pos = vec2.add(org, (Lx/div/2 * x, Ly/div/3*parity + Ly/div*(y - 0.5)))
                layer = Cu_layers[parity]
                # layer = Cu_layers[0]
                add_onigiri_area(pos, 90 * sign, layer)
        return

    for t in range(0, int(Ly*3/2), 3):
        s = t / (Ly*3/2)
        width = (0.2 + 0.8 * (1-abs(1 -2*s))) * 2
        Radius = max(Ly - t, 0)
        cnrs = [
            ((vec2.add(org, vec2.scale(Ly*3/2 - t, vec2.rotate(-150), (-Lx/4, -Ly/2))), +120), Round, [Radius]),
            ((vec2.add(org, (0, Ly - t)), 0), Round, [Radius]),
            ((vec2.add(org, vec2.scale(Ly*3/2 - t, vec2.rotate(-30), (+Lx/4, -Ly/2))), -120), Round, [Radius]),
            ((vec2.add(org, (0, -Ly*2 + t)), 180), Round, [Radius]),
        ]
        kad.draw_closed_corners(cnrs, layer, width)
    return

    width = 1.0

    Radius = Ly
    ctrs = [(-Lx, 0), (+Lx, 0), (+Lx/2, -Ly), (-Lx/2, -Ly)]
    inits = [90, -30, -90, -150]
    angles = [120, 120, 60, 60]
    dirs = [-30, -150, +120, +60]
    for idx, ctr in enumerate(ctrs):
        vec = vec2.rotate(dirs[idx])
        for t in range(0, int(Radius), 5):
            _ctr = vec2.add(org, ctr)
            # _ctr = vec2.scale(t, vec, _ctr)
            _pos = vec2.scale(Radius - t, vec2.rotate(inits[idx]), _ctr)
            kad.add_arc(_ctr, _pos, angles[idx], layer, width)
    return
    if board in [BDT, BDS]:  # keysw holes
        length = 13.94 if board == BDT else 14.80
        for sw_pos, angle in sw_pos_angles:
            corners = []
            for i in range(4):
                deg = i * 90 + angle
                pos = vec2.scale(length / 2.0, vec2.rotate(deg), sw_pos)
                # corners.append( [(pos, deg + 90), Round, [0.9]] )
                corners.append([(pos, deg + 90), BezierRound, [0.9]])
            kad.draw_closed_corners(corners, 'Edge.Cuts', 0.1)

    if board == BDS:
        return

    if False:  # screw holes
        for prm in holes:
            x, y, angle = prm
            ctr = (x, y)
            kad.add_arc(ctr, vec2.add(ctr, (2.5, 0)), 360, 'Edge.Cuts', 0.1)
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
    for n in range(1, len(anchors)):
        anchor_a = anchors[n-1]
        anchor_b = anchors[n]
        pos_a, angle_a = sw_pos_angles[anchor_a[0]]
        pos_b, angle_b = sw_pos_angles[anchor_b[0]]
        angle_a += anchor_a[1]
        angle_b += anchor_b[1]
        if abs(angle_a - angle_b) > 1:
            vec_a = vec2.rotate(angle_a + 90)
            vec_b = vec2.rotate(angle_b + 90)
            ctr, _, _ = vec2.find_intersection(pos_a, vec_a, pos_b, vec_b)
            if n == 1:
                angle_a += (angle_a - angle_b) * 1.1
            elif n + 1 == len(anchors):
                angle_b += (angle_b - angle_a) * 1.5
            if False:
                layer = 'F.Fab'
                width = 1.0
                # print( ctr, ka, kb )
                kad.add_line(ctr, pos_a, layer, width)
                kad.add_line(ctr, pos_b, layer, width)
        else:
            ctr = None
        ctr_pos_angle_vec.append((ctr, pos_a, angle_a, pos_b, angle_b))
    # return

    # read distance data
    board_type = {BDT: 'T', BDB: 'B'}[board]
    dist_image = load_distance_image('/Users/akihiro/repos/Hermit/Hermit{}/Edge_Fill.txt'.format(board_type))

    # draw lines
    pos_dummy = [None, None]
    pitch = 2.0
    nyrange = range(-559, 888, 16)
    width0, width1 = 0.3, 1.3
    for ny in nyrange:
        y = ny * 0.1
        uy = float(ny - nyrange[0]) / float(nyrange[-1] - nyrange[0])
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
        pos_base = vec2.mult(mat2.rotate(-angle_base), (0, y), pos_base)
        # control points for one horizontal line
        pos_angles = [(pos_base, angle_base)]
        for dir in [-1, +1]:
            idx = idx_base
            pos_a, angle_a = pos_base, angle_base
            while 0 < idx and idx < len(ctr_pos_angle_vec):
                idx2 = idx + dir
                if dir == -1:
                    ctr, _, angle_b, _, angle_a = ctr_pos_angle_vec[idx2]
                else:  # dir == +1:
                    ctr, _, angle_a, _, angle_b = ctr_pos_angle_vec[idx]
                idx = idx2
                #
                vec_b = vec2.rotate(angle_b + 90)
                pos_b = vec2.scale(-vec2.distance(pos_a, ctr), vec_b, ctr)
                pos_angles.append((pos_b, angle_b))
                pos_a = pos_b
            if dir == -1:
                pos_angles.reverse()

        # one horizontal line with nearly constant pitch
        curv = []
        for idx, (pos_b, angle_b) in enumerate(pos_angles):
            if idx == 0:
                curv.append(pos_b)
                continue
            if False:
                curv.append(pos_b)
            else:
                pos_a, angle_a = pos_angles[idx-1]
                # pnts = kad.calc_bezier_round_points( pos_a, vec2.rotate( angle_a ), pos_b, vec2.rotate( angle_b + 180 ), 8 )
                pnts = kad.calc_bezier_corner_points(pos_a, vec2.rotate(angle_a), pos_b, vec2.rotate(angle_b + 180), pitch, ratio=0.8)
                for idx in range(1, len(pnts)):
                    curv.append(pnts[idx])

        gap = 0.5
        if True:  # divide if close to the edge
            div = 10
            thick = width1 / 2.0 + gap
            curv2 = []
            for idx, pnt in enumerate(curv):
                dist = get_distance(dist_image, pnt)
                if idx == 0:
                    prev_pnt = pnt
                    prev_dist = dist
                    curv2.append(pnt)
                    continue
                if max(dist, prev_dist) > -pitch and min(dist, prev_dist) < thick:
                    vec = vec2.sub(pnt, prev_pnt)
                    for i in range(1, div):
                        curv2.append(vec2.scale(i / float(div), vec, prev_pnt))
                curv2.append(pnt)
                prev_pnt = pnt
                prev_dist = dist
            curv = curv2

        # draw horizontal line avoiding key / screw holes
        w_thin = 0.25
        thick_thin = w_thin / 2.0 + gap
        for lidx, layer in enumerate(['F.Cu', 'B.Cu']):
            if lidx == 0:
                w = width0 + (width1 - width0) * uy
            else:
                w = width1 + (width0 - width1) * uy
            thick = w / 2.0 + gap
            num_lines = int(math.ceil(w / (w_thin * 0.96)))
            line_sep = (w - w_thin) / (num_lines - 1)
            line_lefts = [None for _ in range(num_lines)]
            line_rights = [None for _ in range(num_lines)]
            last_pnt = [None for _ in range(num_lines)]
            for cidx in range(1, len(curv)):
                pnt_a = curv[cidx-1]
                pnt_b = curv[cidx]
                if False:
                    kad.add_line(pnt_a, pnt_b, layer, w)
                    # kad.add_arc( pnt_a, vec2.add( pnt_a, (w / 2, 0) ), 360, layer, 0.1 )
                    continue
                vec_ba = vec2.sub(pnt_b, pnt_a)
                unit_ba = vec2.normalize(vec_ba)[0]
                norm_ba = (unit_ba[1], -unit_ba[0])
                # multiple horizontal lines
                single = True
                lines = []
                for m in range(num_lines):
                    delta = line_sep * m + w_thin / 2.0 - w / 2.0
                    q0 = vec2.scale(delta, norm_ba, pnt_a)
                    q1 = vec2.scale(delta, norm_ba, pnt_b)
                    d0 = get_distance(dist_image, q0)
                    d1 = get_distance(dist_image, q1)
                    if min(d0, d1) < thick:
                        single = False
                    if d0 >= thick_thin and d1 >= thick_thin:  # single line
                        pass
                    elif d0 >= thick_thin:
                        while d1 < thick_thin - 0.01:
                            diff = thick_thin - d1
                            q1 = vec2.scale(-diff * 0.94, unit_ba, q1)
                            d1 = get_distance(dist_image, q1)
                        connect_line_ends(line_lefts, line_rights, cidx, q1, m, layer, w_thin)
                    elif d1 >= thick_thin:
                        while d0 < thick_thin - 0.01:
                            diff = thick_thin - d0
                            q0 = vec2.scale(+diff * 0.94, unit_ba, q0)
                            d0 = get_distance(dist_image, q0)
                        connect_line_ends(line_rights, line_lefts, cidx, q0, m, layer, w_thin)
                    else:  # no line
                        q0 = None
                        q1 = None
                    if q0 and q1:
                        lines.append((q0, q1))
                        if last_pnt[m]:
                            d = vec2.distance(last_pnt[m], q0)
                            if 0.01 < d and d < 0.8:  # close tiny gap
                                kad.add_line(last_pnt[m], q0, layer, w_thin)
                        last_pnt[m] = q1

                if single:
                    kad.add_line(pnt_a, pnt_b, layer, w)
                    if not pos_dummy[lidx] and w > 1.1:
                        pos_dummy[lidx] = pnt_a
                else:
                    for (q0, q1) in lines:
                        kad.add_line(q0, q1, layer, w_thin)
                # clear line_ends when single or no line
                if single or len(lines) == 0:
                    for m in range(num_lines):
                        line_lefts[m] = None
                        line_rights[m] = None
    kad.set_mod_pos_angle('P1', pos_dummy[0], 0)
    kad.set_mod_pos_angle('P2', pos_dummy[1], 0)


Cu_layers = ['F.Cu', 'B.Cu']

GND = pcb.FindNet('GND')
VCC = pcb.FindNet('3V3')

via_size_pwr = VIA_Size[1]
via_size_dat = VIA_Size[2]
via_size_gnd = VIA_Size[3]

# switch positions
sw_pos_angles = []


# Set key positios
def place_key_switches():
    for idx in sorted(keys.keys()):
        px, py, _w, _h, angle = keys[idx]
        sw_pos = (px, -py)
        sw_pos_angles.append((sw_pos, 180 - angle))

        if idx == SW_RJ45:
            kad.set_mod_pos_angle('J1', vec2.scale(6.2, vec2.rotate(-angle - 90), sw_pos), angle + 180)
            continue
        if idx == SW_RotEnc:
            mod_re = 'RE1'
            kad.set_mod_pos_angle(mod_re, sw_pos, angle + 180)
            kad.add_via(kad.calc_pos_from_pad(mod_re, 'S2', (0, -2.54)), GND, via_size_gnd)
            continue

        mod_sw = f'SW{idx}'
        mod_led = f'L{idx}'
        mod_cap = f'C{idx}'
        mod_dio = f'D{idx}'

        is_L2R = is_L2R_key(idx)
        diode_sign = get_diode_side(idx)

        kad.move_mods(sw_pos, angle + 180, [
            (mod_sw, (0, 0), 0),
            (mod_led, (0, 4.7), 0 if is_L2R else 180),
            (mod_cap, (0, 8.5), 180 if is_L2R else 0),
            (mod_dio, (5.4 * diode_sign, 0.8), 90),
        ])
        kad.wire_mod_pads([(mod_sw, '2', mod_sw, '3', 0.4, (Dird, [(-90, 0.12), 0], 90, 0), 'F.Cu')])

        # GND vias
        def _add_gnd_via(pad, pos):
            kad.add_via(kad.calc_pos_from_pad(mod_sw, pad, pos), GND, via_size_gnd)

        col, row = idx
        # above LED lines
        if idx not in ['13']:
            dx_col = 0 if idx[1] == '5' else dx_cols[int(idx[0])]
            if idx not in ['21']:
                _add_gnd_via('5', (-dx_col * 0.6, 5.2))
            if idx not in ['82']:
                _add_gnd_via('4', (-dx_col * 0.6, 5.2))
        # next to col
        if col != '1' and row != '5':
            if idx[0] in ['2', '3']:
                _add_gnd_via('4', (-3.5, +0.7))
                _add_gnd_via('2', (-3.3, -1.1))
            elif idx[0] in ['4', '5']:
                _add_gnd_via('5', (+3.5, +0.7))
                _add_gnd_via('3', (+3.3, -1.1))
            elif idx[0] in ['6', '7', '8']:
                _add_gnd_via('5', (+3.5, 0))
        # SW '3
        _add_gnd_via('2', (-0.4, 1.8))
        _add_gnd_via('3', (+0.4, 1.8))
        # thumb row
        if row == '5':
            if col not in ['3']:
                _add_gnd_via('4', ([-2.4, -6.6][int(col)-1], 0))
            _add_gnd_via('5', (6.2, 0))
            _add_gnd_via('3', (6.2, 2))

        for i, sign in enumerate([+1, -1]):
            # debounce line
            if row == '4' or idx in ['63', '73', '83']:
                _add_gnd_via('1', (2.6 * sign, 0))
            # below LED
            pad = '54'[i]
            _add_gnd_via(pad, (+0.4 * sign, -1.8))
            _add_gnd_via(pad, (-2.0 * sign, -3.0))
            # right end
            if idx in ['83']:
                _add_gnd_via('1', (-11.4, 5 + 4.6 * sign))


def place_mods():
    # RJ45 connector
    pos, angle = kad.get_mod_pos_angle('J1')
    for side in range(2):
        sign_side = [+1, -1][side]
        for idx in range(4):
            pad = 2 * idx + 2  # 2, 4, 6, 8
            dx = 1.27 * (2 * idx - 3)  # -3, -1, +1, +3
            kad.move_mods(pos, angle - 90, [(f'JP{"FB"[side]}{pad}', (3.8, -dx * sign_side), 0)])
    pos = kad.calc_relative_vec('J1', (0, 6), kad.get_pad_pos('J1', '9'))
    kad.move_mods(pos, angle - 90, [('C3', (0, -6), 0)])

    # DL1
    mod_sw = 'SW21'
    _, angle = kad.get_mod_pos_angle(mod_sw)
    pos = kad.calc_pos_from_pad(mod_sw, '5', (1, 4))
    kad.set_mod_pos_angle('DL1', pos, angle)

    # Debounce RRCs
    for cidx in range(1, 9):
        idx = f'{cidx}4'
        lrs = get_diode_side(idx)
        mod_sw = f'SW{idx}'
        if cidx == 7:
            mod_sw = 'SW64'
            dx, dy = 11.0, -9.6
        else:
            dx, dy = 11.0, 1.2 * lrs
        pos, angle = kad.get_mod_pos_angle(mod_sw)
        kad.move_mods(pos, angle + 90, [
            (None, (dx, dy), 0, [
                (f'CD{cidx}', (0, -2.2 * lrs), 0),
                (f'R{cidx}1', (0,  0), 0),
                (f'R{cidx}2', (0, +2.2 * lrs), 180),
            ]),
        ])

    # RotEnc
    _, angle = kad.get_mod_pos_angle('RE1')
    for i in range(2):
        sgn = [+1, -1][i]
        cidx = [11, 12][i]
        pos = kad.calc_pos_from_pad('RE1', 'AB'[i], (-5, 0 * sgn))
        kad.move_mods(pos, angle + 90 * sgn, [
            (f'CD{cidx}', (0, -1.6 * sgn), 0),
            (f'R{cidx}1', (0,  0), 0),
            (f'R{cidx}2', (0, +1.6 * sgn), 0),
        ])

    # RotEnc diode
    pos = kad.get_mod_pos('RE1')
    kad.move_mods(pos, angle, [(f'D{SW_RotEnc}', (10.5, 0), 90)])

    # I/O expanders
    exp_pos = kad.calc_pos_from_pad('CD1', '2', (11.6, 8))
    angle = kad.get_mod_angle('SW14')
    kad.move_mods(exp_pos, angle, [
        (None, (0, 0), 90, [
            ('U1', (0, 0), 0),
            ('U2', (0, 0), 180),
            ('C1', (-5.4, 2), -90),
            ('C2', (+5.4, 2), -90),
        ]),
    ])
    pos = kad.get_pad_pos('U1', '8')
    kad.move_mods(pos, angle, [
        (None, (3.6, 4), 0, [
            ('R1', (+0.8, 0), +90),
            ('C4', (-0.8, 0), -90),
        ]),
    ])


def place_screw_holes(board):
    d = 4.0
    dy = 8
    holes = [
        ((Lx - 8, Ly - d), 0),
        ((Lx + Ly - d, 0), 90),
        (vec2.add(vec2.add(vec2.scale(-d, vec2.rotate(-30)), vec2.scale(-dy, vec2.rotate(60))), (Lx * 1.5, -Ly)), 120),
        ((Lx * 0.5 - 8, -2 * Ly + d), 0),
    ]
    for idx, prm in enumerate(holes):
        (x, y), angle = prm
        for idx2, sign in enumerate([+1, -1]):
            ctr = vec2.add(org, (x * sign, y))
            hole = 'H{}'.format(2 * idx + idx2 + 1)
            kad.set_mod_pos_angle(hole, ctr, angle * sign)


def add_boundary_gnd_vias():
    dist = 2.4
    pnts = []
    # top
    for t in range(-2, 2 + 1):
        pnts.append((6 * t, -2*Ly + dist))
    # bottom
    for t in range(-5, 5 + 1):
        pnts.append((7 * t, Ly - dist))
    # left / right
    for t in range(-4, 4):
        if t == -1:
            continue
        pnts.append(vec2.add(vec2.add(vec2.scale(-dist, vec2.rotate(90-120)), vec2.scale(7*t+1, vec2.rotate(90-30))), (+Lx*1.5, -Ly))),
        pnts.append(vec2.add(vec2.add(vec2.scale(-dist, vec2.rotate(90+120)), vec2.scale(7*t+1, vec2.rotate(90+30))), (-Lx*1.5, -Ly))),
    # top corners
    for th in range(-130 + 1, -180, -10):
        pnts.append(vec2.scale(Ly - dist, vec2.rotate(90+th), (+Lx/2, -Ly)))
        pnts.append(vec2.scale(Ly - dist, vec2.rotate(90-th), (-Lx/2, -Ly)))
    # bottom corners
    for th in range(-120 + 0, 0, 10):
        if abs(90+th) < 5:
            continue
        pnts.append(vec2.scale(Ly - dist, vec2.rotate(90+th), (+Lx, 0)))
        pnts.append(vec2.scale(Ly - dist, vec2.rotate(90-th), (-Lx, 0)))
    # add vias
    for pnt in pnts:
        kad.add_via(vec2.add(org, pnt), GND, via_size_gnd)


# expander
via_exp_gnd = {}
wire_via_exp = {}
# RJ45
via_rj45 = {}
via_rj45_dbnc = {}
# led power rails
via_size_led_cap = VIA_Size[2]
via_size_led_dat = VIA_Size[2]
wire_via_led_pwr_1st = {}
wire_via_led_pwr_2nd = {}
# led dat connection
via_cap_vcc = {}
via_cap_gnd = {}
via_led_left = {}
via_led_rght = {}
# wiring corner center positions
ctr_row_sw = {}
ctr_led_left = {}
ctr_led_rght = {}
ctr_row_left = {}
ctr_row_rght = {}
ctr_dbnc_left = {}
ctr_dbnc_rght = {}
# debounce row
via_dbnc_row = {}
via_dbnc_col = {}
wire_via_dbnc_vcc = {}
wire_via_dbnc_gnd = {}
# diode col
wire_via_dio_col = {}
# row vert
wire_via_row_vert_set = {}
wire_via_col_horz_set = {}

w_pwr, r_pwr = 0.6, 1.2  # power
w_led, r_led = 0.4, 2.0  # LED dat
w_dat, r_dat = 0.4, 2.0  # row / col
w_exp, r_exp = 0.4, 1.0  # expander

w_gnd = 0.36
s_dat = 0.3
s_pwr = 0.8

s_col = 0.28
s_col2 = 0.5

rj45_vert_width_space_net_pads = [
    (w_dat, s_dat, 'SDA_SCK', '7'),
    (w_gnd, s_dat, 'GND', None),
    (w_dat, s_dat, 'NRST_in', '5'),
    (w_gnd, s_dat, 'GND', None),
    (w_dat, s_pwr, 'SCK_SDA', '3'),
    (w_pwr, s_pwr, 'GND', '6'),
    (w_pwr, 0.000, '3V3', '8'),
]

exp_cidx_pad_width_space_nets = [
    (0, 4, w_dat, s_col, 'ROW3'),
    (0, 3, w_dat, s_col, 'ROW4'),
    (0, 2, w_dat, s_col, 'COL1'),
    (2, -1, w_gnd, s_col2, 'GND'),
    (2, 1, w_dat, s_col2, 'ROW1'),
    (2, -1, w_gnd, s_col2, 'GND'),
    (2, 28, w_dat, s_col2, 'ROW2'),
    (2, -1, w_gnd, s_col2, 'GND'),
    (2, 27, w_dat, s_col, 'COL2'),
    (3, -1, w_gnd, s_col, 'GND'),
    (3, 26, w_dat, s_col, 'COL3'),
    (4, -1, w_gnd, s_col, 'GND'),
    (4, 25, w_dat, s_col, 'COL4'),
    (5, -1, w_gnd, s_col, 'GND'),
    (5, 24, w_dat, s_col, 'COL5'),
    (6, -1, w_gnd, s_col, 'GND'),
    (6, 23, w_dat, s_col, 'COL6'),
    (7, -1, w_gnd, s_col, 'GND'),
    (7, 22, w_dat, s_col, 'COL7'),
    (8, -1, w_gnd, s_col, 'GND'),
    (8, 21, w_dat, s_col, 'COL8'),
    (5, -1, w_gnd, s_col, 'GND'),
    (3, 20, w_dat, s_col, 'COLA'),
    (3, -1, w_gnd, s_col, 'GND'),
    (3, 19, w_dat, s_col, 'COLB'),
    (3, -1, w_gnd, s_col, 'GND'),
    # (9, 18, w_dat, s_col, 'ROW5'),
]

row12_vert_width_space_net = [
    (1, w_gnd, s_dat, 'GND'),
    (1, w_dat, s_dat, 'ROW1'),
    (1, w_gnd, s_dat, 'GND'),
    (2, w_dat, s_dat, 'ROW2'),
    # (2, w_pwr, s_dat, 'GND'),
]


def wire_exp():
    # GND
    wire_via_gnd = kad.add_via_relative('U1', '29', (0, 0), via_size_pwr)
    for mod_exp in ['U1', 'U2']:
        gnd_pad_nums = [6, 12, 13]
        if mod_exp == 'U2':
            gnd_pad_nums.append(11)
        for gnd_pad_num in gnd_pad_nums:
            base_angle = (((gnd_pad_num + 5) // 7) % 2) * 90  # not correct-worthy, but enough
            kad.wire_mod_pads([(mod_exp, wire_via_gnd, mod_exp, str(gnd_pad_num), w_exp, (Dird, base_angle, base_angle + 90, 0))])
    pcb.Delete(wire_via_gnd)

    # I2C address
    mod_exp = 'U1'
    pad_addr = '11'
    via_exp_addr1 = kad.add_via_relative(mod_exp, pad_addr, (0, 4.7), via_size_dat)
    via_exp_addr2 = kad.add_via_relative(mod_exp, pad_addr, (0, 8.2), via_size_pwr)
    kad.wire_mod_pads([
        (mod_exp, pad_addr, mod_exp, via_exp_addr1, w_exp, (Strt)),
        (mod_exp, via_exp_addr1, mod_exp, via_exp_addr2, w_exp, (Strt), 'B.Cu'),
    ])

    # VCC / GND / Nrst vias
    wire_via_exp_vcc = kad.add_via(kad.calc_pos_from_pad(mod_exp, pad_addr, (0, 8.2)), VCC, via_size_dat)
    wire_via_exp_gnd = kad.add_via(kad.calc_pos_from_pad(mod_exp, pad_addr, (0, 6.8)), GND, via_size_dat)
    wire_via_exp_nrst = kad.add_via(kad.calc_pos_from_pad(mod_exp, pad_addr, (0, 5.8)), kad.get_pad_net('U1', '14'), via_size_dat)

    # pass caps (VCC, GND)
    via_exp_cap_vcc = {}
    via_exp_cap_gnd = {}
    ctr = kad.calc_relative_vec('U1', (0, -3.6), kad.get_via_pos(wire_via_exp_vcc))
    for idx, i in enumerate('12'):
        mod_exp = f'U{i}'
        mod_cap = f'C{i}'
        via_exp_cap_vcc[mod_cap] = kad.add_via_relative(mod_cap, '1', [(0, 2.8), (1.8, 1.6)][idx], via_size_pwr)
        via_exp_cap_gnd[mod_cap] = kad.add_via_relative(mod_cap, '2', [(0, 1.4), (1.8, 0)][idx], via_size_pwr)
        kad.wire_mod_pads([
            (mod_cap, '1', mod_exp, '5', w_exp, (Dird, 90, [(180, 1.25), 50], 1)),
            (mod_cap, '2', mod_exp, '6', w_exp, (Dird, 90, [(180, 1.25), 90], 0.5)),
            (mod_cap, '1', mod_cap, via_exp_cap_vcc[mod_cap], w_exp, (Dird, 90, 0, 1)),
            (mod_cap, '2', mod_cap, via_exp_cap_gnd[mod_cap], w_exp, (Dird, 90, 0, 1)),
        ])
        if idx == 0:
            kad.wire_mod_pads([
                #
                (mod_cap, via_exp_cap_vcc[mod_cap], 'U1', wire_via_exp_vcc, w_pwr, (Dird, [(-90, 2.7), 0], 0, r_exp, ctr), 'F.Cu'),
                (mod_cap, via_exp_cap_gnd[mod_cap], 'U1', wire_via_exp_gnd, w_pwr, (Dird, [(-90, 2.7), 0], 0, r_exp, ctr), 'F.Cu'),
            ])
        else:
            kad.wire_mod_pads([
                (mod_cap, via_exp_cap_vcc[mod_cap], 'U1', wire_via_exp_vcc, w_pwr, (Dird, 0, 0, kad.inf, ctr), 'F.Cu'),
                (mod_cap, via_exp_cap_gnd[mod_cap], 'U1', wire_via_exp_gnd, w_pwr, (Dird, 0, 0, kad.inf, ctr), 'F.Cu'),
            ])
            # gnd via
            kad.add_via(kad.calc_pos_from_pad(mod_cap, '1', (0, 2.8)), GND, via_size_gnd)

    # I2C & NRST
    offset_x_nrst = 3.6
    sep_x_nrst = 1.1
    offset_y_nrst = 1.3
    offset_y_i2c = 0.3
    via_exp_nrst_pad = kad.add_via_relative('U2', '14', (offset_y_nrst, 0), via_size_dat)
    via_exp_nrst_con = kad.add_via_relative('U2', '14', (offset_y_nrst, offset_x_nrst), via_size_dat)
    via_exp_sck_sda = kad.add_via_relative('U1', '8', (-offset_y_i2c, offset_x_nrst - sep_x_nrst), via_size_dat)
    via_exp_sda_sck = kad.add_via_relative('U1', '9', (-offset_y_i2c - 0.6, offset_x_nrst + sep_x_nrst), via_size_dat)
    kad.wire_mod_pads([
        # NRST
        ('U2', via_exp_nrst_pad, 'U2', '14', w_exp, (Dird, 0, 90, r_exp)),
        ('U1', via_exp_nrst_pad, 'U1', via_exp_nrst_con, w_exp, (Strt)),
        ('U1', wire_via_exp_nrst, 'U1', '14', w_exp, (Dird, 0, 90, r_exp)),
        ('U1', wire_via_exp_nrst, 'U1', via_exp_nrst_con, w_exp, (Dird, 0, 90, r_exp)),
        # I2C
        ('U1', via_exp_sck_sda, 'U1', '8', w_exp, (Dird, 45, 90, r_exp)),
        ('U1', via_exp_sda_sck, 'U1', '9', w_exp, (Dird, 45, 90, r_exp)),
        ('U2', via_exp_sck_sda, 'U2', '9', w_exp, (Dird, 135, [(-90, 1.5), 0], r_exp)),
        ('U2', via_exp_sda_sck, 'U2', '8', w_exp, (Dird, 135, [(-90, 2.6), 0], r_exp)),
    ])

    # for rj45
    sep = 1.0
    dx = sep * 2
    offset_y = 1.85 + 1.4 + 3.0
    pos_nrst = kad.get_via_pos(via_exp_nrst_con)
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx < 5:
            net = pcb.FindNet(net_name)
            y = offset_y
            if idx == 2:
                y -= 1.1
            pos = kad.calc_relative_vec('C1', (dx, y), pos_nrst)
            dx -= sep
            wire_via_exp[idx] = kad.add_via(pos, net, via_size_gnd)

    kad.wire_mod_pads([
        (mod_exp, via_exp_sda_sck, mod_exp, wire_via_exp[0], w_exp, (Dird, 135, 0, r_exp)),
        (mod_exp, via_exp_sck_sda, mod_exp, wire_via_exp[4], w_exp, (Dird, 45, 0, r_exp)),
    ])
    # NRST
    for layer in Cu_layers:
        kad.wire_mod_pads([
            (mod_exp, wire_via_exp[2], 'R1', '1', w_exp, (Dird, 90, 0), layer),
            (mod_exp, wire_via_exp[3], 'C4', '2', w_exp, (Dird, 0, 90, 0), layer),
            (mod_exp, via_exp_nrst_con, 'R1', '2', w_exp, (Dird, [(0, 0.8), 90], 0), layer),
            (mod_exp, via_exp_nrst_con, 'C4', '1', w_exp, (Dird, [(0, 0.8), 90], 0), layer),
        ])

    wire_via_exp[5] = via_exp_cap_gnd['C1']
    wire_via_exp[6] = via_exp_cap_vcc['C1']

    for via in [wire_via_exp_vcc, wire_via_exp_gnd, wire_via_exp_nrst]:
        pcb.Delete(via)


def wire_rj45():
    w_con = w_pwr

    mod_rj = 'J1'
    # RJ45 to jumpers
    for idx, pad in enumerate('2468'):
        mod_jpf = f'JPF{pad}'
        mod_jpb = f'JPB{10-int(pad)}'
        kad.wire_mod_pads([
            (mod_rj, pad, mod_jpf, '1', w_con, (Dird, 0, 0, 0), 'F.Cu'),
            (mod_rj, pad, mod_jpb, '1', w_con, (Dird, 0, 0, 0), 'B.Cu'),
        ])

    # y positions for jumpers and vias
    sep_via_y = 1.40
    sep_jmp_y = 1.27
    pos_via_y = {}
    pos_jmp_y = {}
    for idx, pad in enumerate('2468'):
        pos_via_y[pad] = sep_via_y * [2, 0, -1, -3][idx]
        pos_jmp_y[pad] = sep_jmp_y * [3, 1, -1, -3][idx]

    wire_via_rj45 = {}
    # jumper to wire vias
    offset_x = 2.0
    for idx, pad in enumerate('268'):
        dy = pos_via_y[pad]
        dy -= pos_jmp_y[pad]
        for layer in Cu_layers:
            name = f'{layer[0]}{pad}'
            mod_jmp = f'JP{name}'
            wire_via_rj45[name] = kad.add_via_relative(mod_jmp, '2', (offset_x, dy), via_size_pwr)
            kad.wire_mod_pads([(mod_jmp, '2', mod_jmp, wire_via_rj45[name], w_con, (Dird, 45, 0), layer)])
    via_rj45['4'] = kad.add_via_relative('JPF4', '2', (offset_x - 0.4, -sep_jmp_y), via_size_pwr)
    kad.wire_mod_pads([
        # '2' -- '8' arc
        ('JPF8', wire_via_rj45['F8'], 'JPB8', wire_via_rj45['B8'], w_con, (Dird, [(0, sep_via_y * 3), 90], 0), 'B.Cu'),
        # connection via (4)
        ('JPF4', '2', 'JPF4', via_rj45['4'], w_con, (Dird, [(90, 0.35), 0], 45), 'F.Cu'),
        ('JPB4', '2', 'JPB4', via_rj45['4'], w_con, (Dird, [(90, 0.35), 0], 45), 'B.Cu'),
        # connect 1 == 9
        (mod_rj, '1', mod_rj, '9', w_dat, (Dird, [(-90, 3), 0], 90, 1.0), 'F.Cu'),
    ])
    via_rj45['8'] = wire_via_rj45['F8']
    del wire_via_rj45['F8']

    # circle connection vias (2 & 6)
    for pidx, pad in enumerate('26'):
        angle = [60, -60][pidx]
        rad = sep_via_y * [2, 1][pidx]
        x = rad * math.cos(math.radians(angle)) + offset_x
        y = rad * math.sin(math.radians(angle)) - pos_jmp_y[pad]
        via_rj45[pad] = kad.add_via_relative(f'JPF{pad}', '2', (x, y), via_size_pwr)
        for lidx, layer in enumerate('FB'):
            lsgn = [+1, -1][lidx]
            name = f'{layer}{pad}'
            mod_jmp = f'JP{name}'
            wire_angle = 90 - angle * lsgn
            kad.wire_mod_pads([(mod_jmp, wire_via_rj45[name], mod_jmp, via_rj45[pad], w_con, (Dird, 0, wire_angle), f'{layer}.Cu')])

    # remove wire vias
    for via in wire_via_rj45.values():
        pcb.Delete(via)


def wire_rj45_vert_lines():
    w_con = w_pwr
    mod_rj = 'J1'

    x_lines = []
    # region prep x offsets
    dx = 0
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx > 0:
            dx -= width / 2
        x_lines.append(dx)
        dx -= width / 2 + space
    # endregion

    wire_via_rj45_row_sets = []

    wire_via_rj45_row = {}
    wire_via_rj45_row_sets.append(wire_via_rj45_row)
    # region 1st via row
    offset_y = 1.8
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        net = pcb.FindNet(net_name)
        if idx < 5:
            x = 2.54 - 1.27 * idx
            pos = kad.calc_pos_from_pad(mod_rj, '5', (x, offset_y))
            wire_via_rj45_row[idx] = kad.add_via(pos, net, via_size_dat)
            if pad is not None:
                kad.wire_mod_pads([(mod_rj, pad, mod_rj, wire_via_rj45_row[idx], w_dat, (Strt), 'B.Cu')])
        else:
            x = 2.4 + (x_lines[idx] - x_lines[5])
            pos = kad.calc_pos_from_pad(mod_rj, '9', (x, -6))
            wire_via_rj45_row[idx] = kad.add_via(pos, net, via_size_pwr)

    # connection vias (3, 5, 7) and gnd
    pos = kad.calc_pos_from_pad(mod_rj, '7', (1.27, offset_y))
    via_gnd = kad.add_via(pos, GND, via_size_pwr)
    # more gnd via
    pos = kad.calc_pos_from_pad(mod_rj, '3', (-1.27, offset_y))
    via_gnd2 = kad.add_via(pos, GND, via_size_dat)
    # wire GND/VCC vias
    r_rj = 2.4
    kad.wire_mod_pads([
        # 6 - GND & 8 - VCC
        ('J1', via_rj45['6'], 'J1', wire_via_rj45_row[6], w_con, (Dird, [(45, 1.2), 0], 90, r_rj), 'F.Cu'),
        ('J1', via_rj45['8'], 'J1', wire_via_rj45_row[5], w_con, (Dird, 0, 90, r_rj), 'B.Cu'),
        # Gnd - Gnd
        (mod_rj, wire_via_rj45_row[5], mod_rj, via_gnd, w_con, (Dird, 90, 0, r_rj), 'B.Cu'),
        (mod_rj, via_gnd2, mod_rj, via_gnd, w_dat, (Strt), 'F.Cu'),  # thru [1]
    ])
    # endregion

    wire_via_rj45_row = {}
    wire_via_rj45_row_sets.append(wire_via_rj45_row)
    # region 2nd via row
    offset_y = 6.0
    sep_cap = 1.1
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx < 5:
            x = x_lines[idx] - x_lines[2]
            pos = kad.calc_pos_from_pad(mod_rj, '5', (x, offset_y))
        else:
            x = 6 - (idx - 5.5) * 2 * sep_cap
            pos = kad.calc_pos_from_pad(mod_rj, '9', (x, offset_y))
        net = pcb.FindNet(net_name)
        wire_via_rj45_row[idx] = kad.add_via(pos, net, via_size_dat)

    # pwr cap
    mod_c = 'C3'
    via_cap_vcc = kad.add_via_relative(mod_c, '1', (-1.6, 0), via_size_dat)
    via_cap_gnd = kad.add_via_relative(mod_c, '2', (+1.6, 0), via_size_dat)
    for layer in Cu_layers:
        kad.wire_mod_pads([
            (mod_c, '1', mod_c, via_cap_vcc, w_dat, (Strt), layer),
            (mod_c, '2', mod_c, via_cap_gnd, w_dat, (Strt), layer),
        ])
    for idx in range(2):
        _via = [via_cap_vcc, via_cap_gnd][idx]
        _wia = kad.add_via_relative(mod_c, '12'[idx], ([-1.6, +1.6][idx], [+1, -1][idx] * sep_cap), via_size_dat)
        for sign in [-1, +1]:
            kad.wire_mod_pads([(mod_c, _via, mod_c, _wia, w_pwr, (Dird, 90, [(0, 1.0 * sign), 0]), 'F.Cu')])
        pcb.Delete(_wia)

    # wire 1-2
    ctr_pwr_top = kad.calc_relative_vec(mod_rj, (+2, +1), kad.get_via_pos(wire_via_rj45_row_sets[0][5]))
    ctr_pwr_btm = kad.calc_relative_vec(mod_rj, (-2, -1), kad.get_via_pos(wire_via_rj45_row_sets[1][6]))
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx < 5:
            layer = 'B.Cu'
            prm = (ZgZg, 90, 30)
        else:
            layer = 'F.Cu'
            prm = (Dird, [(-90, ctr_pwr_top), -50], 90, kad.inf, ctr_pwr_btm)
        kad.wire_mod_pads([(mod_rj, wire_via_rj45_row_sets[0][idx], mod_rj, wire_via_rj45_row_sets[1][idx], width, prm, layer)])
    # endregion

    wire_via_rj45_row = {}
    wire_via_rj45_row_sets.append(wire_via_rj45_row)
    # region 3rd via row
    mod_sw = 'SW13'

    offset_y = 2
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        dy = 0 if idx < 5 else -(idx - 5.5)
        x = 11 + x_lines[idx]
        pos = kad.calc_pos_from_pad(mod_sw, '3', (x, offset_y + dy))
        net = pcb.FindNet(net_name)
        wire_via_rj45_row[idx] = kad.add_via(pos, net, via_size_pwr)

    ctr_pwr_top = kad.calc_relative_vec(mod_rj, (-2, +3), kad.get_via_pos(wire_via_rj45_row_sets[1][6]))
    ctr_pwr_btm = kad.calc_relative_vec(mod_rj, (+2, -3), kad.get_via_pos(wire_via_rj45_row_sets[2][5]))
    ctr_dat_top = kad.calc_relative_vec(mod_rj, (+2, +0.5), kad.get_via_pos(wire_via_rj45_row_sets[1][0]))
    ctr_dat_btm = kad.calc_relative_vec(mod_rj, (-2, -0.5), kad.get_via_pos(wire_via_rj45_row_sets[2][4]))

    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx < 5:
            layer = 'B.Cu'
            prm = (Dird, [(-90, ctr_dat_top), -45], 90, kad.inf, ctr_dat_btm)
        else:
            layer = 'F.Cu'
            prm = (Dird, [(-90, ctr_pwr_top), -135], 90, kad.inf, ctr_pwr_btm)
        kad.wire_mod_pads([(mod_rj, wire_via_rj45_row_sets[1][idx], mod_sw, wire_via_rj45_row_sets[2][idx], width, prm, layer)])
    # endregion

    wire_via_rj45_row = {}
    wire_via_rj45_row_sets.append(wire_via_rj45_row)
    # region 4th via row
    mod_sw = 'SW14'
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        y = 8 + (0 if idx < 5 else (idx - 5.5))
        x = x_lines[idx] - x_lines[2]
        pos = kad.calc_relative_vec(mod_sw, (x, y), kad.get_via_pos(wire_via_exp[2]))
        net = pcb.FindNet(net_name)
        wire_via_rj45_row[idx] = kad.add_via(pos, net, via_size_pwr)

    # wire 2-3
    ctr_top = kad.calc_relative_vec(mod_rj, (-3, +8), kad.get_via_pos(wire_via_rj45_row_sets[2][6]))
    ctr_btm = kad.calc_relative_vec(mod_rj, (+3, -3), kad.get_via_pos(wire_via_rj45_row_sets[3][0]))
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        prm = (Dird, [(-90, ctr_top), -120], 90, kad.inf, ctr_btm)
        kad.wire_mod_pads([(mod_rj, wire_via_rj45_row_sets[2][idx], mod_sw, wire_via_rj45_row_sets[3][idx], width, prm, 'B.Cu')])

    # wire 3-exp
    mod_exp = 'U1'
    for idx, (width, space, net_name, pad) in enumerate(rj45_vert_width_space_net_pads):
        if idx in [2]:
            prm = (Strt)
        elif idx in [1, 3]:
            prm = (Dird, 90, 90 - 45 * (idx - 2))
        elif idx in [0, 4]:
            prm = (Dird, 90, [(180, 0.5), 45 * (idx - 2)/2])
        else:
            prm = (ZgZg, 90, 30)
        kad.wire_mod_pads([(mod_rj, wire_via_rj45_row[idx], mod_exp, wire_via_exp[idx], width, prm, 'B.Cu')])
    # endregion

    # remove wire vias
    for set_no, wire_vias in enumerate(wire_via_rj45_row_sets):
        for idx, via in wire_vias.items():
            if set_no == 0 and idx in [1, 3, 5]:
                continue
            if set_no == 2 and idx in [5, 6]:
                continue
            if set_no == 3:
                if idx == 5:
                    via_rj45_dbnc['gnd'] = via
                    continue
                if idx == 6:
                    via_rj45_dbnc['vcc'] = via
                    continue
            pcb.Delete(via)


def wire_debounce_rrc_rotenc():
    dy_pwr_vcc = 2.4
    dy_pwr_gnd = 1.4
    dy_via_pwr = 0.25
    for cidx in range(1, 9):
        mod_cd = f'CD{cidx}'
        mod_r1 = f'R{cidx}1'
        mod_r2 = f'R{cidx}2'

        lrs = get_diode_side(f'{cidx}4')

        # row gnd and vcc vias
        dx = -1.6 * lrs
        via_dbnc_vcc_conn = kad.add_via_relative(mod_cd, '1', (0, dx), via_size_pwr)
        via_dbnc_gnd_conn = kad.add_via_relative(mod_r2, '2', (0, dx), via_size_pwr)
        if cidx not in [8]:
            kad.add_via_relative(mod_cd, '1', (-dy_pwr_vcc - dy_via_pwr, dx), via_size_pwr)  # vcc
        wire_via_dbnc_vcc[cidx] = kad.add_via_relative(mod_cd, '1', (-dy_pwr_vcc, dx + (1.2 if cidx == 8 else 0)), via_size_pwr)
        wire_via_dbnc_gnd[cidx] = kad.add_via_relative(mod_r2, '2', (+dy_pwr_gnd, dx - (1.2 if cidx == 8 else 0)), via_size_pwr)
        if cidx == 5:
            via_dbnc_rotenc_vcc = kad.add_via_relative(mod_cd, '1', (-dy_pwr_vcc - dy_via_pwr, dx + 11.2), via_size_pwr)
            via_dbnc_rotenc_gnd = kad.add_via_relative(mod_r2, '2', (+dy_pwr_gnd - dy_via_pwr, dx - 5.0), via_size_pwr)
        via_dbnc_row[cidx] = kad.add_via_relative(mod_cd, '2', (0.2, dx), via_size_dat)
        via_dbnc_col[cidx] = kad.add_via_relative(mod_r2, '1', (0, dx), via_size_dat)
        # gnd vias
        if cidx not in [3]:
            kad.add_via_relative(mod_r2, '2', (-1.1, 7.0 * lrs), via_size_gnd)

        # resister and cap vias
        for layer in Cu_layers:
            kad.wire_mod_pads([
                # debounce resisters and cap
                (mod_r1, '1', mod_r2, '1', w_dat, (ZgZg, 90, 90, 0.5), layer),
                (mod_r1, '2', mod_cd, '2', w_dat, (Dird, 90, 0, 0), layer),
                # res & cap pads and via
                (mod_cd, '1', mod_cd, via_dbnc_vcc_conn, w_dat, (Strt), layer),
                (mod_r2, '2', mod_r2, via_dbnc_gnd_conn, w_dat, (Strt), layer),
                (mod_cd, '2', mod_cd, via_dbnc_row[cidx], w_dat, (Dird, 90, 0, 0), layer),
                (mod_r2, '1', mod_cd, via_dbnc_col[cidx], w_dat, (Dird, 90, 0, 0), layer),
            ])
        # debounce to vcc / gnd rails
        kad.wire_mod_pads([
            (mod_cd, via_dbnc_vcc_conn, mod_cd, wire_via_dbnc_vcc[cidx], w_pwr, (Strt), 'B.Cu') if cidx not in [8] else None,
            (mod_cd, via_dbnc_vcc_conn, mod_cd, wire_via_dbnc_vcc[cidx], w_pwr, (Dird, 0, 90), 'F.Cu') if cidx in [8] else None,
            (mod_r2, via_dbnc_gnd_conn, mod_r2, wire_via_dbnc_gnd[cidx], w_pwr, (Dird, 0, [(+90, 1.4), 90], w_pwr), 'F.Cu'),
            (mod_r2, via_dbnc_gnd_conn, mod_r2, wire_via_dbnc_gnd[cidx], w_pwr, (Dird, 0, [(-90, 1.4), 90], w_pwr), 'F.Cu') if cidx not in [8] else None,
        ])
        # remake to make it to the right
        if cidx == 4:
            pcb.Delete(wire_via_dbnc_gnd[cidx])
            wire_via_dbnc_gnd[cidx] = kad.add_via_relative(mod_r2, '2', (+dy_pwr_gnd, dx + 8), via_size_pwr)

    # rotenc debounce
    mod_re = 'RE1'

    via_dbnc_gnd = {}
    via_rotenc_gnd = kad.add_via(kad.calc_pos_from_pad(mod_re, 'C', (2.4, +1.4)), GND, via_size_pwr)
    via_rotenc_gnd = kad.add_via(kad.calc_pos_from_pad(mod_re, 'C', (2.4, -1.4)), GND, via_size_pwr)

    for i, cidx in enumerate([11, 12]):
        mod_cd = f'CD{cidx}'
        mod_r1 = f'R{cidx}1'
        mod_r2 = f'R{cidx}2'

        sign = [+1, -1][i]

        # row gnd and vcc vias
        via_dbnc_gnd[cidx] = kad.add_via_relative(mod_r2, '2', (1.6, 0), via_size_pwr)
        via_dbnc_row[cidx] = kad.add_via_relative(mod_cd, '2', (1.6 * sign, [0, 2.0][i]), via_size_dat)
        # gnd via
        if i == 0:
            kad.add_via(kad.calc_pos_from_pad(mod_cd, '2', (1.6, 1.4)), GND, via_size_gnd)
        elif i == 1:
            via_dbnc_row['Gnd1'] = kad.add_via(kad.calc_pos_from_pad(mod_cd, '2', (-3.3, 1.0)), GND, via_size_dat)
            via_dbnc_row['Gnd2'] = kad.add_via(kad.calc_pos_from_pad(mod_cd, '2', (0, 3.0)), GND, via_size_dat)

        # resister and cap vias
        for layer in Cu_layers:
            kad.wire_mod_pads([
                # debounce resisters and cap
                (mod_r1, '1', mod_r2, '1', w_dat, (Strt), layer),
                (mod_r1, '2', mod_cd, '2', w_dat, (Dird, 90, 0, 0), layer),
                # res & cap pads and via
                (mod_cd, '2', mod_cd, via_dbnc_row[cidx], w_dat, (Dird, 90, 0), layer),
                (mod_r2, '2', mod_r2, via_dbnc_gnd[cidx], w_dat, (Dird, 90, 0, 0), layer),
                # rotenc vcc & rea/b
                (mod_re, 'C', mod_cd, '1', w_dat, (Dird, 0, 0, w_dat), layer),
                (mod_re, 'AB'[i], mod_r2, '1', w_dat, (Dird, [30, 150][i], 90, 2.0), layer),
            ])
        # gnd via
        kad.wire_mod_pads([(mod_re, via_rotenc_gnd, mod_r2, via_dbnc_gnd[cidx], w_pwr, (Dird, 90, 90, r_dat), 'F.Cu')])

    # gnd between cols for col horz lines
    kad.wire_mod_pads([
        (mod_re, via_dbnc_row['Gnd1'], mod_re, via_dbnc_row['Gnd2'], w_dat, (Dird, 0, 90, 0.4), 'B.Cu'),
        (mod_re, via_dbnc_row['Gnd2'], mod_re, via_dbnc_gnd[12], w_dat, (Dird, -90, 0, 0.4), 'B.Cu'),
    ])
    # cap vcc
    for layer in Cu_layers:
        kad.wire_mod_pads([('CD11', '1', 'CD12', '1', w_dat, (Strt), layer)])

    # vcc & gnd from row4
    tctr = kad.calc_pos_from_pad(mod_re, 'S1', (2, -10))
    bctr = kad.calc_pos_from_pad(mod_re, 'C', (9.4, -3.0))
    kad.wire_mod_pads([
        ('CD5', via_dbnc_rotenc_vcc, mod_re, 'C', w_pwr, (Dird, 0, [(0, bctr), 90], kad.inf, tctr), 'B.Cu'),
        ('R52', via_dbnc_rotenc_gnd, mod_re, via_rotenc_gnd, w_pwr, (Dird, 0, [(0, bctr), -90], kad.inf, tctr), 'B.Cu'),
    ])


def wire_led():
    dx_led_pwr = 1.75
    dy_led_pwr = 1.04

    idx_left_1st_end = ['13', '35']
    idx_left_2nd_end = ['35']
    for idx in keys.keys():
        if not is_SW(idx):
            continue
        mod_sw = 'SW' + idx
        mod_led = 'L' + idx
        mod_cap = 'C' + idx

        isL2R = is_L2R_key(idx)
        lrx = 0 if isL2R else 1  # L/R index
        lrs = [+1, -1][lrx]  # L/R sign

        # 1st power rail vias
        dy = +dy_led_pwr
        dx_1st = -dx_led_pwr
        if idx in idx_left_1st_end:
            dx_1st += 1.2  # move 1st via to the right
        if idx not in ['21']:
            wire_via_led_pwr_1st[idx] = kad.add_via_relative(mod_cap, '12'[lrx], vec2.scale(lrs, (dx_1st, -dy)), via_size_pwr)
        # 2nd power rail vias
        dy = -dy_led_pwr
        dx_2nd = +dx_led_pwr
        if idx in idx_left_2nd_end:
            dx_2nd += 1.2  # move 2nd via to the right
        wire_via_led_pwr_2nd[idx] = kad.add_via_relative(mod_cap, '21'[lrx], vec2.scale(lrs, (dx_2nd, -dy)), via_size_pwr)
        # cap vias (internal)
        via_cap_vcc[idx] = kad.add_via_relative(mod_cap, '1', (-dx_led_pwr, 0), via_size_led_cap)
        via_cap_gnd[idx] = kad.add_via_relative(mod_cap, '2', (+dx_led_pwr, 0), via_size_led_cap)
        # pwr vias (internal)
        via_pwr_vcc = kad.add_via_relative(mod_cap, '1', (-1.3, +2.1 * lrs), via_size_led_cap)
        via_pwr_gnd = kad.add_via_relative(mod_cap, '2', (+1.3, +2.1 * lrs), via_size_led_cap)
        # led data vias (internal)
        via_led_in = kad.add_via_relative(mod_led, '73'[lrx], (+1.5, 0), via_size_led_dat)
        if idx not in ['351']:
            via_led_out = kad.add_via_relative(mod_led, '15'[lrx], (-1.5, 0), via_size_led_dat)
        else:
            via_led_out = None
        # led data connection vias
        pos = kad.calc_pos_from_pad(mod_cap, '21'[lrx], (+3.6 * lrs, 0))
        via_led_rght[idx] = kad.add_via(pos, kad.get_pad_net(mod_led, '13'[lrx]), via_size_led_dat)
        if idx not in ['35']:
            dy = 1 if idx == '21' else 0
            pos = kad.calc_pos_from_pad(mod_cap, '12'[lrx], (-3.6 * lrs, dy))
            via_led_left[idx] = kad.add_via(pos, kad.get_pad_net(mod_led, '75'[lrx]), via_size_led_dat)

        # wiring centers
        ctr_row_sw[idx] = kad.calc_pos_from_pad(mod_sw, '3', (0, -10))
        ctr_led_rght[idx] = kad.calc_pos_from_pad(mod_sw, '4', (-0.6, 0.4))
        ctr_led_left[idx] = kad.calc_pos_from_pad(mod_sw, '5', (-1, 6))
        ctr_row_rght[idx] = kad.calc_pos_from_pad(mod_sw, '2', (0, -3))
        ctr_row_left[idx] = kad.calc_pos_from_pad(mod_sw, '3', (-0.8, +3))
        ctr_dbnc_rght[idx] = kad.calc_pos_from_pad(mod_sw, '2', (0, -7))
        ctr_dbnc_left[idx] = kad.calc_pos_from_pad(mod_sw, '3', (1.2, -2))

        # wire internal vias
        for lidx, layer in enumerate(Cu_layers):
            kad.wire_mod_pads([
                # cap pad <-> cap pwr via
                (mod_cap, '1', mod_cap, via_cap_vcc[idx], w_led, (Dird, 0, 90, 0), layer),
                (mod_cap, '2', mod_cap, via_cap_gnd[idx], w_led, (Dird, 0, 90, 0), layer),
                # led pad <-> dat via (3/7 = in, 1/5 = out)
                (mod_led, '37'[lidx], mod_led, via_led_in,  w_led, (Dird, 0, 90), layer),
                (mod_led, '15'[lidx], mod_led, via_led_out, w_led, (Dird, 0, 90), layer) if via_led_out is not None else None,
            ])
        # wire vias
        kad.wire_mod_pads([
            # pwr rail vias <-> cap vias
            (mod_sw, wire_via_led_pwr_1st[idx], mod_sw, [via_cap_vcc, via_cap_gnd][lrx][idx], w_pwr, (Dird, [(0, +1.2), 0], 90, r_pwr), 'F.Cu') if idx in wire_via_led_pwr_1st and idx not in idx_left_1st_end else None,
            (mod_sw, wire_via_led_pwr_1st[idx], mod_sw, [via_cap_vcc, via_cap_gnd][lrx][idx], w_pwr, (Dird, [(0, -1.2), 0], 90, r_pwr), 'F.Cu') if idx in wire_via_led_pwr_1st else None,
            (mod_sw, wire_via_led_pwr_2nd[idx], mod_sw, [via_cap_gnd, via_cap_vcc][lrx][idx], w_pwr, (Dird, [(0, +1.2), 0], 90, w_pwr), 'F.Cu') if idx not in idx_left_2nd_end else None,
            (mod_sw, wire_via_led_pwr_2nd[idx], mod_sw, [via_cap_gnd, via_cap_vcc][lrx][idx], w_pwr, (Dird, [(0, -1.2), 0], 90, w_pwr), 'F.Cu'),
            # cap pwr via <-> pwr via
            (mod_cap, via_cap_vcc[idx], mod_led, via_pwr_vcc, w_led, (Dird, 90, -60 * lrs), 'B.Cu'),
            (mod_cap, via_cap_gnd[idx], mod_led, via_pwr_gnd, w_led, (Dird, 90, +60 * lrs), 'B.Cu'),
            # pwr via <-> led pad (4/8 = 5VD, 2/6 = GNDD)
            (mod_cap, via_pwr_vcc, mod_led, '48'[lrx], w_led, (Dird, 0, -60 * lrs), Cu_layers[lrx]),
            (mod_cap, via_pwr_gnd, mod_led, '62'[lrx], w_led, (Dird, 0, +60 * lrs), Cu_layers[lrx ^ 1]),
            # pwr via <-> sw pins
            (mod_cap, via_pwr_vcc, mod_sw, '54'[lrx], w_led, (Dird, 0, +60 * lrs), 'F.Cu'),
            (mod_cap, via_pwr_gnd, mod_sw, '45'[lrx], w_led, (Dird, 0, -60 * lrs), 'F.Cu'),
            # led pad <-> sw pins
            (mod_led, '26'[lrx], mod_sw, '45'[lrx], w_led, (Dird, 0, 90), Cu_layers[lrx]),
            (mod_led, '84'[lrx], mod_sw, '54'[lrx], w_led, (Dird, 0, 90), Cu_layers[lrx ^ 1]),
            # led dat via <-> dat connect vias
            (mod_led, [via_led_in, via_led_out][lrx], mod_led, via_led_left[idx], w_led, (Dird, 102, 0), 'B.Cu') if idx in via_led_left else None,
            (mod_led, [via_led_out, via_led_in][lrx], mod_led, via_led_rght[idx], w_led, (Dird,  78, 0), 'B.Cu') if idx in via_led_rght else None,
        ])


def wire_row_led_horz_lines():
    for ridx in range(1, 5):
        for cidx in range(1, 8):
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
            prm_dbnc = None
            if cidx in [2]:  # straight
                prm_led = (Dird, 0, 90)
                prm_row = (Dird, 0, 90)
                if ridx == 4:
                    prm_dbnc = (Dird, 0, 90)
            elif cidx in [3, 4]:
                sangle = {3: 0, 4: 1}[cidx]  # small_angle [deg]
                wctr = ctr_row_sw[rght]
                prm_led = (Dird, sangle, 0, kad.inf, wctr)
                prm_row = (Dird, sangle, 0, kad.inf, wctr)
                if ridx == 4:
                    prm_dbnc = (Dird, sangle, 0, kad.inf, wctr)
            else:
                row_angle = 90 + 4
                # led
                sangle = row_angle - (angle_Inner_Index if cidx in [1] else angle_M_Comm)
                lctr = ctr_led_rght[left]
                rctr = ctr_led_left[rght]
                prm_led = (Dird, [(180, lctr), sangle], 0, kad.inf, rctr)
                # sw row
                sangle = 90 + 22
                lctr = ctr_row_rght[left]
                rctr = ctr_row_left[rght]
                prm_row = (Dird, 0, [(0, rctr), sangle + 180], kad.inf, lctr)
                if ridx == 4:
                    lctr = ctr_dbnc_rght[left]
                    rctr = ctr_dbnc_left[rght]
                    prm_dbnc = (Dird, 0, [(0, rctr), 110 + 180], kad.inf, lctr)
            # print( idx, nidx )
            sw_L, sw_R = f'SW{left}', f'SW{rght}'
            # power rails, row lines, led data lines
            kad.wire_mod_pads([
                (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_1st[rght], w_pwr, prm_led, 'F.Cu') if left in wire_via_led_pwr_1st else None,
                (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_2nd[rght], w_pwr, prm_led, 'F.Cu'),
                (sw_L, via_led_rght[left], sw_R, via_led_left[rght], w_led, prm_led, 'F.Cu'),
                (sw_L, '2', sw_R, '3', w_dat, prm_row, 'F.Cu'),
            ])
            # debounse power rails
            if ridx == 4:
                kad.wire_mod_pads([
                    (sw_L, wire_via_dbnc_vcc[cidx], sw_R, wire_via_dbnc_vcc[ncidx], w_pwr, prm_dbnc, 'F.Cu'),
                    (sw_L, wire_via_dbnc_gnd[cidx], sw_R, wire_via_dbnc_gnd[ncidx], w_pwr, prm_dbnc, 'F.Cu'),
                ])
            # VCC and GND from RJ45
            if ridx == 4 and cidx == 1:
                kad.wire_mod_pads([
                    (sw_L, via_rj45_dbnc['vcc'], sw_L, wire_via_dbnc_vcc[cidx], w_pwr, (Dird, 90, 0, 1), 'F.Cu'),
                    (sw_L, via_rj45_dbnc['gnd'], sw_L, wire_via_dbnc_gnd[cidx], w_pwr, (Dird, 90, 0, 1), 'F.Cu'),
                ])


def wire_led_left_right_ends_thumb():
    # between rj45 and SW21
    mod_rj = 'J1'
    mod_sw = 'SW21'
    mod_dio = 'DL1'
    # 4V3 diode
    via_led_5v = kad.add_via_relative(mod_dio, '2', (2, 0), via_size_pwr)
    for layer in Cu_layers:
        kad.wire_mod_pads([
            (mod_dio, '1', mod_sw, via_cap_vcc['21'], w_pwr, (Dird, 0, 90), layer),
            (mod_dio, '2', mod_dio, via_led_5v, w_pwr, (Strt), layer),
        ])
    # 5V, derouting the diode
    prm = (Dird, [(-90, 1.4), (180, 7.0), 135], 0)
    kad.wire_mod_pads([(mod_dio, via_led_5v, 'SW31', wire_via_led_pwr_1st['31'], w_pwr, prm, 'F.Cu')])

    # from rj45
    kad.wire_mod_pads([
        # 5VD & GNDD
        (mod_rj, via_rj45['4'], mod_dio, via_led_5v, w_pwr, (Dird, 100, 0), 'F.Cu'),
        (mod_rj, via_rj45['2'], mod_sw, wire_via_led_pwr_2nd['21'], w_pwr, (Dird, 135, 0), 'F.Cu'),
        # led data
        (mod_rj, '1', mod_sw, via_led_left['21'], w_led, (Dird, [(150, 0.8), 90], 0, 3), 'B.Cu'),
    ])

    # between rows at left ends
    for left, rght in [('22', '13'), ('15', '25')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        if left == '22':
            lcnr = kad.calc_pos_from_pad(sw_L, '5', (0.2, 0.2))
            rcnr = kad.calc_pos_from_pad(sw_R, '5', (-0.7, 4.0))
            prm_1st = (Dird, [(0, lcnr), 90 + angle_Inner_Index], [(0, rcnr), (-90, rcnr), 0], 2)
            prm_2nd = (Dird, [(0, lcnr), 90 + angle_Inner_Index], 0, 2)
        elif left == '15':
            lctr = kad.calc_pos_from_pad(sw_L, '5', (0, 0))
            rctr = kad.calc_pos_from_pad(sw_R, '5', (0, 5.4))
            prm = (Dird, 0, [(0, rctr), -78], kad.inf, lctr)
            prm_1st = prm_2nd = prm
        kad.wire_mod_pads([
            (sw_L, via_led_left[left], sw_R, via_led_left[rght], w_led, prm_1st, 'F.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_2nd[rght], w_pwr, prm_1st, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_1st[rght], w_pwr, prm_2nd, 'F.Cu'),
        ])

    # between rows at right ends
    for left, rght in [('71', '82'), ('83', '84'), ('25', '35')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        if left == '71':
            lcnr = ctr_led_rght[left]
            rcnr = kad.calc_pos_from_pad(sw_R, '4', (1.2, 5.3))
            prm = (Dird, [(180, lcnr), 125], [(180, rcnr), -90], 2)
        elif left == '83':
            lcnr = kad.calc_pos_from_pad(sw_L, '4', (-1.2, +0.6))
            rcnr = kad.calc_pos_from_pad(sw_L, '2', (-0.8, -3.2))
            prm = (Dird, [(180, lcnr), (90, rcnr), 0], 180, 8)
        elif left == '25':
            lctr = kad.calc_pos_from_pad(sw_L, '4', (-2.0, 0.6))
            rctr = kad.calc_pos_from_pad(sw_R, '4', (-0.3, 5.3))
            prm = (Dird, [(180, lctr), 90], [(180, rctr), -98], 8)
        kad.wire_mod_pads([
            (sw_L, via_led_rght[left], sw_R, via_led_rght[rght], w_led, prm, 'F.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_2nd[rght], w_pwr, prm, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_1st[rght], w_pwr, prm, 'F.Cu'),
        ])

    # row4 --> thumb
    for left, rght in [('14', '15')]:
        sw_L, sw_R = f'SW{left}', f'SW{rght}'
        lctr = kad.calc_pos_from_pad(sw_L, '5', (0, -4))
        rctr = kad.calc_pos_from_pad(sw_L, '3', (-4, -16))
        bctr = kad.calc_pos_from_pad(sw_R, '2', (0, -20))
        prm_led = (Dird, [(0, lctr), (54, rctr), 90], 180, kad.inf, bctr)
        kad.wire_mod_pads([
            (sw_L, via_led_left[left], sw_R, via_led_rght[rght], w_led, prm_led, 'F.Cu'),
            (sw_L, wire_via_led_pwr_1st[left], sw_R, wire_via_led_pwr_1st[rght], w_pwr, prm_led, 'F.Cu'),
            (sw_L, wire_via_led_pwr_2nd[left], sw_R, wire_via_led_pwr_2nd[rght], w_pwr, prm_led, 'F.Cu'),
        ])

    # ROW5
    prm = (Dird, 0, [(0, 5), 90], r_pwr)
    kad.wire_mod_pads([
        # COL1 --> COL2
        ('SW15', '3', 'SW25', '3', w_dat, prm, 'B.Cu'),
        # COL2 --> COL3
        ('SW25', '3', 'SW35', '3', w_dat, prm, 'B.Cu'),
        # thumb to RotEnc
        ('SW35', '3', 'RE1', 'S2', w_dat, (Dird, 0, [(-90, 6), 0], r_dat), 'B.Cu'),
    ])


def wire_col_diode():
    # diode vias and wire them
    for idx in keys.keys():
        if not is_SW(idx):
            continue
        lrs = get_diode_side(idx)
        mod_sw = 'SW' + idx
        mod_dio = 'D' + idx
        # vias
        kad.add_via_relative(mod_dio, '1', (0, (1.8 - 0.25) * lrs), via_size_dat)
        wire_via_dio_col[idx] = kad.add_via_relative(mod_dio, '1', (0, 1.8 * lrs), via_size_dat)
        via_dio_sw = kad.add_via_relative(mod_dio, '2', (0.9, -1.5 * lrs), via_size_dat)
        # wire to diode vias
        for layer in Cu_layers:
            kad.wire_mod_pads([
                (mod_dio, '1', mod_dio, wire_via_dio_col[idx], w_dat, (Dird, 0, 90), layer),
                (mod_dio, '2', mod_dio, via_dio_sw, w_dat, (Dird, 90, -90-50*lrs), layer),
            ])
        # wire to SW pad
        kad.wire_mod_pads([(mod_sw, '1', mod_dio, via_dio_sw, w_dat, (Dird, 9, -90-50*lrs, 1.6), 'B.Cu')])

    # RotEnc diode
    idx = SW_RotEnc
    mod_re = 'RE1'
    mod_dio = f'D{idx}'
    via_dio_col_re = kad.add_via_relative(mod_dio, '1', (-1.8, 1.8), via_size_dat)
    kad.add_via(kad.calc_pos_from_pad(mod_dio, '1', (-0.4, 1.8)), GND, via_size_gnd)
    for layer in Cu_layers:
        kad.wire_mod_pads([
            (mod_dio, '2', mod_re, 'S1', w_dat, (Dird, 0, 0, 1), layer),
            (mod_dio, '1', mod_dio, via_dio_col_re, w_dat, (Dird, 0, 90, 1), layer),
        ])

    # col lines
    for cidx in range(1, 9):
        for ridx in range(1, 4):
            # from (top) & to (bottom)
            top = f'{cidx}{ridx}'
            btm = f'{cidx}{ridx+1}'
            if top not in keys.keys() or not is_SW(top):
                continue
            if btm not in keys.keys() or not is_SW(btm):
                continue
            # route
            if btm in ['64']:
                prm_dio = (Dird, 0, 0, 20)
            elif btm in ['84']:
                prm_dio = (Dird, 0, [(180, 7), -50], 6)
            else:
                prm_dio = (ZgZg, 0, 45)
            dio_T = 'D' + top
            dio_B = 'D' + btm
            kad.wire_mod_pads([(dio_T, wire_via_dio_col[top], dio_B, wire_via_dio_col[btm], w_dat, prm_dio, 'B.Cu')])

        mod_r = f'R{cidx}2'

        # row4 to debounce resister
        idx = f'{cidx}{get_btm_row_idx(cidx)}'
        mod_dio = f'D{idx}'
        if cidx == 7:
            prm = (Dird, 0, [(45, 0), (45, 2.6), (-45, 7), 0])
        else:
            prm = (Dird, 0, 90)
        kad.wire_mod_pads([(mod_dio, wire_via_dio_col[idx], mod_r, via_dbnc_col[cidx], w_dat, prm, 'B.Cu')])

        # thumb / RotEnc to debounce resister
        idx = f'{cidx}5'
        mod_dio = f'D{idx}'
        prm = None
        if cidx in [1, 2, 3]:
            prm = (Dird, [(90, 1.2), (0, 9.6), -12], 0, 3)
            _via = wire_via_dio_col[idx]
        elif idx == SW_RotEnc:
            prm = (Dird, 90, 0, 3)
            _via = via_dio_col_re
        if prm is not None:
            kad.wire_mod_pads([(mod_dio, _via, mod_r, via_dbnc_col[cidx], w_dat, prm, 'B.Cu')])


def wire_row_vert_lines():
    # ROW1 & ROW2
    COL = 2
    sep_x = (w_dat + w_gnd) / 2 + s_dat
    # vias
    for rvert in range(1, 5):
        mod_sw = f'SW{COL}{rvert}'
        wire_via_row_vert = {}
        for idx, (row_idx, width, space, net_name) in enumerate(row12_vert_width_space_net):
            if rvert <= row_idx:
                continue
            net = pcb.FindNet(net_name)
            pos = kad.calc_pos_from_pad(mod_sw, '1', (9.2 - sep_x * idx, 8.0))
            wire_via_row_vert[idx] = kad.add_via(pos, net, via_size_gnd)
        wire_via_row_vert_set[rvert] = wire_via_row_vert
    # wiring
    for rvert in range(1, 4):
        mod_swT = f'SW{COL}{rvert}'
        mod_swB = f'SW{COL}{rvert+1}'
        for idx, (row_idx, width, space, net_name) in enumerate(row12_vert_width_space_net):
            if rvert == row_idx and net_name != 'GND':
                kad.wire_mod_pads([
                    (mod_swT, '3', mod_swB, wire_via_row_vert_set[rvert+1][idx], w_dat, (Dird, 50, 90, 4.5), 'B.Cu'),
                ])
            elif idx in wire_via_row_vert_set[rvert] and idx in wire_via_row_vert_set[rvert+1]:
                tcnr = kad.calc_relative_vec(mod_swT, (+3, -4.5), kad.get_via_pos(wire_via_row_vert_set[rvert][0]))
                bcnr = kad.calc_relative_vec(mod_swT, (-3, 0), kad.get_via_pos(wire_via_row_vert_set[rvert+1][3]))
                prm = (Dird, [(90, tcnr), 90 + angle_Inner_Index], 90, kad.inf, bcnr)
                kad.wire_mod_pads([
                    (mod_swT, wire_via_row_vert_set[rvert][idx], mod_swB, wire_via_row_vert_set[rvert+1][idx], width, prm, 'B.Cu'),
                ])


def wire_col_horz_lines():
    # line offset y
    y_offsets = []
    dy = 0
    for idx, (cidx, pad, width, space, net_name) in enumerate(exp_cidx_pad_width_space_nets):
        y_offsets.append(dy)
        dy += width + space

    # horizontal col lines
    pos_y_wire_via_set = {}
    idx_ranges = {}
    for cidx in range(2, 9):
        lrs = get_diode_side(f'{cidx}4')
        lrx = (lrs + 1) / 2
        mod_cd = f'CD{cidx}'

        # index range
        idx0 = -1
        idx1 = -1
        for idx, (cidx0, pad, width, space, net_name) in enumerate(exp_cidx_pad_width_space_nets):
            if cidx0 < cidx:
                continue
            if idx0 < 0:
                idx0 = idx
            idx1 = idx
        assert idx0 >= 0
        idx_ranges[cidx] = (idx0, idx1)

        # y pos
        cidx0, pad, width, space, net_name = exp_cidx_pad_width_space_nets[idx0]
        if lrx == 1:
            dy = 1.3
        else:
            dy = 0.9
        # x pos
        dx = -1.6 * lrs * (1 - lrx)
        if cidx == 2:
            dx += 10
            dy -= y_offsets[idx0+6] - y_offsets[idx0]  # ROW1, ROW2
        elif cidx == 3:
            dx += 1.4
            dy -= y_offsets[idx0+2] - y_offsets[idx0]

        wire_via_col_horz = {}
        pos_y_wire_via = {}
        pos_y_wire_via_set[cidx] = pos_y_wire_via
        for idx in range(idx0, idx1+1):
            cidx0, pad, width, space, net_name = exp_cidx_pad_width_space_nets[idx]
            if cidx0 < cidx:
                continue
            dy += width / 2
            pos = kad.calc_pos_from_pad(mod_cd, '2', (dy, dx))
            net = GND if pad == -1 else kad.get_pad_net(f'U1', f'{pad}')
            wire_via_col_horz[idx] = kad.add_via(pos, net, (0.58, 0.3))
            pos_y_wire_via[idx] = dy
            dy += width / 2 + space
        wire_via_col_horz_set[cidx] = wire_via_col_horz
        # wire to debounce
        didx = 5 if cidx == 2 else 1
        kad.wire_mod_pads([
            (mod_cd, via_dbnc_row[cidx], mod_cd, wire_via_col_horz_set[cidx][idx0+didx], w_dat, (Dird, 0, 90), 'F.Cu'),
        ])

    # ROW1 & ROW2
    _ctr = kad.calc_relative_vec('SW24', (-1, 2), kad.get_via_pos(wire_via_col_horz_set[2][3]))
    prm = (Dird, 90, 0, kad.inf, _ctr)
    lidx0 = None
    for lidx in range(len(exp_cidx_pad_width_space_nets)):
        cidx, pad, width, space, net_name = exp_cidx_pad_width_space_nets[lidx]
        if cidx != 2:
            continue
        if lidx0 is None:
            lidx0 = lidx
        idx = lidx - lidx0
        if idx > 4:
            continue
        if net_name == 'GND':
            delta = (0, -1)
        else:
            delta = (0, 0)
        mod_cd = f'CD{cidx}'
        pos_ref = kad.get_via_pos(wire_via_col_horz_set[cidx][lidx])
        net = pcb.FindNet(net_name)
        _via = kad.add_via(kad.calc_relative_vec(mod_cd, delta, pos_ref), net, via_size_gnd if net_name == 'GND' else via_size_dat)
        if idx != 4:
            kad.wire_mod_pads([(mod_cd, _via, mod_cd, wire_via_row_vert_set[4][idx], width, prm, 'B.Cu')])
        if net_name == 'GND':
            wire_via = kad.add_via(kad.calc_relative_vec(mod_cd, (0, 2), pos_ref), GND, via_size_gnd)
            for layer in Cu_layers:
                kad.wire_mod_pads([(mod_cd, _via, mod_cd, wire_via, width, (Strt), layer)])
            pcb.Delete(wire_via)

    # RotEnc cols
    mod_re = 'RE1'
    lctr = kad.calc_relative_vec('CD3', (2, -2), kad.get_via_pos(wire_via_col_horz_set[3][23]))
    for lidx in range(22, 26):
        cidx, pad, width, space, net_name = exp_cidx_pad_width_space_nets[lidx]
        if cidx != 3:
            continue
        mod_cd = f'CD{cidx}'
        # print(lidx, net_name)
        if net_name == 'COLA':
            idx = 11
        elif net_name == 'COLB':
            idx = 12
        elif lidx == 23:
            idx = 'Gnd1'
        else:
            idx = 'Gnd2'
        prm = (Dird, 90, 90, kad.inf, lctr)
        kad.wire_mod_pads([(mod_cd, wire_via_col_horz_set[cidx][lidx], mod_re, via_dbnc_row[idx], width, prm)])

    # Gnd vias
    for lidx in range(22):
        cidx, pad, width, space, net_name = exp_cidx_pad_width_space_nets[lidx]
        if net_name != 'GND':
            continue
        pos, net = kad.get_via_pos_net(wire_via_col_horz_set[cidx][lidx])
        if cidx in [3, 4, 5, 6, 7, 8]:
            delta = ((width - 0.8)/2, 0)
            if lidx == 21:
                delta = vec2.scale(-1, delta)
        else:
            continue
        mod_cd = f'CD{cidx}'
        pos = kad.calc_relative_vec(mod_cd, delta, pos)
        kad.add_via(pos, net, via_size_gnd)

    # horzontal wire
    for cidx in range(2, 8):
        cidxL = cidx
        cidxR = cidx + 1
        # route
        mod_cdL = f'CD{cidxL}'
        mod_cdR = f'CD{cidxR}'
        mod_rL = f'R{cidxL}1'
        mod_rR = f'R{cidxR}1'
        ctr_dy = 4
        if cidx in [3]:
            rctr = kad.calc_pos_from_pad(mod_cdR, '2', (pos_y_wire_via_set[cidxR][idx_ranges[cidxR][1]] + ctr_dy, 3))
            prm_row = (Dird, 90, -90, kad.inf, rctr)
        elif cidx in [2, 4, 6]:
            lctr = kad.calc_pos_from_pad(mod_cdL, '2', (pos_y_wire_via_set[cidxL][idx_ranges[cidxR][0]] - ctr_dy, 0))
            rctr = kad.calc_pos_from_pad(mod_cdR, '2', (pos_y_wire_via_set[cidxR][idx_ranges[cidxR][1]] + ctr_dy, 4))
            if cidx in [2]:
                prm_row = (Dird, 90, [(-90, rctr), -70], kad.inf, lctr)
            else:
                prm_row = (Dird, [(90, lctr), 180 - 55], -90, kad.inf, rctr)
        elif cidx in [5, 7]:
            lctr = kad.calc_pos_from_pad(mod_cdL, '2', (pos_y_wire_via_set[cidxL][idx_ranges[cidxR][1]] + ctr_dy, 0))
            rctr = kad.calc_pos_from_pad(mod_cdR, '2', (pos_y_wire_via_set[cidxR][idx_ranges[cidxR][0]] - ctr_dy, 0))
            prm_row = (Dird, [(90, lctr), 55], -90, kad.inf, rctr)
        # wires
        if cidxL not in wire_via_col_horz_set:
            continue
        if cidxR not in wire_via_col_horz_set:
            continue
        for idx in range(len(exp_cidx_pad_width_space_nets)):
            if idx not in wire_via_col_horz_set[cidxL]:
                continue
            if idx not in wire_via_col_horz_set[cidxR]:
                continue
            wire_via_L = wire_via_col_horz_set[cidxL][idx]
            wire_via_R = wire_via_col_horz_set[cidxR][idx]
            width = exp_cidx_pad_width_space_nets[idx][2]
            kad.wire_mod_pads([(mod_rL, wire_via_L, mod_rR, wire_via_R, width, prm_row, 'F.Cu')])


def wire_exp_row_vert_col_horz():
    y_sep_exp_via = 1.6
    y_offset_exp_via = (via_size_dat[0] - w_dat) / 2

    mod_exp = 'U1'
    via_exp = {}

    def get_via_pos(ny, sign, min_ny=0):
        x = max(ny, min_ny)
        mx = 7.0  # min x
        y = x - mx
        return vec2.scale(y_sep_exp_via, (sign * x, y))

    # ROW & COL flower wiring
    # 4, 3, 2, 1, 28, ..., 18
    exp_pads = [f'{((4 - i - 1 + 28) % 28) + 1}' for i in range(15)]
    for i in range(15):
        ny = abs(i - 7)
        sy = vec2.sign(i - 7)
        dpos = get_via_pos(ny, sy, 1)
        pos = kad.calc_pos_from_pad(mod_exp, '29', dpos)
        net = kad.get_pad_net(mod_exp, exp_pads[i])
        via_exp[i] = kad.add_via(pos, net, via_size_dat)
        ctr = kad.calc_pos_from_pad(mod_exp, '29', vec2.scale(3.0, (sy, -1)))
        if ny in [0, 7]:
            prm = (Strt)
        elif ny <= 3:
            prm = (Dird, 90, [50, 45, 40][ny-1] * sy, kad.inf, ctr)
        elif ny <= 6:
            prm = (Dird, 0, [50, 45, 60][ny-4] * sy, kad.inf, ctr)
        kad.wire_mod_pads([
            (mod_exp, exp_pads[i], mod_exp, via_exp[i], w_exp, prm),
            ('U2', exp_pads[14-i], mod_exp, via_exp[i], w_exp, prm),
        ])

    # GND vias in-between
    wire_via_exp_gnd = {}
    offset_gnd_via = 0.6
    for i in range(0, 14):
        ny = abs(i - 6.5)
        sy = vec2.sign(i - 6.5)
        if ny == 0.5:
            angle = 0
            xv = 0.4
            xw = 0.4
            yv = yw = y_offset_exp_via / 2
        elif ny == 6.5:
            angle = -45
            xv = yv = y_offset_exp_via * 2
            xw = 1.4
            yw = y_offset_exp_via / 2
        else:
            angle = 65
            xv = yv = -offset_gnd_via
            xw = 1.0
            yw = y_offset_exp_via
        dpos = get_via_pos(ny, sy)
        pos_via = vec2.add(dpos, (yv * sy, -xv))
        pos_wire = vec2.add(dpos, (yw * sy, -xw))
        pos_via = kad.calc_pos_from_pad(mod_exp, '29', pos_via)
        pos_wire = kad.calc_pos_from_pad(mod_exp, '29', pos_wire)
        via_exp_gnd[i] = kad.add_via(pos_via, GND, via_size_gnd)
        wire_via_exp_gnd[i] = kad.add_via(pos_wire, GND, via_size_gnd)
        if angle == 0 or i == 0:
            continue
        prm = (Dird, 90 - angle * sy, 90)
        for layer in Cu_layers:
            kad.wire_mod_pads([(mod_exp, via_exp_gnd[i], mod_exp, wire_via_exp_gnd[i], w_gnd, prm, layer)])

    # connect GND vias on B.Cu
    for idx in range(1, 14):
        if idx in [6, 7]:
            continue
        ctr_idx = 6 if idx < 6 else 7
        prm = (Dird, 90, 0, 0)
        kad.wire_mod_pads([(mod_exp, wire_via_exp_gnd[idx], mod_exp, via_exp_gnd[ctr_idx], w_gnd, prm, 'B.Cu')])
    # connect GND vias on F.Cu
        kad.wire_mod_pads([(mod_exp, via_exp_gnd[0], mod_exp, wire_via_exp_gnd[1], w_gnd, (Dird, 90, 0, 0), 'F.Cu')])

    # wire to exp
    gnd_idx = 2
    pad_idx = 3
    gnd_angle = 65
    ctr_exp_col = kad.calc_relative_vec('SW24', (1, 2), kad.get_via_pos(wire_via_col_horz_set[2][3]))
    for idx, (cidx, pad, width, space, net) in enumerate(exp_cidx_pad_width_space_nets):
        if cidx <= 1:
            continue
        # wire angle
        dangle = gnd_angle if net == 'GND' else 90
        angle = 90
        if idx < 12:
            angle += dangle
        elif idx > 12:  # mid
            angle -= dangle

        # length to the corner
        if net == 'GND':
            l = 0
            _via_exp = wire_via_exp_gnd[gnd_idx]
            gnd_idx += 1
        else:
            l = y_offset_exp_via
            _via_exp = via_exp[pad_idx]
            pad_idx += 1
        prm = (Dird, [(angle, l), 90], 0, kad.inf, ctr_exp_col)
        kad.wire_mod_pads([(mod_exp, _via_exp, 'SW24', wire_via_col_horz_set[2][idx], width, prm, 'F.Cu')])

    for via in wire_via_exp_gnd.values():
        pcb.Delete(via)

    # expander to ROW3, ROW4, ROW5, COL1
    r_row = 2
    prm = (Dird, 0, 0, r_row)
    kad.wire_mod_pads([
        (mod_exp, via_exp[0], 'SW13', '3', w_dat, prm, 'B.Cu'),
        (mod_exp, via_exp[1], 'SW14', '3', w_dat, (Dird, [(180, y_offset_exp_via), 90], 90, r_row), 'B.Cu'),
        (mod_exp, via_exp[2], 'SW14', via_dbnc_row[1], w_dat, (Dird, [(180, y_offset_exp_via), 90], 90, r_row), 'F.Cu'),
        (mod_exp, via_exp[14], 'SW15', '2', w_dat, prm),
    ])


def remove_temporary_vias():
    for idx, via in wire_via_exp.items():
        if idx in [1, 2, 3, 5, 6]:
            continue
        pcb.Delete(via)
    for idx, via in via_led_left.items():
        if idx in ['21']:
            pcb.Delete(via)
    for vias in [wire_via_dio_col, wire_via_dbnc_vcc, wire_via_dbnc_gnd, wire_via_led_pwr_1st, wire_via_led_pwr_2nd]:
        for via in vias.values():
            pcb.Delete(via)
    for via_dict in [wire_via_row_vert_set, wire_via_col_horz_set]:
        for vias in via_dict.values():
            for via in vias.values():
                pcb.Delete(via)
                pass


# References
def set_text_prop(text, pos, angle, offset_length, offset_angle, text_angle):
    if text_angle == None:
        text.SetVisible(False)
    else:
        text.SetTextSize(pcbnew.wxSizeMM(1.0, 1.0))
        text.SetTextThickness(pcbnew.FromMM(0.18))
        pos_text = vec2.scale(offset_length, vec2.rotate(- (offset_angle + angle)), pos)
        text.SetPosition(pnt.to_unit(vec2.round(pos_text, 3), True))
        text.SetTextAngle(text_angle * 10)
        text.SetKeepUpright(False)


def set_refs(board):
    # hide value texts
    for mod in pcb.GetFootprints():
        ref = mod.Reference()
        val = mod.Value()
        val.SetVisible(False)
    refs = []
    if board == BDC:
        refs = [
            (6.4, +90, 180, ['J1']),
            (5.6, +135, 45, ['U1']),
            (5.6, -135, 135, ['U2']),
            (0, 0, 0, ['RE1']),
            (1.6, -90, 180, ['DL1', 'D65', 'C1']),
            (1.6, +90, 0, ['C2', 'C3']),
            (3.6, 0, 0, ['C4']),
            (3.6, 180, 180, ['R1']),
        ]
        # SW
        for idx in keys:
            if is_SW(idx):
                refs.append((None, None, None, [f'L{idx}', f'D{idx}', f'C{idx}']))
                refs.append((3.7, 90, 180, [f'SW{idx}']))
        # Debounce
        for col in range(1, 9):
            refs.append((3.6, 0, 0, [f'CD{col}']))
            refs.append((3.6, 0, 0, [f'R{col}1']))
            refs.append((3.6, 180, 180, [f'R{col}2']))
        for col in range(11, 13):
            refs.append((4.2, 0, 0, [f'CD{col}']))
            refs.append((4.2, 0, 0, [f'R{col}1']))
            refs.append((4.2, 0, 0, [f'R{col}2']))
        # RJ45
        for idx in '2468':
            refs.append((3.6, 0, 0, [f'JPF{idx}']))
            refs.append((3.6, 0, 180, [f'JPB{idx}']))
    if True:
        refs.append((None, None, None, [f'H{i}' for i in range(1, 9)]))
    for offset_length, offset_angle, text_angle, mod_names in refs:
        for mod_name in mod_names:
            mod = kad.get_mod(mod_name)
            if mod is None:
                continue
            pos, angle = kad.get_mod_pos_angle(mod_name)
            ref = mod.Reference()
            set_text_prop(ref, pos, angle, offset_length, offset_angle, text_angle)
            for item in mod.GraphicalItems():
                if type(item) is pcbnew.FP_TEXT and item.GetShownText() == ref.GetShownText():
                    set_text_prop(item, pos, angle, offset_length, offset_angle, text_angle)
    # J1
    if board == BDC:
        angle = kad.get_mod_angle('J1')
        pads = ['LED', 'GNDD', 'SCK', '5VD', 'NRST', '3V3', 'SDA', 'GND', 'LED']
        for idx in range(9):
            pos = kad.calc_pos_from_pad('J1', f'{idx+1}', (0, 1.8 if (idx+1) % 2 == 1 else -1.8))
            kad.add_text(pos, angle, pads[idx], 'F.SilkS', (0.8, 0.8), 0.15, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER)
        for idx in range(9):
            pos = kad.calc_pos_from_pad('J1', f'{9-idx}', (0, 1.8 if (9-idx) % 2 == 1 else -1.8))
            kad.add_text(pos, angle, pads[idx], 'B.SilkS', (0.8, 0.8), 0.15, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER)


prop_file = '../mod_props.json'


def save_mod_props():
    props = {}
    for mod in pcb.GetFootprints():
        name = mod.Reference().GetText()
        pos, angle = kad.get_mod_pos_angle(name)
        layer = kad.get_mod_layer(name)
        props[name] = (pos, angle, layer)
    with open(prop_file, 'w') as fout:
        json.dump(props, fout)


def load_mod_props():
    with open(prop_file) as fin:
        props = json.load(fin)
    return props


def main():
    # board type
    filename = pcb.GetFileName()
    # print( f'{filename = }' )
    m = re.search(r'/Mozza([^/]*)\.kicad_pcb', filename)
    assert m

    boardname = m.group(1)
    # print( f'{boardname = }' )

    board = None
    for bname, btype in [('C', BDC), ('T', BDT), ('B', BDB), ('M', BDM), ('S', BDS)]:
        if boardname[0] == bname:
            board = btype
            break
    assert board != None

    if board in [BDC, BDM, BDS]:
        pass
        # kad.add_text( (120, 24), 0, f'  Mozza62{bname} by orihikarna 2023/05/09  ',
        #     'F.Cu', (1.2, 1.2), 0.2, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER )

    # place & route
    if board in [BDC]:
        place_key_switches()
        place_mods()
        save_mod_props()
        wire_exp()
        wire_rj45()
        wire_rj45_vert_lines()
        wire_debounce_rrc_rotenc()
        wire_led()
        wire_row_led_horz_lines()
        wire_led_left_right_ends_thumb()
        wire_col_diode()
        wire_row_vert_lines()
        wire_col_horz_lines()
        wire_exp_row_vert_col_horz()
        remove_temporary_vias()
        add_boundary_gnd_vias()

    global mod_props, org
    mod_props = load_mod_props()
    org = vec2.add(mod_props['SW54'][0], vec2.scale(unit, (-1.1, 0.27)))

    set_refs(board)
    draw_edge_cuts(board)
    place_screw_holes(board)
    # logo
    for mod, angle in [('G1', -30), ('G2', 150)]:
        if kad.get_mod(mod) is not None:
            kad.move_mods((175, 35), 0, [(mod, (0, 0), angle)])

    # zones
    if board in [BDC, BDB]:
        offset = (40, 18.8)
        add_zone('GND', 'F.Cu', kad.make_rect((PCB_Width, PCB_Height), offset))
        add_zone('GND', 'B.Cu', kad.make_rect((PCB_Width, PCB_Height), offset))

    # draw top & bottom patterns
    if board in [BDB]:
        draw_bottom()


if __name__ == '__main__':
    kad.removeDrawings()
    kad.removeTracksAndVias()
    main()
    pcbnew.Refresh()
