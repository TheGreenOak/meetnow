#include <iostream>
#include <opencv4/opencv2/opencv.hpp>

#include "codec.h"

#define HEIGHT 480
#define WIDTH 848
    
int test() {
    cv::Mat currFrame;
    cv::Mat prevMatFrame;
    cv::VideoCapture cap(0);
    unsigned char* prevFrame = 0;

    if (!cap.isOpened()) {
        std::cout << "Unable to open Webcam";
        return 1;
    }

    cap.set(cv::CAP_PROP_FRAME_HEIGHT, HEIGHT);

    cap >> prevMatFrame;
    prevFrame = prevMatFrame.data;
    cv::imshow("DECODED", prevMatFrame);

    while (true) {
        cap >> currFrame;

        auto encoded = encode(currFrame.data, prevMatFrame.data, HEIGHT, WIDTH, 6);
        prevFrame = decode(encoded, prevFrame, HEIGHT, WIDTH);

        cv::imshow("DECODED", cv::Mat(HEIGHT, WIDTH, CV_8UC3, prevFrame));
        cv::imshow("CURRENT FRAME", currFrame);

        std::memcpy(prevMatFrame.data, currFrame.data, HEIGHT * WIDTH * 3);
        cv::waitKey(30);

        free(encoded);
    }
}