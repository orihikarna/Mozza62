height = 12;
top_radius = 15;
btm_radius = 18;
axis_r = 3.2;
w_thick = 2.0;
delta = 0.1;

// h_top, h_btm
module axis( h_top, h_btm ) {
  h_axis = h_top + h_btm;
  $fn = 30;
  difference() {
    union() {
      // axis outer
      cylinder( h_axis + 0.6 * axis_r, axis_r + w_thick, axis_r + w_thick );
      // axis supporr walls
      intersection() {
        cylinder( height - delta, btm_radius - 1, top_radius - 1 );
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
            cylinder( h_top + delta, axis_r, axis_r );
            // top hat
            translate( [0, 0, h_top + 0 * delta] ) {
              cylinder( axis_r * 0.8, axis_r, 0 );
            }
          }
          translate( [axis_r/2, -(h_top * 2 + 2 * delta) / 2, 0] )
            cube( h_top * 2 + 2 * delta );
        }
      // bottom hat
      translate( [0, 0, h_btm + 1 * delta] ) {
        cylinder( axis_r * 0.8, axis_r, 0 );
      }
      // bottom part
      cylinder( h_btm + 2 * delta, axis_r, axis_r );
    }
  }
}

sph_h = height - 1.6;
sph_btm = btm_radius - 2.4;

difference() {
  union() {
    axis( 7.4, 2.0 );
    difference() {
      import( "knob_surface.stl", 10 );
      scale( [sph_btm, sph_btm, sph_h] ) sphere( 1, $fn = 64 );
    }
  }
  // remove elephant foot
  translate( [0, 0, -delta] )
    cylinder( 0.6, axis_r + 0.6, axis_r, $fn = 64 );

  if (false)
    translate( [0, 50, 0] )
      cube( 100, center = true );
}
