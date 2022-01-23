#pragma once

unsigned char* encode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width);
unsigned char* decode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width);