#!/usr/bin/env python3
#
# Note -- this code is tweaked from the original at:
#           https://github.com/dusty-nv/jetson-inference/blob/master/python/www/html/stream.py
#
# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the 'Software'),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
import sys
import threading
import traceback

from jetson_inference import imageNet, detectNet, segNet, actionNet, poseNet, backgroundNet
from jetson_utils import videoSource, videoOutput, cudaFont, cudaAllocMapped
from util import logHandler


class Stream(threading.Thread):
    """
    Thread for streaming video and applying DNN inference
    """

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.input = videoSource(args.input, argv=sys.argv)
        self.output = videoOutput(args.output, argv=sys.argv)
        self.frames = 0
        self.status = ""
        self.guess = {}

        self.net = imageNet(model="./models/target.onnx", labels="./models/labels.txt", input_blob="input_0",
                            output_blob="output_0")
        self.font = cudaFont()
        self.fontSize = self.font.GetSize() / 2
        self.lastObj = ""
        self.logHandler = logHandler()

    def process(self):
        """
        Capture one image from the stream, process it, and output it.
        """
        img = self.input.Capture()

        if img is None:  # timeout
            return

        classID, confidence = self.net.Classify(img)
        classLabel = self.net.GetClassLabel(classID)
        confidence *= 100.0

        self.font.OverlayText(img, text=f"{confidence:05.2f}% {classLabel}", x=5, y=5,
                              color=self.font.White, background=self.font.Gray40)

        # Judge every n frames
        if self.frames == 20:
            guesses = list(self.guess.keys())
            possibilities = []
            # Find the one that model guess the most and record how many times it appear
            maxnum = max([len(i) for i in self.guess.values()])
            for person in guesses:
                sum = 0
                for confidency in self.guess[person]:
                    sum += confidency
                possibilities.append(sum / maxnum)

            theOne = guesses[possibilities.index(max(possibilities))]
            
            # If the confidence is above 80
            if max(possibilities) > 80:
                if theOne == "Nothing":
                    self.lastObj = "Nothing"
                    self.status = "DENY"
                elif theOne != self.lastObj:
                    # Log it
                    self.logHandler.addRec(classLabel)
                    # print(classLabel)
                    self.status = "PASS"
                    self.lastObj = theOne
            else:
                self.lastObj = "Nothing"
                self.status = "ALARM"

            self.frames = 0
            self.guess = {}
        else:
            if classLabel not in self.guess.keys():
                self.guess[classLabel] = [confidence]
            else:
                self.guess[classLabel].append(confidence)
            self.frames += 1

        # Overlay PASS and DENY
        (lambda: self.font.OverlayText(img, text="PASS", x=int(img.width / 2 - self.fontSize),
                                       y=int(img.height / 2 - self.fontSize + 5), color=self.font.Green,
                                       background=self.font.Gray40) if self.status == "PASS" else self.font.OverlayText(
            img, text="DENY", x=int(img.width / 2 - self.fontSize),
            y=int(img.height / 2 - self.fontSize + 5), color=self.font.Red,
            background=self.font.Gray40))()

        self.font.OverlayText(img, text=f"LastObj: {self.lastObj}", x=5, y=40,
                              color=self.font.White, background=self.font.Gray40)
        self.output.Render(img)

    def run(self):
        """
        Run the stream processing thread's main loop.
        """
        while True:
            try:
                self.process()
            except:
                traceback.print_exc()

    @staticmethod
    def usage():
        """
        Return help text for when the app is started with -h or --help
        """
        return videoSource.Usage() + videoOutput.Usage() + imageNet.Usage() + detectNet.Usage() + segNet.Usage() + actionNet.Usage() + poseNet.Usage() + backgroundNet.Usage()
