import json
import math
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

def vec2_find_intersection( p0, t0, p1, t1, tolerance = 1 ):
    A = vec2( t0, t1 )
    R = np.linalg.inv( A )
    B = p1 - p0
    k0, k1 = B @ R
    q0 =  k0 * t0 + p0
    q1 = -k1 * t1 + p1
    dq = np.linalg.norm( q0 - q1 )
    if dq > 1e-3:
        print( 'ERROR |q0 - q1| = {}'.format( dq ) )
    return (q1, k0, -k1)

def vec2_rotate( vec, angle ):
    th = np.deg2rad( angle )
    co = math.cos( th )
    si = math.sin( th )
    nxvec = co * vec[0] - si * vec[1]
    nyvec = si * vec[0] + co * vec[1]
    return (nxvec, nyvec)

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

    def write_png( self, path: str, unit, thickness, paper_size ):
        # 2560 x 1600, 286mm x 179mm, MacBook size
        scale = 2560.0 / 286.0 / 2 * anti_alias_scaling
        size = scale * paper_size
        L = scale * unit
        Th = thickness / unit

        image = Image.new( 'RGBA', (math.ceil( size[0] ), math.ceil( size[1] )), ( 255, 255, 255, 255 ) )
        draw = ImageDraw.Draw( image )
        for key in self.keys:
            ctr = key.getCenterPos()
            w, h, rot = key.w, key.h, key.r

            ctr *= L
            dim = L * vec2( w - 2 * Th, h - 2 * Th )
            key_image, rsz = get_key_image( (int( dim[0] ), int( dim[1] )), int( L/12 ), key.name, "DarkTurquoise" )
            key_image = key_image.rotate( -rot )
            pos = ctr - vec2( rsz, rsz ) / 2
            image.paste( key_image, (int( pos[0] ), int( pos[1] )), key_image )

        xsize = round( size[0] / anti_alias_scaling )
        ysize = round( size[1] / anti_alias_scaling )
        image = image.resize( (xsize, ysize), Image.ANTIALIAS )
        image.save( path )

    def write_scad( self, path: str, unit_w: float ):
        with open( path, 'w' ) as fout:
            fout.write( f'key_w = {unit_w};\n' )
            fout.write( f'key_h = {unit_h};\n' )
            fout.write( 'key_pos_angles = [\n' )
            idx = 0
            for key in self.keys:
                ctr = key.getCenterPos()
                w, h, rot = key.w, key.h, key.r

                ctr *= unit_w
                w *= unit_w
                h *= unit_w
                fout.write( '    [{:.3f}, {:.3f}, {:.3f}, {:.3f}, {:.3f}, {}, "{}"],\n'.format( ctr[0], -ctr[1], -rot, w, h, idx, key.name ) )
                idx += 1
            fout.write( '];\n' )

    def write_kicad( self, fout, unit_w: float ):
        fout.write( 'keys = {\n' )
        col = 1
        row = 1
        for key in self.keys:
            (x, y, r, rx, ry, w, h) = (key.x, key.y, key.r, key.rx, key.ry, key.w, key.h)
            px = x - rx + w / 2
            py = y - ry + h / 2
            t = vec2( rx, ry ) + vec2( px, py ) @ mat2_rot( r )
            keyidx = f'{col}{row}'
            row += 1
            if row == 4:
                if col == 7:
                    col += 1
                    row = 2
            elif row == 5:
                if col == 5:
                    row = 2
                elif col == 8:
                    row = 1
                else:
                    row = 1
                col += 1
            t *= unit_w
            w *= unit_w
            h *= unit_w
            fout.write( '    \'{}\' : [{:.3f}, {:.3f}, {:.3f}, {:.3f}, {:.1f}], # {}\n'.format( keyidx, t[0], -t[1], w, h, -r, key.name[0] ) )
        fout.write( '}\n' )

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
    def __init__( self, xctr, keyh ):
        self.data = []
        self.xctr = xctr
        self.keyh = keyh

    def add_col( self, angle, org, dxs, names1, names2, ydir = -1, keyw = 1 ):
        keyh = self.keyh
        for hand_idx, names in enumerate( [names1, names2]):
            # if hand_idx in [0]:# 0 = right
            if hand_idx in [1]:# 1 = left
                pass
                #continue
            xsign = [+1, -1][hand_idx]
            prop = collections.OrderedDict()
            prop["r"]  = xsign * angle
            prop["rx"] = xsign * org[0] + self.xctr
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
                x = -keyw + dxs[min( idx, len( dxs ) - 1 )] * xsign
                y = keyh * ydir
            self.data.append( row )

def make_kbd_layout( unit_w, unit_h, paper_size, output_type ):

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

    xctr = (paper_size[0] / 2.0) / unit_w
    keyh = unit_h / unit_w

    maker = key_layout_maker( xctr, keyh )
    maker.data.append( { "name" : kbd_name, "author" : "orihikarna" } ) # meta

    # Comma: the origin  
    if output_type in ['png']:
        angle_Comm = 0
        org_Comm = vec2( 4.5, 4.3 )
    elif output_type in ['scad']:
        angle_Comm = 45
        org_Comm = vec2( 5.6, 4.3 )
    elif output_type in ['kicad']:
        # angle_Comm = 0
        # angle_Comm = 16
        angle_Comm = 6.351954683901843
        org_Comm = vec2( -4.9, 4.0 )
    else:
        return

    # parameters
    angle_M_Comm = -16
    # print( f'angle_M_Comm = {angle_M_Comm:.6f}' )
    dy_Cln = 0.17
    dy_Entr = 0.5

    angle_Index_Thmb = 80
    dangles_Thmb = [-20, -20, 0]
    delta_M_Thmb = vec2( -0.86, 2.22 )
    dys_Thmb = [-0.1, 0.1, 0]

    ## Middle finger: Comm(,)
    dx_Comm_8 = 3 * math.tan( np.deg2rad( angle_M_Comm / 2 * keyh ) )
    dx_I_8 = 0
    dx_Comm_K = dx_K_I = (dx_Comm_8 - dx_I_8) / 2

    ## Index finger: M, N
    angle_Index = angle_M_Comm + angle_Comm
    org_M = org_Comm \
        + vec2( -0.5, +0.5 * keyh ) @ mat2_rot( angle_Comm ) \
        + vec2( -0.5, -0.5 * keyh ) @ mat2_rot( angle_Index )
    org_N = org_M + vec2( -1, 0 ) @ mat2_rot( angle_Index )

    dx_M_7 = -dx_Comm_8
    dx_U_7 = -math.sin( np.deg2rad( angle_M_Comm ) ) * keyh
    dx_J_U = dx_U_7 * 0.8
    dx_M_J = dx_M_7 - (dx_J_U + dx_U_7)
    # print( f'dx_M_J={dx_M_J:.3f}, dx_J_U={dx_J_U:.3f}, dx_U_7={dx_U_7:.3f}')

    ## Inner most
    angle_Inner = angle_Index# + math.atan2( dx_M_J, np.rad2deg( (1 - dy_Entr) * keyh ) )
    org_Inner = org_N \
        + vec2( -0.5, (+0.5 - dy_Entr) * keyh ) @ mat2_rot( angle_Index ) \
        + vec2( -0.5, -keyh/2 ) @ mat2_rot( angle_Inner )

    ## Ring finger: Dot
    angle_Dot = angle_Comm
    org_Dot = org_Comm + vec2( +1, 0 ) @ mat2_rot( angle_Dot )
    dx_Dot_L = dx_Comm_8 / 3

    ## Pinky finger: top
    angle_Dot_Scln = -angle_M_Comm
    if angle_Dot_Scln == 0:
        dy_Scln = 0.5 * keyh
    else:
        dy_Scln = keyh + dx_Dot_L / math.sin( np.deg2rad( angle_Dot_Scln ) )
    if False:
        dy_Scln *= ratio
        angle_Dot_Scln = math.asin( dx_Dot_L / (dy_Scln - keyh) ) * rad2deg
    print( f'angle_Dot_Scln={angle_Dot_Scln}, dx_Dot_L={dx_Dot_L}, dy_Scln={dy_Scln}')
    # Scln(;)
    angle_PinkyTop = angle_Dot - angle_Dot_Scln
    tr_Dot = org_Dot + vec2( +0.5, -0.5 * keyh ) @ mat2_rot( angle_Dot )
    org_Scln = tr_Dot + vec2( +0.5, dy_Scln - 0.5 * keyh) @ mat2_rot( angle_PinkyTop )
    dx_Scln_P = dy_Scln * math.tan( np.deg2rad( angle_Dot_Scln ) )
    # Cln(:), RBrc(])
    org_Cln = org_Scln + vec2( +1, dy_Cln ) @ mat2_rot( angle_PinkyTop )
    org_RBrc = org_Cln + vec2( +1, dy_Cln ) @ mat2_rot( angle_PinkyTop )

    ## Pinky finger: bottom
    angle_Pinky_Btm_Top = np.rad2deg( math.atan2( dy_Cln, 1 ) )# 1 == keyw
    angle_PinkyBtm = angle_PinkyTop + angle_Pinky_Btm_Top
    print( f'angle_PinkyBtm = {angle_PinkyBtm}' )
    keyw_Slsh = 1.25 + 0.1
    keyw_Bsls = 1.5 + 0.12
    # Slsh(/)
    br_Dot = org_Dot + vec2( +0.5, +0.5 * keyh ) @ mat2_rot( angle_Dot )
    bl_Scln = org_Scln + vec2( -0.5, +0.5 * keyh ) @ mat2_rot( angle_PinkyTop )
    tl_Slsh = vec2_find_intersection( bl_Scln, vec2( 1, 0 ) @ mat2_rot( angle_PinkyBtm ),
                                      br_Dot,  vec2( 1, 0 ) @ mat2_rot( angle_Dot + 90 ) )[0]
    org_Slsh = tl_Slsh + vec2( keyw_Slsh / 2, +0.5 * keyh ) @ mat2_rot( angle_PinkyBtm )
    # Bsls(\)
    org_Bsls = org_Slsh + vec2( (keyw_Slsh + keyw_Bsls) / 2, 0 ) @ mat2_rot( angle_PinkyBtm )

    ### add columns
    dxs_Index = [dx_M_J, dx_J_U, dx_U_7]
    maker.add_col( angle_Index, org_N, dxs_Index, col_N, col_B )
    maker.add_col( angle_Index, org_M, dxs_Index, col_M, col_V )
    maker.add_col( angle_Comm,  org_Comm, [dx_Comm_K, dx_K_I, dx_I_8], col_Comm, col_C )
    maker.add_col( angle_Dot,   org_Dot,  [dx_Dot_L, dx_Dot_L, dx_Dot_L], col_Dot, col_X )
    #
    maker.add_col( angle_PinkyBtm, org_Slsh, [0], col_Scln[0:1], col_Z[0:1], keyw = keyw_Slsh )
    maker.add_col( angle_PinkyTop, org_Scln, [dx_Scln_P], col_Scln[1:], col_Z[1:] )
    #
    maker.add_col( angle_PinkyTop, org_Cln,  [dx_Scln_P], col_Cln[1:], col_Tab[1:] )
    #
    maker.add_col( angle_PinkyBtm, org_Bsls, [0], col_Brac[0:1], col_Gui[0:1], keyw = keyw_Bsls )
    maker.add_col( angle_PinkyTop, org_RBrc, [dx_Scln_P], col_Brac[1:], col_Gui[1:] )

    # add the thumb row
    keyw12 = (1.25 * 19.05 - (19.05 - unit_w)) / 19.05
    keyws = [keyw12, keyw12, 1]
    # keyw12 = 1.25
    keyw = keyw12

    angle_Thmb = angle_Index_Thmb + angle_Index
    org_Thmb = org_M + delta_M_Thmb @ mat2_rot( angle_Index )
    for idx, name in enumerate( thumbsR ):
        maker.add_col( angle_Thmb + 180, org_Thmb, [0], [name], [thumbsL[idx]], keyw = keyws[idx] )
        org_Thmb += vec2( +keyw / 2, +0.5 * keyh ) @ mat2_rot( angle_Thmb )
        angle_Thmb += dangles_Thmb[idx]
        org_Thmb += vec2( -keyw / 2 - dys_Thmb[idx], +0.5 * keyh ) @ mat2_rot( angle_Thmb )

    # the inner most key (Enter, Del)
    maker.add_col( angle_Inner, org_Inner, [dx_M_J], col_IR, col_IL )

    return maker.data

if __name__=='__main__':

    work_dir = './'
    dst_path = os.path.join( work_dir, f'{kbd_name}-layout.json' )
    dst_scad = os.path.join( work_dir, f'{kbd_name}-layout.scad' )
    dst_png  = os.path.join( work_dir, f'{kbd_name}-layout.png' )

    unit_w = 16.8 # 17.4
    unit_h = 16.8
    # paper_size = vec2( 297, 210 )# A4
    # paper_size = vec2( 364, 257 )# B4
    paper_size = vec2( 330, 165 )
    thickness = 0.3# mm

    output_type = 'png'

    data = make_kbd_layout( unit_w, unit_h, paper_size, output_type )
    # write to json for keyboard layout editor
    with open( dst_path, 'w' ) as fout:
        json.dump( data, fout, indent = 4 )

    kbd = keyboard_layout.load( dst_path )
    # kbd.print()
    if output_type == 'png':
        kbd.write_png( dst_png, unit_w, thickness, paper_size )
    if output_type == 'scad':
        kbd.write_scad( dst_scad, unit_w )
    if output_type == 'kicad':
        kbd.write_kicad( sys.stdout, unit_w )
