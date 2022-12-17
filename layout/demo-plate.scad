$fn = 24;

include <kbd-layout.scad>
//include <hermit-edgecuts.scad>

key_hole = 14.1;
center_key = 8;

module round_square( xsize, ysize, radius ) {
  if (radius == 0) {
    square( [xsize , ysize], true );
  } else {
    minkowski() {
      square( [xsize - 2 * radius, ysize - 2 * radius], true );
      circle( radius );
    }
  }
}

module key_rect( prm, size_delta = 0 ) {
  x = prm[0] - key_pos_angles[center_key][0];
  y = prm[1] - key_pos_angles[center_key][1];
  r = prm[2];
  translate( [x, y, 0] )
    rotate( [0, 0, r] )
      square( [prm[3] + size_delta, prm[4] + size_delta], center = true );
}

module key_square( prm, size, radius ) {
  x = prm[0] - key_pos_angles[center_key][0];
  y = prm[1] - key_pos_angles[center_key][1];
  r = prm[2];
  translate( [x, y, 0] )
    rotate( [0, 0, r] )
      round_square( size, size, radius );
}

module plate_inflate() {
  close = 12;
  offset( -close ) offset( +close ) {
    for (prm = key_pos_angles) {
      if (prm[5] == 31) {
        key_rect( prm, 2.4 );
      } else {
        key_rect( prm );
      }
    }
    Alt = 26;
    for (idxs = [[Alt, 0], [Alt, 4], [Alt, 8], [Alt, 12], [Alt, 16]]) {
      hull() {
        for (idx = idxs) {
          prm = key_pos_angles[idx];
          key_rect( prm, -10 );
        }
      }
    }
  }
}

module plate_edgecuts() {
    echo( len( edgecuts ) );
    pnts = [ for (i = [0 : len( edgecuts ) - 1])
        [edgecuts[i][0] - key_pos_angles[center_key][0],
        -edgecuts[i][1] - key_pos_angles[center_key][1]]
    ];
    echo( len( pnts ) );
    polygon( pnts );
}

thick = 1.5;
wall = 0.6;

mirror( [1, 0, 0] )
difference() {
  // the outer box
  intersection() {
    translate( [0, 0, -50 + 6.4] )
      cube( [300, 300, 100], center = true );
    linear_extrude( 20, scale = 1.01 ) {
      offset( wall + 0.1 )
        //plate_inflate();
        plate_edgecuts();
    }
  }
  // key holes (top)
  translate( [0, 0, -1] ) {
    linear_extrude( 10 ) {
      for (prm = key_pos_angles) {
        if (prm[5] >= 31) {
          key_rect( prm, 0 );
        } else {
          key_square( prm, key_hole, 0.6 );
        }
      }
    }
  }
  // key holes (bottom)
  translate( [0, 0, thick] ) {
    linear_extrude( 10 ) {
      for (prm = key_pos_angles) {
        if (prm[5] == 31) {
          key_rect( prm, 1 );
        } else {
          key_square( prm, 15.6, 0.6 );
        }
      }
    }
  }
  // small ditches
  if (false) {
    for (idxs = [[0, 2], [3, 6], [7, 10], [11, 14], [15, 18], [19, 21], [22, 24], [25, 26], [29, 30], [2,31]]) {
      hull() {
        for (idx = idxs) {
          prm = key_pos_angles[idx];
          x = prm[0] - key_pos_angles[center_key][0];
          y = prm[1] - key_pos_angles[center_key][1];
          translate( [x, y, 0] )
            cube( [0.4, 0.4, 0.4], true );
        }
      }
    }
  }

}
