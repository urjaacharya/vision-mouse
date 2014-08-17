import cv2
# import sys
# import os
import numpy as np


#coordinates of the number of intersections obtained
class Coordinates(object):
    coord = []
    size = -1

    def __init__(self):
        Coordinates.size += 1
        Coordinates.centroidx = 0
        Coordinates.centroidy = 0
        Coordinates.corners = []

    def getlist(self):
        return Coordinates.coord

    #append the coordinates of intersections
    def append(self, x, y):
        Coordinates.coord.append([x, y])
        Coordinates.size += 1

    #check if the points make up a quadrilateral
    def quadcheck(self):
        Coordinates.coord = np.reshape(Coordinates.coord, (Coordinates.size, 1, 2))
        # print Coordinates.coord, "size", Coordinates.size
        peri = cv2.arcLength(Coordinates.coord, True)
        # print "peri", peri*0.02
        approx = cv2.approxPolyDP(Coordinates.coord, 0.02*peri, True)
        # print approx
        # if len(approx) % 4 == 0:
        if approx.size == 8:
            Coordinates.coord = approx.tolist()
            Coordinates.size = 4
            return True
        else:
            Coordinates.coord = approx.tolist()
            Coordinates.size = 4
            return False

    #find the centroid of the points of intersections found
    def calculateCentroid(self):
        sumx = 0
        sumy = 0
        for i in xrange(0, Coordinates.size):
            sumx += Coordinates.coord[i][0][0]
            sumy += Coordinates.coord[i][0][1]
        Coordinates.centroidx = sumx/Coordinates.size
        Coordinates.centroidy = sumy/Coordinates.size

    #find the intersection points of all the hull structures found
    def intersection(self, p1, p2, p3, p4):
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        x3 = p3[0]
        y3 = p3[1]
        x4 = p4[0]
        y4 = p4[1]
        d = (((x1 - x2) * (y3 - y4)) - ((y1 - y2) * (x3 - x4)))
        if d:
            interx = ((x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2) * (x3*y4 - y3*x4)) / d
            intery = ((x1*y2 - y1*x2) * (y3 - y4) - (y1 - y2) * (x3*y4 - y3*x4)) / d
        return [interx, intery]

    #find the Top right, Top left, Bottom right and Bottom left points
    def calculatetrtlbrbl(self):
        topoints = []
        bottompoints = []
        for i in xrange(0, Coordinates.size):
            if Coordinates.coord[i][0][1] < Coordinates.centroidy:
                topoints.append(Coordinates.coord[i])
            else:
                bottompoints.append(Coordinates.coord[i])

        top_left = min(topoints)
        top_right = max(topoints)
        bottom_right = max(bottompoints)
        bottom_left = min(bottompoints)

        Coordinates.corners.append(top_left)
        Coordinates.corners.append(top_right)
        Coordinates.corners.append(bottom_right)
        Coordinates.corners.append(bottom_left)
        return Coordinates.corners


#     change the perspective look of an image
class Perspective(object):

    def __init__(self, source):
        self.source = source

    #     get the destinations and edges and find the hull/ contour and the intersection points
    def handle(self):
        img = self.source
        self.shape = img.shape
        width = self.shape[1]
        height = self.shape[0]
        self.destination = np.float32([[0, 0], [width, 0],  [width, height], [0, height]])
        gray = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
        edges = cv2.Canny(gray, 150, 255)

        hull = None
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for i, cnt in enumerate(contours):
            if hierarchy[0, i, 3] == -1 and cv2.contourArea(cnt) > 5000:
                hull = cv2.convexHull(cnt, returnPoints=True)
                break

        coord = Coordinates()
        ###new way to find intersection
        count = 0
        temp = []
        for tier1 in hull:
            for tier2 in tier1:
                # print "tier2", tier2
                count += 1
                temp.append(tier2)
                if count == 4:
                    count -= 1
                    # print "temp0", temp[0]
                    [x, y] = coord.intersection(temp[0], temp[1], temp[2], temp[3])
                    # print temp[0], temp[1], temp[2], temp[3]
                    coord.append(x, y)
                    temp.pop(0)
        return coord

#     transform the points to the destination and return warped image and transformationMatrix
    def transform(self, corners):
        corners = np.float32((corners[0][0], corners[1][0], corners[2][0], corners[3][0]))
        transformationMatrix = cv2.getPerspectiveTransform(corners, self.destination)
        minVal = np.min(self.destination[np.nonzero(self.destination)])
        maxVal = np.max(self.destination[np.nonzero(self.destination)])
        warpedImage = cv2.warpPerspective(self.source, transformationMatrix, (self.shape[1], self.shape[0]))
        return warpedImage, transformationMatrix

#         improve the image by sharpening it
    def showsharpen(self, warpedImage):
        gray = cv2.cvtColor(warpedImage, cv2.cv.CV_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 2)
        alpha = 1.5
        beta = 1 - alpha
        gamma = 0
        sharpened = cv2.addWeighted(gray, alpha, blur, beta, gamma)

if __name__ == "__main__":
    source = cv2.imread("bgr.jpg")

    #this needs to be dynamic
    shape = source.shape
    if shape[0] < 320 or shape[1] < 480:
        source = cv2.pyrUp(source)
    else:
        source = cv2.pyrDown(source)

    # source = cv2.pyrDown(source)
    persp = Perspective(source)
    # edges = persp.handle()
    contourcoord = persp.handle()
    for corner in contourcoord.getlist():
        print corner
        cv2.circle(source, (corner[0], corner[1]), 10, (0, 0, 255))
        cv2.imshow("circles", source)
        cv2.waitKey(0)
    if contourcoord.quadcheck():
        contourcoord.calculateCentroid()
        corners = contourcoord.calculatetrtlbrbl()
        # for corner in corners:
        #     for nextcorner in corner:
        #         print nextcorner
        #         cv2.circle(source, (nextcorner[0], nextcorner[1]), 10, (0, 0, 255))
        source = cv2.pyrDown(source)
        warpedImage, transformationMatrix = persp.transform(corners)
        # warpedImage = cv2.pyrDown(warpedImage)
        cv2.imwrite("result.jpg", warpedImage)
        cv2.imshow("Warped Image", warpedImage)
        cv2.waitKey(0)
        print "0:successful write"
    else:
        print "1:not a quad"
        # except Exception:
        #     print "2:exception"
        # print contourcoord