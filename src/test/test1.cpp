#include <iostream>
#include <opencv4/opencv2/opencv.hpp>

#include "codec.h"

#define HEIGHT 480
#define WIDTH 848
    
int test() {
    cv::Mat image;
    cv::Mat oldImage;
    cv::VideoCapture cap(0);

    if (!cap.isOpened()) {
        std::cout << "Unable to open Webcam";
        return 1;
    }

    cap.set(cv::CAP_PROP_FRAME_HEIGHT, HEIGHT);
    cap >> oldImage;
    cv::imshow("TEST", oldImage);
    cv::waitKey(1500);

    cap >> oldImage;

    unsigned char* encoded1 = encode(oldImage.data, nullptr, HEIGHT, WIDTH);

    cv::imshow("TEST", oldImage);
    cv::waitKey(1500);
    cap >> image;

    unsigned char* encoded2 = encode(image.data, oldImage.data, HEIGHT, WIDTH, 1);

    cv::imshow("TEST", image);
    cv::waitKey(1500);

    std::cout << "Now decoding!" << std::endl;
    cv::waitKey(1500);

    unsigned char* decoded1 = decode(encoded1, nullptr, HEIGHT, WIDTH);
    cv::imshow("TEST", cv::Mat(HEIGHT, WIDTH, CV_8UC3, decoded1));

    for (int i = 0; i < HEIGHT * WIDTH * 3; i++) {
        if (oldImage.data[i] != decoded1[i]) {
            std::cout << "Something went wrong...";
            return 1;
        }
    }

    std::cout << "Decoded 1." << std::endl;
    cv::waitKey(1500);

    unsigned char* decoded2 = decode(encoded2, decoded1, HEIGHT, WIDTH);

    cv::imshow("TEST", cv::Mat(HEIGHT, WIDTH, CV_8UC3, decoded2));
    std::cout << "Decoded 2." << std::endl;
    cv::waitKey(1500);
}