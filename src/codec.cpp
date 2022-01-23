#include "codec.h"
#include <iostream>

#define CHANNELS          3
#define THRESHOLD         15
#define MAX_SAVED         0x1FFFFFF
#define TURN_ON_SAVE_BIT  0x1000000 // (1 << 23)

/*
 * Codec Format 
 * 4 bytes. One is the identifier byte, the other 3 are RGB values.
 * 
 * Identifier Byte can be:
 * 0: New information
 * 1: Existing information - the 3 other bytes serve as length
 * 
 */

unsigned char* encode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width) {
    unsigned char pixel[CHANNELS] = { 0 };
    unsigned char previousPixel[CHANNELS] = { 0 };
    unsigned char* encoded = ((unsigned char*)new unsigned int[height * width]);

    int counter = 0;
    bool previouslySaved = false;

    if (previousFrame == nullptr) {
        for (int row = 0; row < height; row++) {
            for (int col = 0; col < width; col++) {
                encoded[row * height + col + 0] = 0;
                encoded[row * height + col + 1] = pixels[row * height + col + 0];
                encoded[row * height + col + 2] = pixels[row * height + col + 1];
                encoded[row * height + col + 3] = pixels[row * height + col + 2];
            }
        }

        return encoded;
    }

    for (int row = 0; row < height; row++) {
        for (int col = 0; col < width; col++) {

            // Setup the fist pixel
            pixel[0] = pixels[row * height + col + 0];
            pixel[1] = pixels[row * height + col + 1];
            pixel[2] = pixels[row * height + col + 2];

            // Setup the second pixel
            previousPixel[0] = previousFrame[row * height + col + 0];
            previousPixel[1] = previousFrame[row * height + col + 1];
            previousPixel[2] = previousFrame[row * height + col + 2];

            // Check if the pixels are similar
            if ((pixel[0] - previousPixel[0] <= THRESHOLD || pixel[0] - previousPixel[0] >= ((unsigned char)-THRESHOLD))
            &&  (pixel[1] - previousPixel[1] <= THRESHOLD || pixel[1] - previousPixel[1] >= ((unsigned char)-THRESHOLD))
            &&  (pixel[2] - previousPixel[2] <= THRESHOLD || pixel[2] - previousPixel[2] >= ((unsigned char)-THRESHOLD))) {

                // Check if we reached the max save value
                if (((int*)encoded)[counter] == MAX_SAVED) {
                    counter += sizeof(int);
                }

                // Keep old pixel
                ((int*)encoded)[counter] = ((int*)encoded)[counter] | TURN_ON_SAVE_BIT; // Indiciate existing information
                ((int*)encoded)[counter]++;
                previouslySaved = true;

            } else {

                // We don't want to override the saved pixels
                if (previouslySaved) {
                    counter += sizeof(int);
                    previouslySaved = false;
                }

                encoded[counter] = 0;
                encoded[counter + 1] = pixel[0];
                encoded[counter + 2] = pixel[1];
                encoded[counter + 3] = pixel[2];
                counter += sizeof(int);
            }
        }
    }

    std::cout << "Number of ints stored: " << counter;
    return encoded;
}

unsigned char* decode(unsigned char* pixels, unsigned char* previousFrame, unsigned short height, unsigned short width) {
    
}