# print("exec(open('place_and_route_rella.py').read())")
import importlib

import pcbnew
from kadpy import kad, mat2, pnt, vec2

importlib.reload(kad)
importlib.reload(pnt)
importlib.reload(vec2)
importlib.reload(mat2)

kad.UnitMM = True
kad.PointDigits = 3

# alias
Strt = kad.Straight
Dird = kad.Directed
ZgZg = kad.ZigZag

Round = kad.Round
BezierRound = kad.BezierRound
LinearRound = kad.LinearRound

# in mm
VIA_Size = [(1.2, 0.6), (1.15, 0.5), (0.92, 0.4), (0.8, 0.3)]

mod_props = {}


Cu_layers = ['F.Cu', 'B.Cu']

pcb = pcbnew.GetBoard()

GND = pcb.FindNet('GND')
VCC = pcb.FindNet('3V3')

via_size_pwr = VIA_Size[1]
via_size_dat = VIA_Size[2]
via_size_gnd = VIA_Size[3]



def add_zone(net_name, layer_name, rect):
    settings = pcb.GetZoneSettings()
    settings.m_ZoneClearance = pcbnew.FromMils(12)
    pcb.SetZoneSettings(settings)

    zone = kad.add_zone(rect, layer_name, net_name)
    zone.SetMinThickness(pcbnew.FromMils(16))
    # zone.SetThermalReliefGap( pcbnew.FromMils( 12 ) )
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMils(16))
    # zone.Hatch()


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
        ((vec2.add(board_org, (Lx * (-2 + 1/2), -Ly)), +120), Round, [Radius]),
        ((vec2.add(board_org, (0, Ly)), 0), Round, [Radius]),
        ((vec2.add(board_org, (Lx * (+2 - 1/2), -Ly)), -120), Round, [Radius]),
        ((vec2.add(board_org, (0, -Ly*2)), 180), Round, [Radius]),
    ]
    kad.draw_closed_corners(cnrs, 'Edge.Cuts', width)

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



w_pwr, r_pwr = 0.6, 1.2  # power
w_led, r_led = 0.4, 2.0  # LED dat
w_dat, r_dat = 0.4, 2.0  # row / col
w_exp, r_exp = 0.4, 1.0  # expander

w_gnd = 0.36
s_dat = 0.3
s_pwr = 0.8

s_col = 0.28
s_col2 = 0.5

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
    pass
    # hide value texts
    # for mod in pcb.GetFootprints():
    #     ref = mod.Reference()
    #     val = mod.Value()
    #     val.SetVisible(False)
    # refs = []
    # if board == Board.Circuit:
    #     refs = [
    #         (6.4, +90, 180, ['J1']),
    #         (5.6, +135, 45, ['U1']),
    #         (5.6, -135, 135, ['U2']),
    #         (0, 0, 0, ['RE1']),
    #         (1.6, -90, 180, ['DL1', 'D65', 'C1']),
    #         (1.6, +90, 0, ['C2', 'C3']),
    #         (3.6, 0, 0, ['C4']),
    #         (3.6, 180, 180, ['R1']),
    #     ]
    #     # SW
    #     for idx in keys:
    #         if is_SW(idx):
    #             refs.append((None, None, None, [f'L{idx}', f'D{idx}', f'C{idx}']))
    #             refs.append((3.7, 90, 180, [f'SW{idx}']))
    #     # Debounce
    #     for col in range(1, 9):
    #         refs.append((3.6, 0, 0, [f'CD{col}']))
    #         refs.append((3.6, 0, 0, [f'R{col}1']))
    #         refs.append((3.6, 180, 180, [f'R{col}2']))
    #     for col in range(11, 13):
    #         refs.append((4.2, 0, 0, [f'CD{col}']))
    #         refs.append((4.2, 0, 0, [f'R{col}1']))
    #         refs.append((4.2, 0, 0, [f'R{col}2']))
    #     # RJ45
    #     for idx in '2468':
    #         refs.append((3.6, 0, 0, [f'JPF{idx}']))
    #         refs.append((3.6, 0, 180, [f'JPB{idx}']))
    # if True:
    #     refs.append((None, None, None, [f'H{i}' for i in range(1, 9)]))
    #     refs.append((None, None, None, [f'G{i}' for i in range(1, 3)]))
    # for offset_length, offset_angle, text_angle, mod_names in refs:
    #     for mod_name in mod_names:
    #         mod = kad.get_mod(mod_name)
    #         if mod is None:
    #             continue
    #         pos, angle = kad.get_mod_pos_angle(mod_name)
    #         ref = mod.Reference()
    #         set_text_prop(ref, pos, angle, offset_length, offset_angle, text_angle)
    #         for item in mod.GraphicalItems():
    #             if type(item) is pcbnew.FP_TEXT and item.GetShownText() == ref.GetShownText():
    #                 set_text_prop(item, pos, angle, offset_length, offset_angle, text_angle)
    # # J1
    # if board == Board.Circuit:
    #     angle = kad.get_mod_angle('J1')
    #     pads = ['LED', 'GNDD', 'SCK', '5VD', 'NRST', '3V3', 'SDA', 'GND', 'LED']
    #     for idx in range(9):
    #         pos = kad.calc_pos_from_pad('J1', f'{idx+1}', (0, 1.8 if (idx+1) % 2 == 1 else -1.8))
    #         kad.add_text(pos, angle, pads[idx], 'F.SilkS', (0.8, 0.8), 0.15, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER)
    #     for idx in range(9):
    #         pos = kad.calc_pos_from_pad('J1', f'{9-idx}', (0, 1.8 if (9-idx) % 2 == 1 else -1.8))
    #         kad.add_text(pos, angle, pads[idx], 'B.SilkS', (0.8, 0.8), 0.15, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER)




def main():
    # place & route
    # wire_exp()
    # remove_temporary_vias()

    global mod_props, board_org
    # mod_props = load_mod_props()
    # board_org = vec2.add(mod_props['SW54'][0], vec2.scale(keysw_unit, (-1.1, 0.27)))

    # if board in [Board.Circuit]:
    #     add_boundary_gnd_vias()

    # set_refs(board)
    # draw_edge_cuts(board)
    # place_screw_holes(board)

    # draw rule area
    # if board in [Board.Spacer, Board.Middle, Board.Bottom]:
    #     draw_rule_area(board)

    # logo
    # for mod, angle in [('G1', -30), ('G2', 150)]:
    #     if kad.get_mod(mod) is not None:
    #         kad.move_mods((175.5, 34.5), 0, [(mod, (0, 0), angle)])

    # board size
    # left = int(math.floor(board_org[0]-Lx-Ly))
    # rght = int(math.ceil(board_org[0]+Lx+Ly))
    # top = int(math.floor(board_org[1]-2*Ly))
    # btm = int(math.ceil(board_org[1]+Ly))
    # width = rght - left
    # height = btm - top
    # print(f'PCB size = {width}x{height} ({2*(Lx+Ly):.4f} x {3*Ly:.4f})')

    # zones
    # rect = kad.make_rect((width, height), (left, top))
    # for layer in Cu_layers:
    #     add_zone('GND', layer, rect)

    # name
    # kad.add_text((board_org[0], btm - 5), 0,
    #                 f'Mozza62 {boardname} by orihikarna\n ver1.0 2023/06/18',
    #                 'F.Silkscreen', (2.0, 2.0), 0.4, pcbnew.GR_TEXT_HJUSTIFY_CENTER, pcbnew.GR_TEXT_VJUSTIFY_CENTER)
    # kad.add_text((board_org[0] - 15, btm - 13), -6, 'R*1 = 10k\nR*2 = 4k7\nCD* = 33n', 'B.Silkscreen', (1.2, 1.2), 0.3)


if __name__ == '__main__':
    kad.removeDrawings()
    kad.removeTracksAndVias()
    main()
    pcbnew.Refresh()
