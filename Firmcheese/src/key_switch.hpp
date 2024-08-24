#pragma once

#include <cstdint>

enum EKeySW {
       L71, L61, L51, L41, L31, L21,               R21, R31, R41, R51, R61, R71,
  L82, L72, L62, L52, L42, L32, L22,               R22, R32, R42, R52, R62, R72, R82,
  L83, L73, L63, L53, L43, L33, L23, L13,     R13, R23, R33, R43, R53, R63, R73, R83,
  L84,      L64, L54, L44, L34, L24, L14,     R14, R24, R34, R44, R54, R64,      R84,
            L65, LRB, LRA, L35, L25, L15,     R15, R25, R35, RRA, RRB, R65,
  NumSWs
};

constexpr uint8_t kNumSides = 2;
constexpr uint8_t kNumRows = 5;
constexpr uint8_t kNumCols = 8;
constexpr uint8_t kNumRots = 2;

#define ___ 255

constexpr uint8_t key_matrices[kNumSides][kNumRows][kNumCols] = {
  { // Left
    { ___, L21, L31, L41, L51, L61, L71, ___ },
    { ___, L22, L32, L42, L52, L62, L72, L82 },
    { L13, L23, L33, L43, L53, L63, L73, L83 },
    { L14, L24, L34, L44, L54, L64, ___, L84 },
    { L15, L25, L35, ___, ___, L65, ___, ___ },
  },
  { // Right
    { ___, R21, R31, R41, R51, R61, R71, ___ },
    { ___, R22, R32, R42, R52, R62, R72, R82 },
    { R13, R23, R33, R43, R53, R63, R73, R83 },
    { R14, R24, R34, R44, R54, R64, ___, R84 },
    { R15, R25, R35, ___, ___, R65, ___, ___ },
  },
};

#undef ___
