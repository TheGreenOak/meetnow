#include <iostream>
#include <opencv4/opencv2/opencv.hpp>

#include "codec.h"

int main() {
    cv::Mat image;
    cv::Mat oldImage;
    cv::VideoCapture cap(0);

    if (!cap.isOpened()) {
        std::cout << "Unable to open Webcam";
        return 1;
    }

    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    cap >> oldImage;
    cv::waitKey(500);
    cap >> oldImage;
    
    std::cout << "WIDTH: " << oldImage.cols << std::endl;
    std::cout << "HEIGHT: " << oldImage.rows << std::endl;

    unsigned char* encoded1 = encode(oldImage.data, nullptr, oldImage.cols, oldImage.rows);

    cv::imshow("TEST", oldImage);
    cv::waitKey(1500);
    cap >> image;

    unsigned char* encoded2 = encode(image.data, oldImage.data, image.cols, image.rows, (unsigned char)80);

    cv::imshow("TEST", image);
    cv::waitKey(1500);

    std::cout << "Now decoding!" << std::endl;
    cv::waitKey(1500);

    oldImage.data = decode(encoded1, nullptr, oldImage.cols, oldImage.rows);
    oldImage.datastart = oldImage.data;
    oldImage.dataend = oldImage.data + (oldImage.cols * oldImage.rows * 3);
    oldImage.datalimit = oldImage.dataend;

    cv::imshow("TEST", oldImage);
    std::cout << "Decoded 1." << std::endl;
    cv::waitKey(1500);

    image.data = decode(encoded2, oldImage.data, image.cols, image.rows);

    cv::imshow("TEST", image);
    std::cout << "Decoded 2." << std::endl;
    cv::waitKey(1500);

    return 0;
}
