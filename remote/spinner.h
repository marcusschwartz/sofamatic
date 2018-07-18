char *spinner[] = {
    "o                 ",
    " o                ",
    "  o               ",
    "   o              ",
    "    o             ",
    "     o            ",
    "      o           ",
    "       o          ",
    "        o         ",
    "         o        ",
    "          o       ",
    "           o      ",
    "            o     ",
    "             o    ",
    "              o   ",
    "               o  ",
    "                o ",
    "                 o",
    "                o ",
    "               o  ",
    "              o   ",
    "             o    ",
    "            o     ",
    "           o      ",
    "          o       ",
    "         o        ",
    "        o         ",
    "       o          ",
    "      o           ",
    "     o            ",
    "    o             ",
    "   o              ",
    "  o               ",
    " o                "
};

int spinner_len = 33;
int spinner_seq = 0;

static const unsigned char spinner_logo_left[] = {
  0x00,0x00
 ,0x00,0x0e
 ,0x00,0x1e
 ,0x00,0x1e
 ,0x00,0x1e
 ,0x00,0x3c
 ,0x00,0x3c
 ,0x7f,0xfc
 ,0x7f,0xf8
 ,0x7f,0xf8
 ,0x1f,0xf8
 ,0x1f,0xf8
 ,0x1f,0xf8
 ,0x1f,0xf8
 ,0x1f,0xf8
 ,0x0c,0x30
};

static const unsigned char spinner_logo_right[] = {
0x00,0x00
,0x70,0x00
,0x78,0x00
,0x78,0x00
,0x78,0x00
,0x3c,0x00
,0x3c,0x00
,0x3f,0xfe
,0x1f,0xfe
,0x1f,0xfe
,0x1f,0xf8
,0x1f,0xf8
,0x1f,0xf8
,0x1f,0xf8
,0x1f,0xf8
,0x0c,0x30

};

byte spinner_logo_width = 16;
byte spinner_logo_height = 16;

