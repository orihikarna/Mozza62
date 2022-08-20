import numpy
import numpy as np
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot

bump_r_mm = 0.6 # bump hight on surface
bump_h_mm = 4.0 # bump cycle along the z-axis
bump_th_deg = 30 # bump cycle along the circle

# number of divisions
z_num = 80
t_num = 20
dth_deg = 1

# knob hight
knob_h_mm = 12
# knob radius
knob_r_top_mm = 16
knob_r_btm_mm = 20

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

top_anchors = np.array( [
    [1, 0],
    [0.9, 1],
    [0.8, 2.0],
    [0.7, 2.0],
    [0.6, 2.0],
    [0.5, 2.0],
    [0.4, 2.0],
    [0.3, 1.0],
    [0.2, 0.5],
    [0.1, 0],
    [0.0, 0],
] )

top_points = [calc_bezier_point( top_anchors, t ) for t in np.linspace( 0, 1, t_num )]

def get_bump_pos( zt_idx, th_deg ):
    if zt_idx < -1:
        return None
    if zt_idx == -1:
        return [0, 0, 0]
    if zt_idx == z_num + t_num:
        return [0, 0, knob_h_mm]
    if zt_idx > z_num + t_num:
        return None

    if zt_idx < z_num:# side bumps
        rz = zt_idx / z_num
        z_mm = knob_h_mm * rz
        r_mm = knob_r_top_mm + (knob_r_btm_mm - knob_r_top_mm) * (1 - rz**5)
        bump_h  = np.sin( (2 * np.pi) * (z_mm / bump_h_mm) )
        bump_th = np.cos( (2 * np.pi) * (th_deg / bump_th_deg) )
        bump = bump_th * bump_h * bump_r_mm
        r_mm += bump
    else:# top
        t_idx = zt_idx - z_num
        u = t_idx / t_num
        # pt = calc_bezier_point( top_anchors, u )
        pt = top_points[t_idx]
        r_mm = knob_r_top_mm * pt[0]
        z_mm = knob_h_mm + pt[1] * 0.8
    th_rad = np.deg2rad( th_deg )
    x_mm = r_mm * np.cos( th_rad )
    y_mm = r_mm * np.sin( th_rad )
    return [x_mm, y_mm, z_mm]
    
vertices = []

for zt_idx in range( z_num + t_num ):
    dth_curr = 0 if (zt_idx % 2) == 0 else (dth_deg / 2)
    dth_neib = 0 if (zt_idx % 2) != 0 else (dth_deg / 2)
    for th_deg in np.arange( 0, 360, dth_deg ):
        p_fore = get_bump_pos( zt_idx, th_deg + dth_curr + dth_deg / 2 )
        p_back = get_bump_pos( zt_idx, th_deg + dth_curr - dth_deg / 2 )
        p_btm = get_bump_pos( zt_idx-1, th_deg + dth_curr )
        p_top = get_bump_pos( zt_idx+1, th_deg + dth_curr )
        if p_btm:
            vertices.append( np.array( [p_fore, p_back, p_btm] ) )
        if p_top:
            vertices.append( np.array( [p_fore, p_top, p_back] ) )

vertices = np.array( vertices )
# print( vertices )
print( vertices.shape )

mesh = mesh.Mesh( np.zeros( vertices.shape[0], dtype=mesh.Mesh.dtype ) )
mesh.vectors = vertices
mesh.remove_duplicate_polygons=True
mesh.save( 'knob_surface.stl' )


# figure = pyplot.figure()
# axes = mplot3d.Axes3D(figure)
# axes.add_collection3d(mplot3d.art3d.Poly3DCollection(mesh.vectors))

# scale = mesh.points.flatten()
# print(scale)
# axes.auto_scale_xyz(scale, scale, scale)

# pyplot.show()
