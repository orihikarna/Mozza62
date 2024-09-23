# exec(open('place_and_route_rella.py').read())
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

via_size_pwr = VIA_Size[1]
via_size_dat = VIA_Size[2]
via_size_gnd = VIA_Size[3]

Cu_layers = ["F.Cu", "B.Cu", "In1.Cu", "In2.Cu"]

pcb = pcbnew.GetBoard()

GND = pcb.FindNet("GND")
VCC = pcb.FindNet("3V3")

board_org = (114, 90)


def add_zone(net_name, layer_name, rect):
    settings = pcb.GetZoneSettings()
    settings.m_ZoneClearance = pcbnew.FromMils(12)
    pcb.SetZoneSettings(settings)

    zone = kad.add_zone(rect, layer_name, net_name)
    zone.SetMinThickness(pcbnew.FromMils(16))
    # zone.SetThermalReliefGap( pcbnew.FromMils( 12 ) )
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMils(16))
    # zone.Hatch()


def place_mods():
    kad.move_mods(
        board_org,
        0,
        [
            ("J1", (0, 0), 0),
            (
                None,
                (12, 3.8 - 2.54 * 3),
                0,
                [
                    # ("U1", (-18.114, 1.296 + 2.54 * 3 - 0), 90),
                    ("J3", (0, +2.54 * 3), 90),
                    ("J4", (0, -2.54 * 3), 90),
                ],
            ),
            (
                None,
                (-10.4, -9.6),
                0,
                [
                    ("R4", (1.524 * 0, 0), -90),
                    ("R1", (1.524 * 1, 0), -90),
                    ("R2", (1.524 * 2, 0), -90),
                    ("R3", (1.524 * 3, 0), -90),
                ],
            ),
            (
                None,
                (-9.398, 1.27),
                0,
                [
                    ("R11", (0, 0), -90),
                    ("R12", (1.524 * 2, 0), -90),
                ],
            ),
        ],
    )


w_pwr, r_pwr = 0.7, 1.5  # power
w_led, r_led = 0.5, 1.2  # LED dat
w_dat, r_dat = 0.4, 0.7  # row / col

r_tri = 0.7


def wire_mod():
    rj45 = "J1"
    xiao_l = "J3"
    xiao_r = "J4"
    via_left = kad.add_via_relative(rj45, "20", (-1.4, 0), via_size_pwr)
    # intra RJ45
    via_3v3_1 = kad.add_via_relative(rj45, "18", (0, -1.4 - 0.6), via_size_pwr)
    via_3v3_2 = kad.add_via_relative(rj45, "18", (-2.03, -1.4), via_size_pwr)
    kad.wire_mod_pads(
        [
            (rj45, "6", rj45, "18", w_pwr, (Dird, [(+90, 1.4), 0], 90, r_tri), "B.Cu"),
            (rj45, "6", rj45, via_3v3_1, w_pwr, (Dird, [(+90, 1.4), 0], 90, r_tri), "B.Cu"),
            (rj45, "18", rj45, via_3v3_1, w_pwr, (Strt), "B.Cu"),
            (rj45, "8", rj45, "14", w_pwr, (Strt), "In2.Cu"),
        ]
    )
    # RJ45 - xiao_r
    via_5vd = kad.add_via_relative(rj45, "4", (0, -3.8), via_size_pwr)
    kad.wire_mod_pads(
        [
            # 5VD
            (xiao_r, "1", rj45, via_5vd, w_pwr, (Dird, [(180, 1.6), 90], 90), "F.Cu"),
            (rj45, "4", rj45, via_5vd, w_pwr, (Strt), "F.Cu"),
            (rj45, "16", rj45, via_5vd, w_pwr, (Dird, [(+90, 1.6), 0], 90, r_led), "F.Cu"),
            (rj45, "16", rj45, "4", w_pwr, (Dird, [(+90, 1.6), 0], 90, r_led), "F.Cu"),
            # GND
            (xiao_r, "2", rj45, "2", w_pwr, (ZgZg, 0, 20), "In2.Cu"),
            # 3V3
            (xiao_r, "3", rj45, "6", w_pwr, (ZgZg, 0, 20), "In2.Cu"),
            # LED
            (xiao_r, "4", rj45, "9", w_led, (Dird, -45, [(-90, 1.4), 0], r_led), "In1.Cu"),
            (xiao_r, "5", rj45, "11", w_led, (Dird, -45, 90), "In1.Cu"),
            (xiao_r, "7", rj45, "21", w_led, (Dird, -45, 90), "In1.Cu"),
        ]
    )
    # RJ45 - xiao_l
    kad.wire_mod_pads(
        [
            (xiao_l, "1", rj45, "1", w_dat, (Dird, -45, 90), "In1.Cu"),
            (xiao_l, "2", rj45, "13", w_dat, (Dird, [(0, 2.6), 90], 90, r_led), "In1.Cu"),
            # NRST
            (xiao_l, "3", rj45, "5", w_dat, (ZgZg, 0, 45), "In2.Cu"),
            (xiao_l, "3", rj45, "17", w_dat, (Dird, 0, [(-90, 2.8), 0], r_led), "In2.Cu"),
            # SCK
            (rj45, "3", rj45, "15", w_dat, (Dird, [(-90, 1.6), 0], 90, r_dat), "B.Cu"),
            (xiao_l, "6", rj45, "3", w_dat, (Dird, 0, [(-90, 1.6), 0], r_dat), "B.Cu"),
            (xiao_l, "6", rj45, "15", w_dat, (Dird, 0, [(-90, 1.6), 0], r_dat), "B.Cu"),
            # SDA
            (rj45, "7", rj45, "19", w_dat, (Dird, [(-90, 1.4), 0], 90, r_dat), "F.Cu"),
            (xiao_l, "5", rj45, "7", w_dat, (Dird, 0, [(-90, 1.4), 0], r_dat), "F.Cu"),
            (xiao_l, "5", rj45, "19", w_dat, (Dird, 0, [(-90, 1.4), 0], r_dat), "F.Cu"),
        ]
    )
    # LED
    kad.wire_mod_pads(
        [
            (rj45, "24", "R4", "2", w_led, (Dird, 90, [(0, 1.25), 90], r_led), "B.Cu"),
            (rj45, "22", "R3", "2", w_led, (Dird, 90, [(0, 0.0), 90], r_led), "B.Cu"),
            (rj45, "12", "R2", "2", w_led, (Dird, 90, [(0, 1.25), 90], r_led), "B.Cu"),
            (rj45, "10", "R1", "2", w_led, (Dird, 90, [(0, 2.00), 90], r_led), "B.Cu"),
            (rj45, via_3v3_1, "R4", "1", w_pwr, (Dird, 90, 90, r_tri), "B.Cu"),
            (rj45, via_3v3_1, "R3", "1", w_pwr, (Dird, 90, 90, r_tri), "B.Cu"),
            ("R3", "1", "R4", "1", w_pwr, (Strt), "B.Cu"),
            # LED4
            (rj45, "23", rj45, via_left, w_led, (ZgZg, 90, 30), "In1.Cu"),
            (rj45, via_left, xiao_l, "4", w_led, (Dird, [(-90, 1.5), -60], [(0, 1.8), 90], r_led), "In1.Cu"),
        ]
    )
    # I2C
    kad.wire_mod_pads(
        [
            (rj45, "19", "R11", "1", w_dat, (Dird, 90, 90, r_led), "B.Cu"),
            (rj45, "15", "R12", "1", w_dat, (Dird, 90, 90, r_led), "B.Cu"),
            ("R11", "2", "R12", "2", w_dat, (Strt), "B.Cu"),
            # 3V3
            (rj45, "18", rj45, via_3v3_2, w_dat, (Dird, 90, 0, r_dat), "B.Cu"),
            (rj45, via_3v3_1, rj45, via_3v3_2, w_dat, (Dird, 90, 0, r_dat), "B.Cu"),
            (rj45, via_3v3_2, rj45, via_left, w_dat, (Dird, 0, 90, r_dat), "B.Cu"),
            (rj45, via_left, "R11", "2", w_dat, (Dird, [(-90, 1.5), -60], [(90, 2.0), 0], r_led), "B.Cu"),
        ]
    )
    for via in [via_5vd, via_3v3_1, via_3v3_2, via_left]:
        pcb.Delete(via)


# References
def set_text_prop(text, pos, angle, offset_length, offset_angle, text_angle):
    if text_angle == None:
        text.SetVisible(False)
    else:
        text.SetTextSize(pcbnew.wxSizeMM(1.0, 1.0))
        text.SetTextThickness(pcbnew.FromMM(0.18))
        pos_text = vec2.scale(offset_length, vec2.rotate(-(offset_angle + angle)), pos)
        text.SetPosition(pnt.to_unit(vec2.round(pos_text, 3), True))
        text.SetTextAngle(text_angle * 10)
        text.SetKeepUpright(False)


def draw_edge_cuts():
    width = 0.12

    Radius = 2
    Lx = 32
    Ly = 2.54 * 7
    Oy = vec2.add(kad.get_mod_pos("J3"), kad.get_mod_pos("J4"))[1] / 2
    _org = (board_org[0], Oy)
    cnrs = [
        ((vec2.add(_org, (0, -Ly / 2)), 0), Round, [Radius]),
        ((vec2.add(_org, (+Lx / 2, 0)), 90), Round, [Radius]),
        ((vec2.add(_org, (0, +Ly / 2)), 180), Round, [Radius]),
        ((vec2.add(_org, (-Lx / 2, 0)), 270), Round, [Radius]),
    ]
    kad.draw_closed_corners(cnrs, "Edge.Cuts", width)


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
    place_mods()
    wire_mod()
    draw_edge_cuts()

    # mod_props = load_mod_props()
    # board_org = vec2.add(mod_props['SW54'][0], vec2.scale(keysw_unit, (-1.1, 0.27)))

    # if board in [Board.Circuit]:
    #     add_boundary_gnd_vias()

    # set_refs(board)
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


if __name__ == "__main__":
    kad.removeDrawings()
    kad.removeTracksAndVias()
    main()
    pcbnew.Refresh()
