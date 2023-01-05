import math
import pnt
import vec2
import mat2
import pcbnew

UnitMM = True
PointDigits = 3
inf = 1e9

def scalar_to_unit( v, mm_or_mils ):
    if mm_or_mils:
        return pcbnew.FromMM( v )
    else:
        return pcbnew.FromMils( v )

pcb = pcbnew.GetBoard()

# wire types
Straight = 0
Directed = 1
ZigZag = 2


# draw corner types
Line   = 0
Linear = 1
Bezier = 2
BezierRound  = 3
Round  = 4
Spline = 5


def sign( v ):
    if v > 0:
        return +1
    if v < 0:
        return -1
    return 0

##
## Drawings
##
def add_line_rawunit( a, b, layer = 'Edge.Cuts', width = 2):
    if a[0] == b[0] and a[1] == b[1]:
        print( "add_line_rawunit: identical", a )
        return None
    line = pcbnew.PCB_SHAPE( pcb )
    line.SetShape( pcbnew.SHAPE_T_SEGMENT )
    line.SetStart( a )
    line.SetEnd(   b )
    line.SetLayer( pcb.GetLayerID( layer ) )
    line.SetWidth( pcbnew.FromMils( width ) )
    pcb.Add( line )
    return line

def add_line( a, b, layer = 'Edge.Cuts', width = 2):
    pnt_a = pnt.to_unit( vec2.round( a, PointDigits ), UnitMM )
    pnt_b = pnt.to_unit( vec2.round( b, PointDigits ), UnitMM )
    if True:
        aa = pnt.from_unit( pnt_a, UnitMM )
        bb = pnt.from_unit( pnt_b, UnitMM )
        length = vec2.distance( bb, aa )
        if length == 0:
            print( "add_line: identical", a )
            return
        elif length < 0.001:
            #print( length, a, b )
            None
    line = pcbnew.PCB_SHAPE( pcb )
    line.SetShape( pcbnew.SHAPE_T_SEGMENT )
    line.SetStart( pnt_a )
    line.SetEnd(   pnt_b )
    line.SetLayer( pcb.GetLayerID( layer ) )
    line.SetWidth( scalar_to_unit( width, UnitMM ) )
    pcb.Add( line )
    return line

def add_lines( curv, layer, width ):
    for idx, pnt in enumerate( curv ):
        if idx == 0:
            continue
        add_line( curv[idx-1], pnt, layer, width )

def add_arc( ctr, pos, angle, layer = 'Edge.Cuts', width = 2 ):
    pnt_ctr = pnt.to_unit( vec2.round( ctr, PointDigits ), UnitMM )
    pnt_pos = pnt.to_unit( vec2.round( pos, PointDigits ), UnitMM )
    arc = pcbnew.PCB_SHAPE( pcb )
    arc.SetShape( pcbnew.SHAPE_T_ARC )
    arc.SetCenter( pnt_ctr )
    arc.SetStart( pnt_pos )
    arc.SetArcAngleAndEnd( 10 * angle, True )
    arc.SetLayer( pcb.GetLayerID( layer ) )
    arc.SetWidth( scalar_to_unit( width, UnitMM ) )
    pcb.Add( arc )
    return arc

def add_arc2( ctr, pos, end, angle, layer = 'Edge.Cuts', width = 2 ):
    pnt_ctr = pnt.to_unit( vec2.round( ctr, PointDigits ), UnitMM )
    pnt_pos = pnt.to_unit( vec2.round( pos, PointDigits ), UnitMM )
    pnt_end = pnt.to_unit( vec2.round( end, PointDigits ), UnitMM )
    arc = pcbnew.PCB_SHAPE( pcb )
    arc.SetShape( pcbnew.SHAPE_T_ARC )
    arc.SetCenter( pnt_ctr )
    arc.SetStart( pnt_pos )
    arc.SetArcAngleAndEnd( 10 * angle, True )
    arc.SetLayer( pcb.GetLayerID( layer ) )
    arc.SetWidth( scalar_to_unit( width, UnitMM ) )
    pcb.Add( arc )
    arc_start = arc.GetStart()
    arc_end = arc.GetEnd()
    if arc_start[0] != pnt_pos[0] or arc_start[1] != pnt_pos[1]:
        print( 'add_arc2: arc_start != pnt_pos !!' )
    if arc_end[0] != pnt_end[0] or arc_end[1] != pnt_end[1]:
        #print( 'arc_end != pnt_end !!' )
        add_line_rawunit( arc_end, pnt_end, layer, width )
    return arc

def add_text( pos, angle, string, layer = 'F.SilkS', size = (1, 1), thick = 5, hjustify = None, vjustify = None ):
    text = pcbnew.PCB_TEXT( pcb )
    text.SetPosition( pnt.to_unit( vec2.round( pos, PointDigits ), UnitMM ) )
    text.SetTextAngle( angle * 10 )
    text.SetText( string )
    text.SetLayer( pcb.GetLayerID( layer ) )
    text.SetTextSize( pcbnew.wxSizeMM( size[0], size[1] ) )
    text.SetTextThickness( scalar_to_unit( thick, UnitMM ) )
    text.SetMirrored( layer[0] == 'B' )
    if hjustify != None:
        text.SetHorizJustify( hjustify )
    if vjustify != None:
        text.SetVertJustify( vjustify )
    pcb.Add( text )
    return text

##
## Tracks & Vias
##
def add_track( a, b, net, layer, width ):
    pnt_a = pnt.to_unit( vec2.round( a, PointDigits ), UnitMM )
    pnt_b = pnt.to_unit( vec2.round( b, PointDigits ), UnitMM )
    track = pcbnew.PCB_TRACK( pcb )
    track.SetStart( pnt_a )
    track.SetEnd(   pnt_b )
    if net != None:
        track.SetNet( net )
    track.SetLayer( layer )
    track.SetWidth( scalar_to_unit( width, UnitMM ) )
    track.SetLocked( True )
    pcb.Add( track )
    return track

def add_via( pos, net, size ):# size [mm]
    pnt_ = pnt.to_unit( vec2.round( pos, PointDigits ), UnitMM )
    via = pcbnew.PCB_VIA( pcb )
    via.SetPosition( pnt_ )
    via.SetWidth( pcbnew.FromMM( size[0] ) )
    via.SetDrill( pcbnew.FromMM( size[1] ) )
    via.SetNet( net )
    #print( net.GetNetname() )
    via.SetLayerPair( pcb.GetLayerID( 'F.Cu' ), pcb.GetLayerID( 'B.Cu' ) )
    via.SetLocked( True )
    pcb.Add( via )
    return via

# def add_via_on_pad( mod_name, pad_name, via_size ):
#     pos, net = get_pad_pos_net( mod_name, pad_name )
#     add_via( pos, net, via_size )

def add_via_relative( mod_name, pad_name, offset_vec, size_via ):
    pos, angle, _, net = get_pad_pos_angle_layer_net( mod_name, pad_name )
    if get_mod_layer( mod_name ) == pcb.GetLayerID( 'B.Cu' ):
        offset_vec = (offset_vec[0], -offset_vec[1])
    pos_via = vec2.mult( mat2.rotate( angle ), offset_vec, pos )
    return add_via( pos_via, net, size_via )

def get_via_pos_net( via ):
    return pnt.from_unit( via.GetPosition(), UnitMM ), via.GetNet()


##
## Module
##
def get_mod( mod_name ):
    return pcb.FindFootprintByReference( mod_name )

def get_mod_layer( mod_name ):
    mod = get_mod( mod_name )
    return mod.GetLayer()

def get_mod_pos_angle( mod_name ):
    mod = get_mod( mod_name )
    return (pnt.from_unit( mod.GetPosition(), UnitMM ), mod.GetOrientation() / 10)

def set_mod_pos_angle( mod_name, pos, angle ):
    mod = get_mod( mod_name )
    if pos != None:
        mod.SetPosition( pnt.to_unit( vec2.round( pos, PointDigits ), UnitMM ) )
    mod.SetOrientation( 10 * angle )
    return mod

# mods
def move_mods( base_pos, base_angle, mods ):
    mrot = mat2.rotate( base_angle )
    for vals in mods:
        name, pos, angle = vals[:3]
        npos = vec2.add( base_pos, vec2.mult( mrot, pos ) )
        nangle = base_angle + angle
        if name == None:
            move_mods( npos, nangle, vals[3] )
        else:
            set_mod_pos_angle( name, npos, nangle )

# pad
def get_pad( mod_name, pad_name ):
    mod = get_mod( mod_name )
    return mod.FindPadByNumber( pad_name )

def get_pad_pos( mod_name, pad_name ):
    pad = get_pad( mod_name, pad_name )
    return pnt.from_unit( pad.GetPosition(), UnitMM )

def get_pad_pos_net( mod_name, pad_name ):
    pad = get_pad( mod_name, pad_name )
    return pnt.from_unit( pad.GetPosition(), UnitMM ), pad.GetNet()

def get_pad_pos_angle_layer_net( mod_name, pad_name ):
    mod = get_mod( mod_name )
    pad = get_pad( mod_name, pad_name )
    layer = get_mod_layer( mod_name )
    return (pnt.from_unit( pad.GetPosition(), UnitMM ), mod.GetOrientation() / 10, layer, pad.GetNet())

##
## Wires
##
def add_wire_straight( pnts, net, layer, width, radius = 0 ):
    assert radius >= 0
    num_pnts = len( pnts )
    rpnts = []
    for idx, curr in enumerate( pnts ):
        if idx == 0 or idx == num_pnts - 1:# first or last
            rpnts.append( curr )
            continue
        prev = pnts[idx-1]
        next = pnts[idx+1]
        avec = vec2.sub( prev, curr )
        bvec = vec2.sub( next, curr )
        alen = vec2.length( avec )
        blen = vec2.length( bvec )
        length = min( abs( radius ),
            alen / 2 if idx - 1 > 0 else alen,
            blen / 2 if idx + 1 < num_pnts - 1 else blen
        )
        if length < 10**(-PointDigits):
            rpnts.append( curr )
        else:
            num_divs = 15
            debug = False
            auvec = vec2.scale( 1 / alen, avec )
            buvec = vec2.scale( 1 / blen, bvec )
            # rpnts += vec2.make_bezier_corner( curr, auvec, buvec, length, num_divs, debug )
            rpnts += vec2.make_arc_corner( curr, auvec, buvec, length, num_divs, debug )
    for idx, curr in enumerate( rpnts ):
        if idx == 0:
            prev = rpnts[0]
            continue
        if vec2.distance( prev, curr ) > 0.01:
            add_track( prev, curr, net, layer, width )
            prev = curr

def __make_points_from_offsets( start_pos, offsets ):
    pos = start_pos
    pnts = [pos]
    for off_angle, off_len in offsets:
        pos = vec2.scale( off_len, vec2.rotate( - off_angle ), pos )
        pnts.append( pos )
    return pnts

# params: pos, (offset length, offset angle) x n
def add_wire_offsets_straight( prms_a, prms_b, net, layer, width, radius ):
    pos_a, offsets_a = prms_a
    pos_b, offsets_b = prms_b
    pnts_a = __make_points_from_offsets( pos_a, offsets_a )
    pnts_b = __make_points_from_offsets( pos_b, offsets_b )
    #
    pnts = vec2.combine_points( pnts_a, None, pnts_b )
    add_wire_straight( pnts, net, layer, width, radius )

# params: pos, angle
def add_wire_directed( prms_a, prms_b, net, layer, width, radius ):
    pos_a, angle_a = prms_a
    pos_b, angle_b = prms_b
    #
    dir_a = vec2.rotate( - angle_a )
    dir_b = vec2.rotate( - angle_b )
    xpos, _, _ = vec2.find_intersection( pos_a, dir_a, pos_b, dir_b )
    #
    # pnts = [pos_a, xpos, pos_b]
    pnts = vec2.combine_points( [pos_a], xpos, [pos_b] )
    add_wire_straight( pnts, net, layer, width, radius )

# params: pos, (offset length, offset angle) x n, direction angle
def add_wire_offsets_directed( prms_a, prms_b, net, layer, width, radius ):
    pos_a, offsets_a, angle_a = prms_a
    pos_b, offsets_b, angle_b = prms_b
    pnts_a = __make_points_from_offsets( pos_a, offsets_a )
    pnts_b = __make_points_from_offsets( pos_b, offsets_b )
    #
    apos = pnts_a[-1]
    bpos = pnts_b[-1]
    dir_a = vec2.rotate( - angle_a )
    dir_b = vec2.rotate( - angle_b )
    xpos, _, _ = vec2.find_intersection( apos, dir_a, bpos, dir_b )
    if xpos[0] is None:
        print( f'{xpos = }, {angle_a = }, {angle_b = }, {apos = }, {bpos = }')
    #
    pnts = vec2.combine_points( pnts_a, xpos, pnts_b )
    add_wire_straight( pnts, net, layer, width, radius )

# params: parallel lines direction angle
def add_wire_zigzag( pos_a, pos_b, angle, delta_angle, net, layer, width, radius ):
    mid_pos = vec2.scale( 0.5, vec2.add( pos_a, pos_b ) )
    dir = vec2.rotate( - angle )
    mid_dir1 = vec2.rotate( - angle + delta_angle )
    mid_dir2 = vec2.rotate( - angle - delta_angle )
    _, ka1, _ = vec2.find_intersection( pos_a, dir, mid_pos, mid_dir1 )
    _, ka2, _ = vec2.find_intersection( pos_a, dir, mid_pos, mid_dir2 )
    mid_angle = (angle - delta_angle) if abs( ka1 ) < abs( ka2 ) else (angle + delta_angle)
    add_wire_directed( (pos_a, angle), (mid_pos, mid_angle), net, layer, width, radius )
    add_wire_directed( (pos_b, angle), (mid_pos, mid_angle), net, layer, width, radius )

def __make_offsets_from_params( params, angle, sign ):
    offsets = []
    for off_angle, off_len in params:
        offsets.append( (angle + off_angle * sign, off_len) )
    return offsets

def __add_wire( pos_a, angle_a, sign_a, pos_b, angle_b, sign_b, net, layer, width, prms ):
    if type( prms ) == type( Straight ) and prms == Straight:
        add_wire_straight( [pos_a, pos_b], net, layer, width )
    elif prms[0] == Straight:
        prms_a, prms_b, radius = prms[1:]
        offsets_a = __make_offsets_from_params( prms_a, angle_a, sign_a )
        offsets_b = __make_offsets_from_params( prms_b, angle_b, sign_b )
        prms2_a = (pos_a, offsets_a)
        prms2_b = (pos_b, offsets_b)
        add_wire_offsets_straight( prms2_a, prms2_b, net, layer, width, radius )
    elif prms[0] == Directed:
        prms_a, prms_b = prms[1:3]
        radius = prms[3] if len( prms ) > 3 else inf
        if type( prms_a ) == type( () ):# tuple
            offsets_a = __make_offsets_from_params( prms_a[0], angle_a, sign_a )
            dir_angle_a = prms_a[1] * sign_a
        else:
            offsets_a = []
            dir_angle_a = prms_a * sign_a
        if type( prms_b ) == type( () ):# tuple
            offsets_b = __make_offsets_from_params( prms_b[0], angle_b, sign_b )
            dir_angle_b = prms_b[1] * sign_b
        else:
            offsets_b = []
            dir_angle_b = prms_b * sign_b
        prms2_a = (pos_a, offsets_a, angle_a + dir_angle_a)
        prms2_b = (pos_b, offsets_b, angle_b + dir_angle_b)
        add_wire_offsets_directed( prms2_a, prms2_b, net, layer, width, radius )
    elif prms[0] == ZigZag:
        dangle, delta_angle = prms[1:3]
        radius = prms[3] if len( prms ) > 3 else 0
        add_wire_zigzag( pos_a, pos_b, angle_a + dangle * sign_a, delta_angle, net, layer, width, radius )

def wire_mods( tracks ):
    layer_FCu = pcb.GetLayerID( 'F.Cu' )
    layer_BCu = pcb.GetLayerID( 'B.Cu' )
    for track in tracks:
        mod_a, pad_a, mod_b, pad_b, width, prms = track[:6]
        angle_a, angle_b = None, None
        layer_a, layer_b = None, None
        # check a
        if type( pad_a ) is pcbnew.PCB_VIA:# pad_a is via
            pos_a, net_a = get_via_pos_net( pad_a )
            if mod_a is not None:# ref = mod_a
                _, angle_a = get_mod_pos_angle( mod_a )
                layer_a = get_mod_layer( mod_a )
        else:# pab_a is pad
            pos_a, angle_a, layer_a, net_a = get_pad_pos_angle_layer_net( mod_a, pad_a )
        # check b
        if type( pad_b ) is pcbnew.PCB_VIA:# pad_b is via
            pos_b, net_b = get_via_pos_net( pad_b )
            if mod_b is not None:# ref = mod_b
                _, angle_b = get_mod_pos_angle( mod_b )
                layer_b = get_mod_layer( mod_b )
        else:# pad_b is pad
            pos_b, angle_b, layer_b, net_b = get_pad_pos_angle_layer_net( mod_b, pad_b )
        # 
        if angle_a == None:
            angle_a = angle_b
        if angle_b == None:
            angle_b = angle_a
        sign_a = +1 if layer_a == None or layer_a == layer_FCu else -1
        sign_b = +1 if layer_b == None or layer_b == layer_FCu else -1
        net = net_b if net_a == None else net_a
        layer = layer_b if layer_a == None else layer_a
        if net == None:
            print( 'net is None' )
        if layer == None:
            print( 'layer is None' )
        if len( track ) > 6:
            if track[6] == 'Opp':
                layer = layer_BCu if layer == layer_FCu else layer_FCu
            else:
                layer = pcb.GetLayerID( track[6] )
        __add_wire( pos_a, angle_a, sign_a, pos_b, angle_b, sign_b, net, layer, width, prms )


##
## Drawwings
##
def removeDrawings():
    # pcb.DeleteZONEOutlines()
    for draw in pcb.GetDrawings():
        pcb.Delete( draw )

def removeTracksAndVias():
    # Tracks & Vias
    for track in pcb.GetTracks():
        delete = False
        if track.IsLocked():# locked == placed by python
            delete = True
        # elif type( track ) is pcbnew.PCB_VIA:
        #     delete = True
        # elif type( track ) is pcbnew.PCB_TRACK:
        #     delete = True
        if delete:
            pcb.Delete( track )

def drawRect( pnts, layer, R = 75, width = 2 ):
    if R > 0:
        arcs = []
        for idx, a in enumerate( pnts ):
            b = pnts[idx-1]
            vec = vec2.sub( b, a )
            length = vec2.length( vec )
            delta = vec2.scale( R / length, vec )
            na = vec2.add( a, delta )
            nb = vec2.sub( b, delta )
            ctr = vec2.add( nb, (delta[1], -delta[0]) )
            arcs.append( (ctr, na, nb) )
            add_line( na, nb, layer, width )
        for idx, (ctr, na, nb) in enumerate( arcs ):
            arc = add_arc2( ctr, nb, arcs[idx-1][1], -90, layer, width )
            # print( "na   ", pnt.mils2unit( vec2.round( na ) ) )
            # print( "start", arc.GetArcStart() )
            # print( "nb   ", pnt.mils2unit( vec2.round( nb ) ) )
            # print( "end  ", arc.GetArcEnd() )
    else:
        for idx, a in enumerate( pnts ):
            b = pnts[idx-1]
            add_line( a, b, layer, width )


# edge.cut drawing
def is_supported_round_angle( angle ):
    # integer?
    if angle - round( angle ) != 0:
        return False
    # multiple of 90?
    deg = int( angle )
    if (deg % 90) != 0:
        return False
    return True

def calc_bezier_corner_points( apos, avec, bpos, bvec, pitch = 1, ratio = 0.7 ):
    _, alen, blen = vec2.find_intersection( apos, avec, bpos, bvec )
    debug = False
    if alen <= 0:
        print( 'BezierCorner: alen = {} < 0, at {}'.format( alen, apos ) )
        debug = True
    if blen <= 0:
        print( 'BezierCorner: blen = {} < 0, at {}'.format( blen, bpos ) )
        debug = True
    # if debug:
    #     return []
    actrl = vec2.scale( alen * ratio, avec, apos )
    bctrl = vec2.scale( blen * ratio, bvec, bpos )
    ndivs = int( round( (alen + blen) / pitch ) )
    pnts = [apos, actrl, bctrl, bpos]
    curv = vec2.interpolate_points_by_bezier( pnts, ndivs, debug )
    return curv

def calc_bezier_round_points( apos, avec, bpos, bvec, radius ):
    _, alen, blen = vec2.find_intersection( apos, avec, bpos, bvec )
    debug = False
    if alen <= radius:
        print( 'BezierRound: alen < radius, {} < {}, at {}'.format( alen, radius, apos ) )
        debug = True
    if blen <= radius:
        print( 'BezierRound: blen < radius, {} < {}, at {}'.format( blen, radius, bpos ) )
        debug = True
    amid = vec2.scale( alen - radius, avec, apos )
    bmid = vec2.scale( blen - radius, bvec, bpos )
    #add_line( apos, amid, layer, width )
    #add_line( bpos, bmid, layer, width )
    angle = vec2.angle( avec, bvec )
    if angle < 0:
        #angle += 360
        angle *= -1
    ndivs = int( round( angle / 4.5 ) )
    #print( 'BezierRound: angle = {}, ndivs = {}'.format( angle, ndivs ) )
    coeff = (math.sqrt( 0.5 ) - 0.5) / 3 * 8
    #print( 'coeff = {}'.format( coeff ) )
    actrl = vec2.scale( alen + (coeff - 1) * radius, avec, apos )
    bctrl = vec2.scale( blen + (coeff - 1) * radius, bvec, bpos )
    pnts = [amid, actrl, bctrl, bmid]
    curv = [apos]
    for pos in vec2.interpolate_points_by_bezier( pnts, ndivs, debug ):
        curv.append( pos )
    curv.append( bpos )
    return curv

def draw_corner( cnr_type, a, cnr_data, b, layer, width, dump = False ):
    apos, aangle = a
    bpos, bangle = b
    avec = vec2.rotate( aangle )
    bvec = vec2.rotate( bangle + 180 )
    curv = None
    if cnr_type != Bezier and abs( vec2.dot( avec, bvec ) ) > 0.999:
        cnr_type = Line
        #print( avec, bvec )
    if cnr_type == Line:
        add_line( apos, bpos, layer, width )
    elif cnr_type == Linear:
        xpos, alen, blen = vec2.find_intersection( apos, avec, bpos, bvec )
        if cnr_data == None:
            add_line( apos, xpos, layer, width )
            add_line( bpos, xpos, layer, width )
        else:
            delta = cnr_data[0]
            #print( delta, alen, xpos )
            amid = vec2.scale( alen - delta, avec, apos )
            bmid = vec2.scale( blen - delta, bvec, bpos )
            add_line( apos, amid, layer, width )
            add_line( bpos, bmid, layer, width )
            add_line( amid, bmid, layer, width )
    elif cnr_type == Bezier:
        num_data = len( cnr_data )
        alen = cnr_data[0]
        blen = cnr_data[-2]
        ndivs = cnr_data[-1]
        apos2 = vec2.scale( alen, avec, apos )
        bpos2 = vec2.scale( blen, bvec, bpos )
        pnts = [apos, apos2]
        if num_data > 3:
            for pt in cnr_data[1:num_data-2]:
                pnts.append( pt )
        pnts.append( bpos2 )
        pnts.append( bpos )
        curv = vec2.interpolate_points_by_bezier( pnts, ndivs )
        add_lines( curv, layer, width )
    elif cnr_type == BezierRound:
        radius = cnr_data[0]
        curv = calc_bezier_round_points( apos, avec, bpos, bvec, radius )
        add_lines( curv, layer, width )
    elif cnr_type == Round:
        radius = cnr_data[0]
        # print( 'Round: radius = {}'.format( radius ) )
        # print( apos, avec, bpos, bvec )
        xpos, alen, blen = vec2.find_intersection( apos, avec, bpos, bvec )
        # print( xpos, alen, blen )
        debug = False
        if not is_supported_round_angle( aangle ):
            pass
            #print( 'Round: warning aangle = {}'.format( aangle ) )
            #debug = True
        if not is_supported_round_angle( bangle ):
            pass
            #print( 'Round: warning bangle = {}'.format( bangle ) )
            #debug = True
        if alen < radius:
            print( 'Round: alen < radius, {} < {}'.format( alen, radius ) )
            debug = True
        if blen < radius:
            print( 'Round: blen < radius, {} < {}'.format( blen, radius ) )
            debug = True
        if debug:
            add_arc( xpos, vec2.add( xpos, (10, 0) ), 360, layer, width )
            return b, curv
        angle = vec2.angle( avec, bvec )
        angle = math.ceil( angle * 10 ) / 10
        tangent = math.tan( abs( angle ) / 2 / 180 * math.pi )
        side_len = radius / tangent
        # print( 'angle = {}, radius = {}, side_len = {}, tangent = {}'.format( angle, radius, side_len, tangent ) )

        amid = vec2.scale( -side_len, avec, xpos )
        bmid = vec2.scale( -side_len, bvec, xpos )
        add_line( apos, amid, layer, width )
        add_line( bpos, bmid, layer, width )

        aperp = (-avec[1], avec[0])
        if angle >= 0:
            ctr = vec2.scale( -radius, aperp, amid )
            add_arc2( ctr, bmid, amid, 180 - angle, layer, width )
        else:
            ctr = vec2.scale( +radius, aperp, amid )
            add_arc2( ctr, amid, bmid, 180 + angle, layer, width )
    elif cnr_type == Spline:
        vec_scale = cnr_data[0]
        ndivs = int( round( vec2.distance( apos, bpos ) / 2.0 ) )
        auvec = vec2.rotate( aangle + 90 )
        buvec = vec2.rotate( bangle - 90 )
        curv = vec2.interpolate_points_by_hermit_spline( apos, auvec, bpos, buvec, ndivs, vec_scale )
        add_lines( curv, layer, width )
    return b, curv

def draw_closed_corners( corners, layer, width ):
    a = corners[-1][0]
    curvs = []
    for (b, cnr_type, cnr_data) in corners:
        a, curv = draw_corner( cnr_type, a, cnr_data, b, layer, width, True )
        curvs.append( curv )
        #break
    if False:
        with open( '/Users/akihiro/repos/mywork/hermit-edgecuts.scad', 'w' ) as fout:
            fout.write( 'edgecuts = [\n' )
            for curv in curvs:
                if curv == None:
                    continue
                for idx, pnt in enumerate( curv ):
                    if idx == 0:
                        continue
                    fout.write( '    [{}, {}],\n'.format( pnt[0], pnt[1] ) )
            fout.write( '];\n' )

# zones
def add_zone( rect, layer, idx = 0, net_name = 'GND' ):
    return None, None
    pnts = list( map( lambda pt: pnt.to_unit( vec2.round( pt, PointDigits ), UnitMM ), rect ) )
    net = pcb.FindNet( net_name ).GetNetCode()
    zone = pcb.AddArea( net, idx, layer, pnts[0][0], pnts[0][1], pcbnew.ZONE_CONTAINER.DIAGONAL_EDGE )
    poly = zone.Outline()
    for idx, pt in enumerate( pnts ):
        if idx == 0:
            continue
        poly.Append( pt[0], pt[1] )
    return zone, poly
