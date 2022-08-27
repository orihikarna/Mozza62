set grid
set nosurface
set contour
set size 0.66, 1
set view 0, 0, 1, 1
set isosamples 100, 100
set nokey
a=1
b=1
set cntrparam levels incremental 0, -0.1, -1
splot[0:1.6][-0.8:0.8] (x**2+y**2)**2 - 2*a**2*(x**2-y**2)+a**4-b**4
