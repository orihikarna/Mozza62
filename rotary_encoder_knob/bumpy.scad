knob_height = 12;
knob_top_r = 16;
knob_btm_r = 20;
axis_top_r = 3.2;
axis_btm_r = 3.3;
wall_thick = 1.6;
delta = 0.1;

// h_top, h_btm
module axis( h_top, h_btm ) {
  h_axis = h_top + h_btm;
  $fn = 30;
  difference() {
    union() {
      // axis outer
      cylinder( h_axis + 0.6 * axis_btm_r, r = axis_btm_r + wall_thick );
      // axis supporr walls
      intersection() {
        cylinder( knob_height - delta, knob_btm_r - 1, knob_top_r - 1 );
        union() {
          for (i = [0:4]) {
            rotate( [0, 0, 72 * i] )
              translate( [knob_btm_r/2, 0, knob_height/2] )
                cube( [knob_btm_r, wall_thick, knob_height], true );
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
            cylinder( h_top + delta, axis_top_r, axis_top_r );
            // top hat
            translate( [0, 0, h_top] ) {
              cylinder( axis_top_r * 0.7, axis_top_r, 0 );
            }
          }
          translate( [axis_top_r/2, -(h_top * 2 + 2 * delta) / 2, 0] )
            cube( h_top * 2 + 2 * delta );
        }
      // bottom hat
      translate( [0, 0, h_btm + 1 * delta] ) {
        cylinder( axis_btm_r, axis_btm_r, 0 );
      }
      // bottom part
      cylinder( h_btm + 2 * delta, axis_btm_r, axis_btm_r );
    }
  }
}

sph_h   = knob_height - 1.0;
sph_btm = knob_btm_r - 1.6;

difference() {
  union() {
    axis( 7.2, 2.2 );
    difference() {
      import( "knob_surface.stl", 10 );
      scale( [sph_btm, sph_btm, sph_h] ) sphere( 1, $fn = 64 );
    }
  }
  // remove elephant foot
  translate( [0, 0, -delta] )
    cylinder( 0.6, axis_btm_r + 0.6, axis_btm_r, $fn = 64 );

  if (false)
    translate( [0, 50, 0] )
      cube( 100, center = true );
}
