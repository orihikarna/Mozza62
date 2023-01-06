import json
from turtle import color
import numpy as np
import os
import sys
import collections
from PIL import Image, ImageDraw, ImageFont

kbd_name = 'hermit62'

anti_alias_scaling = 4

fontpath = "/System/Library/Fonts/Courier.dfont"
font = ImageFont.truetype( fontpath, size = 28 * anti_alias_scaling )

def vec2( x, y ):
    return np.array( [x, y] )

def mat2_rot( deg ):
    th = deg / 180 * np.pi
    c = np.cos( th )
    s = np.sin( th )
    return np.array([[c, s], [-s, c]])

def round_corner( radius, fill ):
    """Draw a round corner"""
    corner = Image.new( 'RGBA', (radius, radius), (0, 0, 0, 0) )
    draw = ImageDraw.Draw( corner )
    draw.pieslice( (0, 0, radius * 2, radius * 2), 180, 270, fill = fill )
    return corner

def get_key_image( size, radius, name, fill ):
    """Draw a rounded rectangle"""
    w, h = size[0], size[1]
    sz = int( max( w, h ) * 1.5 )
    rect = Image.new( 'RGBA', (sz, sz), (255, 255, 255, 0) )
    draw = ImageDraw.Draw( rect )
    mx = int( (sz - w) / 2 )
    my = int( (sz - h) / 2 )
    draw.rectangle( (mx, my + radius, mx + w, my + h - radius), fill = fill )
    draw.rectangle( (mx + radius, my, mx + w - radius, my + h), fill = fill )
    corner = round_corner( radius, fill )
    rect.paste( corner, (mx, my) )
    rect.paste( corner.rotate(  90 ), (mx, my + h - radius) )# Rotate the corner and paste it
    rect.paste( corner.rotate( 180 ), (mx + w - radius, my + h - radius) )
    rect.paste( corner.rotate( 270 ), (mx + w - radius, my) )
    # name
    tw, th = draw.textsize( name, font )
    draw.text( (sz / 2 - tw / 2, sz / 2 - th / 2), name, "DarkSlateGrey", font )
    return rect, sz

def calc_bezier_point( pnts, t ):
    num_pnts = len( pnts )
    tmp = [np.array( [0, 0] ) for n in range( num_pnts )]
    s = 1 - t
    for n in range( num_pnts ):
        tmp[n] = pnts[n]
    for L in range( num_pnts - 1, 0, -1 ):
        for n in range( L ):
            tmp[n] = s * tmp[n] + t * tmp[n+1]
    return tmp[0]

def calc_bspline( pnts, num_divs=1 ):
    ret = []
    N = len( pnts )
    for n in range( N ):
        p = pnts[n]
        q = pnts[(n+1) % N]
        r = pnts[(n+2) % N]
        s = pnts[(n+3) % N]
        for t in np.linspace( 0, 1, num_divs ):
            if False:
                a = (1-t)*(1-t)/2
                b = -t*t + t + 1/2
                c = t*t/2
                ret.append( a * p + b * q + c * r )
            else:
                a = (1 - 3*t + 3*t*t - t*t*t)/6
                b = (4 - 6*t*t + 3*t*t*t)/6
                c = (1 + 3*t + 3*t*t - 3*t*t*t)/6
                d = (t*t*t)/6
                ret.append( a * p + b * q + c * r + d * s )
    return ret

class keyboard_key:
    def __init__( self, name, prop ):
        self.name = name
        self.prop = prop
        # topleft position
        self.x  = self.getProperty( "x", 0 )
        self.y  = self.getProperty( "y", 0 )
        # rotation center
        self.rx = self.getProperty( "rx", 0 )
        self.ry = self.getProperty( "ry", 0 )
        # rotation angle
        self.r  = self.getProperty( "r", 0 )
        # key size
        self.w  = self.getProperty( "w", 1 )
        self.h  = self.getProperty( "h", 1 )

    def getProperty( self, key: str, default_value ):
        return self.prop[key] if key in self.prop else default_value

    def getCenterPos( self ):
        cx = self.x + self.w / 2 - self.rx
        cy = self.y + self.h / 2 - self.ry
        ctr = vec2( self.rx, self.ry ) + vec2( cx, cy ) @ mat2_rot( self.r )
        return ctr

class keyboard_layout:
    def __init__( self ):
        self.meta = {}
        self.keys = []

    def print( self ):
        for k, v in self.meta.items():
            print( "meta: {} -> {}".format( k, v ) )
        keys = []
        for key in self.keys:
            ps = ""
            for k, v in key.prop.items():
                if v != 0:
                    ps += ", {}={}".format( k, v )
            name = key.name.replace( '\n', ',' )
            #print( "key '{}' {}".format( name, ps[2:] ) )
            ctr = key.getCenterPos()
            keys.append( (name, ctr, key.r) )
        max_x = max( map( lambda vals: vals[1][0], keys ) )
        min_y = min( map( lambda vals: vals[1][1], keys ) )
        keys.sort( key = lambda vals: -vals[1][0] )
        for name, q, r in keys:
            print( "    ['{}', {:.3f}, {:.3f}, {:.1f}],".format( name[-1], (q[0] - max_x), (q[1] - min_y), r ) )

    def write_png( self, path: str, unit, thickness, paper_size, arc_pnts ):
        # 2560 x 1600, 286mm x 179mm, MacBook size
        scale = 2560.0 / 286.0 / 2 * anti_alias_scaling
        size = scale * paper_size
        paper_ctr = size / 2
        L = scale * unit
        Th = thickness / unit

        xctr = np.mean( list( map( lambda k: k.getCenterPos()[0], self.keys ) ) )

        image = Image.new( 'RGBA', (int( np.ceil( size[0] ) ), int( np.ceil( size[1] ) )), ( 255, 255, 255, 255 ) )
        draw = ImageDraw.Draw( image )
        for key in self.keys:
            ctr = key.getCenterPos()
            if ctr[0] < xctr:
                continue
            w, h, rot, name = key.w, key.h, key.r, key.name

            ctr *= L
            ctr += paper_ctr
            if name.startswith( '>' ):
                egg_ctr = ctr
            dim = L * vec2( w - 2 * Th, h - 2 * Th )
            key_image, rsz = get_key_image( (int( dim[0] ), int( dim[1] )), int( L/12 ), name, "violet" )
            key_image = key_image.rotate( -rot )
            pos = ctr - vec2( rsz, rsz ) / 2
            if name.startswith( 'RE' ):
                r = 41/2 * L / unit
                draw.ellipse( (ctr[0] - r, ctr[1] - r, ctr[0] + r, ctr[1] + r), fill='gray' )
            image.paste( key_image, (int( pos[0] ), int( pos[1] )), key_image )

        def conv_pnts( in_pnts ):
            pnts = []
            for xy in in_pnts:
                pnt = xy * L + paper_ctr
                pnts.append( (pnt[0], pnt[1]) )
            return pnts

        outline = calc_bspline( arc_pnts, 10 )
        draw.line( conv_pnts( arc_pnts ), width=2, fill='red' )
        draw.line( conv_pnts( outline ), width=10, fill='black' )

        xsize = int( round( size[0] / anti_alias_scaling ) )
        ysize = int( round( size[1] / anti_alias_scaling ) )
        image = image.resize( (xsize, ysize), Image.ANTIALIAS )
        image.save( path )

    def write_scad( self, path: str, unit: float, arc_pnts ):
        xctr = np.mean( list( map( lambda k: k.getCenterPos()[0], self.keys ) ) )
        with open( path, 'w' ) as fout:
            fout.write( f'key_w = {unit};\n' )
            fout.write( f'key_h = {unit};\n' )
            fout.write( 'key_pos_angles = [\n' )
            idx = 0
            for key in self.keys:
                ctr = key.getCenterPos()
                if ctr[0] < xctr:
                    continue
                w, h, rot = key.w, key.h, key.r

                ctr *= unit
                w *= unit
                h *= unit
                fout.write( '    [{:.3f}, {:.3f}, {:.3f}, {:.3f}, {:.3f}, {}, "{}"],\n'.format( ctr[0], -ctr[1], -rot, w, h, idx, key.name ) )
                idx += 1
            fout.write( '];\n' )

            if True:
                fout.write( 'edgecuts=[' )
                outline = calc_bspline( arc_pnts, 16 )
                for idx, pnt in enumerate( outline ):
                    if idx % 8 == 0:
                        fout.write( '\n  ' )
                    pnt *= unit
                    fout.write( f'[{pnt[0]:.3f}, {pnt[1]:.3f}], ' )
                fout.write( '\n];\n' )

    def write_kicad( self, fout, unit: float, arc_pnts ):
        xctr = np.mean( list( map( lambda k: k.getCenterPos()[0], self.keys ) ) )
        key_cols = [
            ['rj45', None, '|', 'Entr', 'Raise'],
            ['6', 'Y', 'H', 'N', 'Shift'],
            ['7', 'U', 'J', 'M', 'Space'],
            ['8', 'I', 'K', ',', 'RE'],
            ['9', 'O', 'L', '.'],
            ['0', 'P', ';', '/'],
            ['-', '@', ':'],
            [None, '[', ']', '_'],
        ]
        fout.write( 'keys = {\n' )
        for col in range( len( key_cols ) ):
            for row, name in enumerate( key_cols[col] ):
                if name is None:
                    continue
                key = None
                for _key in self.keys:
                    if _key.getCenterPos()[0] <= xctr:
                        continue
                    if _key.name.find( name ) >= 0:
                        key = _key
                        break
                (x, y, r, rx, ry, w, h) = (key.x, key.y, key.r, key.rx, key.ry, key.w, key.h)
                # px = x - rx + w / 2
                # py = y - ry + h / 2
                # t = vec2( rx, ry ) + vec2( px, py ) @ mat2_rot( r )
                keyidx = f'{col+1}{row+1}'
                t = key.getCenterPos()
                t *= unit
                w *= unit
                h *= unit
                fout.write( '    \'{}\' : [{:.3f}, {:.3f}, {:.3f}, {:.3f}, {:.1f}], # {}\n'.format( keyidx, t[0], -t[1], w, h, -r, key.name[0] ) )
        fout.write( '}\n' )

        if True:
            fout.write( 'EdgeCuts = [' )
            outline = calc_bspline( arc_pnts, 16 )
            for idx, pnt in enumerate( outline ):
                if idx % 4 == 0:
                    fout.write( '\n  ' )
                pnt *= unit
                fout.write( f'[{pnt[0]:.3f}, {pnt[1]:.3f}], ' )
            fout.write( '\n]\n' )

    def save( self, path: str ):
        data = []
        data.append( self.meta )
        for key in self.keys:
            prop = collections.OrderedDict()
            prop['w']  = key.w
            prop['h']  = key.h
            prop['r']  = key.r
            prop['rx'] = key.rx
            prop['ry'] = key.ry
            prop['x']  = key.x - key.rx
            prop['y']  = key.y - key.ry
            row = [prop, key.name]
            data.append( row )
        with open( path, 'w' ) as fout:
            json.dump( data, fout, indent = 4)

    @staticmethod
    def load( path: str ):
        kbd = keyboard_layout()
        with open( path ) as fin:
            cfg = json.load( fin )
            #print( "{}".format( json.dumps( cfg, indent=4 ) ) )
            kbd.meta = cfg[0]

            prop = {}
            prop["y"] = 0
            prop["rx"] = 0
            for row in cfg[1:]:
                prop["x"] = prop["rx"]
                for item in row:
                    if type( item ) is str:
                        key = keyboard_key( item, prop.copy() )
                        kbd.keys.append( key )
                        prop["x"] += key.w
                    else:
                        for key, val in item.items():
                            if key in ("x", "y"):
                                prop[key] += val
                            else:
                                prop[key] = val
                                if key == "rx":
                                    prop["x"] = val
                                elif key == "ry":
                                    prop["y"] = val
                prop["y"] += key.h
        return kbd

class key_layout_maker:
    def __init__( self ):
        self.data = []

    def add_col( self, angle, org, dx, names1, names2, ydir = -1, keyw = 1, keyh = 1 ):
        for hand_idx, names in enumerate( [names1, names2]):
            # if hand_idx in [0]:# 0 = right
            if hand_idx in [1]:# 1 = left
                pass
                #continue
            xsign = [+1, -1][hand_idx]
            prop = collections.OrderedDict()
            prop["r"]  = xsign * angle
            prop["rx"] = xsign * org[0]
            prop["ry"] = org[1]
            prop["x"] = -keyw / 2.0
            prop["y"] = -keyh / 2.0
            prop["w"] = keyw
            prop["h"] = keyh
            row = [prop]
            x, y = 0, 0
            for idx, name in enumerate( names ):
                if name == '':
                    continue
                row.append( { "x" : x, "y" : y, "w" : keyw, "h" : keyh } )
                row.append( name )
                x = -keyw + dx * xsign
                y = keyh * ydir
            self.data.append( row )

def make_kbd_layout( unit, output_type ):

    # Left hand
    thumbsL = ["Alt", "Ctrl", "Lower"]
    col_Gui = ["Shift", "Tab", "Win"]
    col_Tab = ["", "Caps", "Prt", "ESC"]
    col_Z = ["Z", "A", "Q", "!\n1"]
    col_X = ["X", "S", "W", "\"\n2"]
    col_C = ["C", "D", "E", "#\n3"]
    col_V = ["V", "F", "R", "$\n4"]
    col_B = ["B", "G", "T", "%\n5"]
    col_IL = ["Del", '~\n^']

    # Right hand
    col_IR = ["Entr", '|\n¥']
    col_N = ["N", "H", "Y", "&\n6"]
    col_M = ["M", "J", "U", "'\n7"]
    col_Comm = ["<\n,", "K", "I", "(\n8"]
    col_Dot  = [">\n.", "L", "O", ")\n9"]
    col_Scln = ["?\n/", "+\n;", "P", " \n0"]
    col_Cln  = ["", "*\n:", "`\n@", "=\n-"]
    col_Brac = ["_\nBsls", "]\n}", "[\n{"]
    thumbsR  = ["Space", "Shift", "Raise"]

    maker = key_layout_maker()
    maker.data.append( { "name" : kbd_name, "author" : "orihikarna" } ) # meta

    # Dot: the origin
    isHexa = True
    if output_type in ['png', 'scad']:
        if isHexa:
            angle_Dot = 26 - 30 *0
            org_Dot = vec2( 5.3, -0.5 )
        else:
            angle_Dot = 27 - 45 *1
            org_Dot = vec2( 6.0, -1 )
    elif output_type in ['kicad']:
        angle_Dot = 26
        org_Dot = vec2( 9.0, 6.0 )
    else:
        return


    ## Constants
    # pinky
    keyw_Slsh = 22.8 / unit
    keyw_Bsls = 26.0 / unit
    # thumb
    keyw12 = 22 / unit


    ## Parameters
    # pinky
    angle_Dot_Scln = -18
    angle_Dot_Slsh = -4
    dy_Cln = 0.42
    # ring (Dot)
    dx_angle_Dot = -10
    # middle (Comm)
    angle_Comm_Dot = -2
    dx_angle_Comm = -10
    # index
    angle_M_Comm = -18
    dx_angle_M = 6
    # index
    dy_Entr = 0.4
    # thumb
    delta_M_Thmb = vec2( -0.75, 1.85 )
    angle_Index_Thmb = 82
    dangles_Thmb = [-12, -12, 0]
    dys_Thmb = [0.1, 0.1, 0]


    ## Rules
    # Ring finger: Dot
    dx_Dot_L = np.tan( np.deg2rad( dx_angle_Dot ) )
    print( f'dx_Dot = {dx_Dot_L * unit:.6f}' )
    #
    org_9 = org_Dot + 3 * vec2( dx_Dot_L, -1 ) @ mat2_rot( angle_Dot )

    # Middle finger: Comm(,)
    angle_Comm = angle_Comm_Dot + angle_Dot
    dx_Comm_K = np.tan( np.deg2rad( dx_angle_Comm ) )
    print( f'dx_Comma = {dx_Comm_K * unit:.6f}' )
    org_Comm = org_Dot \
         + vec2( -0.5, +0.5 ) @ mat2_rot( angle_Dot ) \
         + vec2( -0.5, -0.5 ) @ mat2_rot( angle_Comm )
    #
    org_8 = org_Comm + 3 * vec2( dx_Comm_K, -1 ) @ mat2_rot( angle_Comm )

    # Index finger: M, N
    angle_Index = angle_M_Comm + angle_Comm
    dx_M_J = np.tan( np.deg2rad( dx_angle_M ) )
    print( f'dx_Index = {dx_M_J * unit:.6f}' )
    org_M = org_Comm \
        + vec2( -0.5, +0.5 ) @ mat2_rot( angle_Comm ) \
        + vec2( -0.5, -0.5 ) @ mat2_rot( angle_Index )
    org_N = org_M + vec2( -1, 0 ) @ mat2_rot( angle_Index )
    #
    org_6 = org_N + 3 * vec2( dx_M_J, -1 ) @ mat2_rot( angle_Index )

    # Inner most
    angle_Inner_Index = np.rad2deg( np.arcsin( dx_M_J / dy_Entr ) )
    angle_Inner = angle_Inner_Index + angle_Index
    print( f'angle_Inner_Index = {angle_Inner_Index:.6f}' )
    org_Inner = org_N \
        + vec2( -0.5, -0.5 ) @ mat2_rot( angle_Index ) \
        + vec2( -0.5, 0.5 - dy_Entr ) @ mat2_rot( angle_Inner )

    _dy = 1 - dy_Entr * np.cos( np.deg2rad( angle_Inner_Index ) )
    dx_Entr_Yen = - _dy * np.sin( np.deg2rad( angle_Inner_Index ) )
    print( f'dx_Inner = {dx_Entr_Yen * unit:.6f}' )
    #
    org_Yen  = org_Inner + vec2( dx_Entr_Yen, -1 ) @ mat2_rot( angle_Inner )
    org_Conn = org_Yen   + vec2( dx_Entr_Yen - 0.05, -1 ) @ mat2_rot( angle_Inner )

    # Pinky finger: top
    angle_PinkyTop = angle_Dot + angle_Dot_Scln
    # Scln(;)
    dy_Scln = 1 - dx_Dot_L / np.sin( np.deg2rad( angle_Dot_Scln ) )
    org_Scln = org_Dot \
        + vec2( +0.5, -0.5 ) @ mat2_rot( angle_Dot ) \
        + vec2( +0.5, dy_Scln - 0.5) @ mat2_rot( angle_PinkyTop )
    dx_Scln_P = dy_Scln * np.tan( np.deg2rad( -angle_Dot_Scln ) )
    print( f'dx_Pinky = {dx_Scln_P * unit:.6f}' )
    exit()
    # Cln(:), RBrc(])
    org_Cln = org_Scln + vec2( +1, dy_Cln ) @ mat2_rot( angle_PinkyTop )
    org_RBrc = org_Cln + vec2( +1, dy_Cln ) @ mat2_rot( angle_PinkyTop )
    #
    org_Mnus = org_Cln + 2 * vec2( dx_Scln_P, -1 ) @ mat2_rot( angle_PinkyTop )
    org_LBrc = org_RBrc + vec2( dx_Scln_P, -1 ) @ mat2_rot( angle_PinkyTop )

    # Pinky finger: bottom
    angle_PinkyBtm = angle_Dot + angle_Dot_Slsh
    # Slsh(/)
    br_Dot = org_Dot + vec2( +0.5, +0.5 ) @ mat2_rot( angle_Dot )
    bl_Cln = org_Cln + vec2( -0.5, +0.5 ) @ mat2_rot( angle_PinkyTop )
    pt = (bl_Cln - br_Dot) @ mat2_rot( -angle_Dot )
    _dy = pt[1] - np.tan( np.deg2rad( angle_Dot_Slsh ) ) * pt[0]
    org_Slsh = org_Dot \
        + vec2( +0.5, _dy + 0.5 ) @ mat2_rot( angle_Dot ) \
        + vec2( keyw_Slsh * 0.5, 0.5 ) @ mat2_rot( angle_PinkyBtm )

    # Bsls(\)
    bl_RBrc = org_RBrc + vec2( -0.5, +0.5 ) @ mat2_rot( angle_PinkyTop )
    _dy = ((bl_RBrc - org_Slsh) @ mat2_rot( -angle_PinkyBtm ))[1]
    org_Bsls = org_Slsh + vec2( (keyw_Slsh + keyw_Bsls) * 0.5, 0.5 + _dy ) @ mat2_rot( angle_PinkyBtm )

    # Thumbs row
    keyws = [keyw12, keyw12, keyw12]
    angle_Thmb = angle_Index + angle_Index_Thmb
    org_Thmb = org_M + delta_M_Thmb @ mat2_rot( angle_Index )
    angle_Thmbs = []
    org_Thmbs = []
    for idx, name in enumerate( thumbsR ):
        angle_Thmbs.append( angle_Thmb + 180 )
        org_Thmbs.append( org_Thmb )
        maker.add_col( angle_Thmb + 180, org_Thmb, 0, [name], [thumbsL[idx]], keyw = keyws[idx] )
        org_Thmb += vec2( +keyws[idx] / 2, +0.5 ) @ mat2_rot( angle_Thmb )
        angle_Thmb += dangles_Thmb[idx]
        org_Thmb += vec2( -keyws[idx] / 2 - dys_Thmb[idx], +0.5 ) @ mat2_rot( angle_Thmb )


    ### add columns
    maker.add_col( angle_Index,  org_N,     dx_M_J,    col_N,    col_B )
    maker.add_col( angle_Index,  org_M,     dx_M_J,    col_M,    col_V )
    maker.add_col( angle_Comm,   org_Comm,  dx_Comm_K, col_Comm, col_C )
    maker.add_col( angle_Dot,    org_Dot,   dx_Dot_L,  col_Dot,  col_X )
    #
    maker.add_col( angle_PinkyTop, org_Scln, dx_Scln_P, col_Scln[1:], col_Z[1:] )
    maker.add_col( angle_PinkyTop, org_Cln,  dx_Scln_P, col_Cln[1:],  col_Tab[1:] )
    maker.add_col( angle_PinkyTop, org_RBrc, dx_Scln_P, col_Brac[1:], col_Gui[1:] )
    #
    maker.add_col( angle_PinkyBtm, org_Slsh, 0, col_Scln[0:1], col_Z[0:1],   keyw = keyw_Slsh )
    maker.add_col( angle_PinkyBtm, org_Bsls, 0, col_Brac[0:1], col_Gui[0:1], keyw = keyw_Bsls )
    #
    maker.add_col( angle_Inner, org_Inner, dx_Entr_Yen, col_IR, col_IL )
    maker.add_col( angle_Inner, org_Conn, 0, {'rj45'}, {'rj45'}, keyw = (15.24+1.27+0.4) / unit, keyh = (15.08+0.4) / unit )
    #
    # Rotary encoder
    angle_RotEnc = angle_Index
    org_RotEnc = org_Dot + vec2( -0.5, 1.75 ) @ mat2_rot( angle_Comm )
    maker.add_col( angle_RotEnc, org_RotEnc, 0, {'RE_R'}, {'RE_L'}, keyw = 13.7 / unit, keyh = 12.7 / unit )

    # edge cuts
    arc_pnts = []
    if isHexa: # hexagonal
        R = mat2_rot( -30*0 )
        org = org_Dot + (-6.9, 0.3)
        P = np.array( [[1, 0], [1/2, np.sqrt(3)/2]] ) * 2.9
        d1 = 0.268
        d2 = 0.25
        deltas = [
            (0, 1),
            (1, 0), (1, 0), (1, 0),
            (1, -1),
            (0, -1), (0, -1),
            (-1, 0), (-1, 0),
            (-1, 1), (-1, 1),
        ]
        ks_set = [
            [d1, 1-d1],
            [d1, 1-d1], [d1, 1-d1], [d1, 1-d1],
            [d1, 1-d1],
            #
            [d1, 1-d2], [d2, 1-d2],
            [d2, 1-d2], [d2, 1-d2],
            [d2, 1-d2], [d2, 1-d1],
        ]
        deltas = np.array( deltas )
        pnt = org.copy()
        for n, delta in enumerate(deltas):
            for k in ks_set[n]:
                vec = pnt + k * (delta @ P)
                vec = (vec - org_Dot) @ R + org_Dot
                arc_pnts.append( vec )
            pnt += delta @ P

    if not isHexa: # octagonal
        R = mat2_rot( -45 *1 )
        th = np.deg2rad( 10 )
        P1 = np.eye(2)
        P2 = np.array( [[1, 0], [np.sin(th), np.cos(th)]] )
        Ps = [P1, P2]
        org = org_Dot + vec2(-3.6, -4.7)

        deltas = [(4, 0), (2, 2), (0, 3), (-1, 1), (-6, 0), (-1, -1), (0, -3), (2, -2)]
        deltas = np.array( deltas ) * 1.28
        pnt = org.copy()
        for idx, delta in enumerate(deltas):
            for k in np.arange( 0, 1, 0.1 ):
                vec = pnt + k * (delta @ Ps[idx%1])
                vec = (vec - org_Dot) @ R + org_Dot
                arc_pnts.append( vec )
            pnt += delta @ Ps[idx%1]

    return maker.data, arc_pnts

if __name__=='__main__':

    work_dir = './'
    dst_path = os.path.join( work_dir, f'kbd-layout.json' )
    dst_scad = os.path.join( work_dir, f'kbd-layout.scad' )
    dst_png  = os.path.join( work_dir, f'kbd-layout.png' )

    unit = 17.0
    # paper_size = vec2( 297, 210 )# A4
    # paper_size = vec2( 364, 257 )# B4
    paper_size = vec2( 350, 200 )
    thickness = 0.3# mm

    for output_type in ['png', 'kicad']:
        data, arc_pnts = make_kbd_layout( unit, output_type )
        # write to json for keyboard layout editor
        with open( dst_path, 'w' ) as fout:
            json.dump( data, fout, indent = 4 )

        kbd = keyboard_layout.load( dst_path )
        # kbd.print()
        if output_type == 'png':
            kbd.write_png( dst_png, unit, thickness, paper_size, arc_pnts )
            kbd.write_scad( dst_scad, unit, arc_pnts )
        if output_type == 'kicad':
            kbd.write_kicad( sys.stdout, unit, arc_pnts )
