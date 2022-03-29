#pragma once

#define DEFAULT_THRESHOLD 20

extern "C" {
	unsigned int encode(unsigned char* buffer, unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width, unsigned char threshold = DEFAULT_THRESHOLD);
	unsigned int decode(unsigned char* buffer, unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width);
}
