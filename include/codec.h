#pragma once

#define DEFAULT_THRESHOLD 20

extern "C" {
	unsigned char* encode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width, unsigned char threshold = DEFAULT_THRESHOLD);
	unsigned char* decode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width);
}
