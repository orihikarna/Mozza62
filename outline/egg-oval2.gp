reset
set grid
set parametric
a = 1
b = 0.98

plot [-pi:+pi][-1:1][-1:1] a * cos( t ), b * cos( t / 4 ) * sin( t )
