#include "codec.h"
#include <iostream>

#define CHANNELS   3
#define BYTE       0xFF
#define BYTE_SIZE  8
#define MAX_SAVED  0xFFFFFF
#define SAVE_BIT   0x1000000 // (1 << 24)

/*
 * Codec Format 
 * 4 bytes. One is the identifier byte, the other 3 are RGB values.
 * 
 * Identifier Byte can be:
 * 0: New information
 * 1: Existing information - the 3 other bytes serve as length
 * 
 * This codec is stored (for now) in Little Endian format.
 */

unsigned char* encode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width, unsigned char threshold) {
    unsigned char pixel[CHANNELS] = { 0 };
    unsigned char previousPixel[CHANNELS] = { 0 };
    unsigned char* encoded = ((unsigned char*)new unsigned int[height * width]);

    unsigned int counter = 0, currPixel = 0;
    bool previouslySaved = false;

    if (previousFrame == nullptr) { // If there's no previous frame, don't process.
        for (int i = 0; currPixel < height * width * CHANNELS; i += sizeof(int)) {
            encoded[i + CHANNELS] = 0;
            
            for (int j = 0; j < CHANNELS; j++) {
                encoded[i + CHANNELS - j - 1] = pixels[currPixel++];
            }
        }

        return encoded;
    }

    for (currPixel = 0; currPixel < height * width; currPixel += CHANNELS) {
        
        // Setup the pixels
        for (int i = 0; i < CHANNELS; i++) {
            pixel[i] = pixels[currPixel + i];
            previousPixel[i] = previousFrame[currPixel + i];
        }

        // Check if the pixels are similar
        if ((pixel[0] - previousPixel[0] <= threshold || pixel[0] - previousPixel[0] >= ((unsigned char)-threshold))
        &&  (pixel[1] - previousPixel[1] <= threshold || pixel[1] - previousPixel[1] >= ((unsigned char)-threshold))
        &&  (pixel[2] - previousPixel[2] <= threshold || pixel[2] - previousPixel[2] >= ((unsigned char)-threshold))) {

            // Check if we reached the max save value
            if (((int*)encoded)[counter] == MAX_SAVED) {
                counter += sizeof(int);
            }

            // Keep old pixel
            ((int*)encoded)[counter] = (((int*)encoded)[counter] | SAVE_BIT); // Indiciate existing information
            ((int*)encoded)[counter]++;
            previouslySaved = true;

        } else {

            // We don't want to override the saved pixels
            if (previouslySaved) {
                counter += sizeof(int);
                previouslySaved = false;
            }

            encoded[counter + CHANNELS] = 0;
            for (int i = 0; i < CHANNELS; i++) {
                encoded[counter + CHANNELS - i - 1] = pixel[i];
            }

            counter += sizeof(int);
        }
    }

    std::cout << "Number of ints stored: " << counter;
    return encoded;
}

unsigned char* decode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width) {
    unsigned char* decoded = new unsigned char[height * width * CHANNELS];
    unsigned int i = 0, currPixel = 0, currBlock = 0;
    unsigned int amountOfPixels = height * width;

    while (currPixel < amountOfPixels) {
        currBlock = ((unsigned int*)pixels)[i];
        
        // The following bits have been saved from the previous frame.
        if ((currBlock & SAVE_BIT) != 0) {
            currBlock = (currBlock & MAX_SAVED);

            for (int j = 0; j < currBlock * CHANNELS; j++) {
                decoded[currPixel] = previousFrame[currPixel++];
            }
        } else {
            for (int bit = 0; bit < CHANNELS; bit++) {
                decoded[currPixel++] = (unsigned char) ((currBlock >> (BYTE_SIZE * bit + BYTE_SIZE)) & BYTE);
            }
        }

        i++;
    }

    return decoded;
}