#include <iostream>
#include <opencv4/opencv2/opencv.hpp>

#include "codec.h"

#define HEIGHT 480
#define WIDTH 848
    
int test() {
    cv::Mat currFrame;
    cv::Mat temp;
    cv::VideoCapture cap(0);
    unsigned char* prevFrame = 0;

    if (!cap.isOpened()) {
        std::cout << "Unable to open Webcam";
        return 1;
    }

    cap.set(cv::CAP_PROP_FRAME_HEIGHT, HEIGHT);

    cap >> temp;
    prevFrame = temp.data;
    cv::imshow("TEST", temp);

    while (true) {
        cap >> currFrame;

        auto encoded = encode(currFrame.data, prevFrame, HEIGHT, WIDTH, 1);
        prevFrame = decode(encoded, prevFrame, HEIGHT, WIDTH);
        cv::imshow("TEST", cv::Mat(HEIGHT, WIDTH, CV_8UC3, prevFrame));
        cv::waitKey(30);
    }
}