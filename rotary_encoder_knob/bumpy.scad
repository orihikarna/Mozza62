height = 12;
top_radius = 16;
btm_radius = 20;
w_thick = 2.4;

module donut() {
}

// h_top, h_btm
module axis( h_top, h_btm ) {
  h_axis = h_top + h_btm;
  delta = 0.1;
  r = 3.2;
  $fn = 30;
  difference() {
    union() {
      // axis outer
      cylinder( h_axis + r + delta, r + w_thick, r + w_thick );
      // axis supporr walls
      intersection() {
        cylinder( height - 3, btm_radius - 3, top_radius - 3 );
        union() {
          for (i = [0:3]) {
            rotate( [0, 0, 120 * i] )
              translate( [btm_radius/2, 0, height/2] )
                cube( [btm_radius, w_thick, height], true );
          }
        }
      }
    }
    // axis hole
    translate( [0, 0, -delta] ) {
      // top part
      translate( [0, 0, h_btm - delta] )
        difference() {
          union() {
            // top cylinder
            cylinder( h_top + delta, r, r );
            // top hat
            translate( [0, 0, h_top + 0 * delta] ) {
              cylinder( r * 0.8, r, 0 );
            }
          }
          translate( [r/2, -(h_top * 2 + 2 * delta) / 2, 0] )
            cube( h_top * 2 + 2 * delta );
        }
      // bottom hat
      translate( [0, 0, h_btm + 1 * delta] ) {
        cylinder( r * 0.8, r, 0 );
      }
      // bottom part
      cylinder( h_btm + 2 * delta, r, r );
    }
  }
}

sph_h = height - 2.5;
sph_btm = btm_radius - 3;

difference() {
  union() {
    axis( 6, 1.5 );
    difference() {
      import( "knob_surface.stl", 10 );
      scale( [sph_btm, sph_btm, sph_h] ) sphere( 1, $fn = 64 );
    }
  }
  if (false)
  translate( [0, 50, 0] )
    cube( 100, center = true );
}
