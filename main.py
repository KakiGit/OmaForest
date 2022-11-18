import requests
import re
import pycookiecheat
import time
import cv2
import numpy as np

JC_URL = "https://f-tep.com/secure/api/v2.0/jobConfigs"
INPUTS = [
    "sentinel2:///S2A_MSIL1C_20180801T095031_N0206_R079_T35VMK_20180801T134045",
    "sentinel2:///S2A_MSIL1C_20190630T100031_N0207_R122_T35VMK_20190630T120400"
]

AOI = "POLYGON((25.643131693359464 63.01498960365606,25.643131693359464 62.99755820039144,25.691101775737476 62.99755820039144,25.691101775737476 63.01498960365606,25.643131693359464 63.01498960365606))"
FC_URL = "https://f-tep.com/secure/api/v2.0/services/1"

FC_TIF = "2018-2019.tif"


class OmaForest():
    def __init__(self):
        self.session = requests.Session()
        self.cookies = pycookiecheat.chrome_cookies(FC_URL)

    def _post(self, url, **args):
        return self.session.post(url, cookies = self.cookies, **args)

    def _get(self, url, **args):
        return self.session.get(url, cookies = self.cookies, **args)

    def create_job_config(self, app_conf):
        job_config_res = self._post(JC_URL, json = app_conf)
        # print(job_config_res, job_config_res.text)
        if not job_config_res.ok:
            return ""
        job_config_res_json = job_config_res.json()
        return job_config_res_json["_links"]["self"]["href"]

    def launch_job(self, job_config_href):
        print(job_config_href)
        job_launch_res = self._post(job_config_href + "/launch")
        # print(job_launch_res, job_launch_res.text)
        if not job_launch_res.ok:
            return ""
        job_launch_res_json = job_launch_res.json()
        return job_launch_res_json["_links"]["self"]["href"]

    def check_job_result(self, job_href):
        job_res = self._get(job_href)
        if not job_res.ok:
            return {}
        job_res_json = job_res.json()
        while job_res_json["status"] != "COMPLETED":
            job_res = self._get(job_href)
            if not job_res.ok:
                return {}
            job_res_json = job_res.json()
            time.sleep(1)
        return job_res_json

    def download_tif(self, job_res_json):
        dl_url = job_res_json["_links"]["output-result"]["href"] + "/dl"
        dl_res = self._get(dl_url)
        # print(dl_res)
        with open(FC_TIF, "wb") as f:
            f.write(dl_res.content)

    def process_tif(self):
        img = cv2.imread(FC_TIF)
        # create hull array for convex hull points
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        hull = []

        # calculate points for each contour
        for i in range(len(contours)):
            # creating convex hull object for each contour
            hull.append(cv2.convexHull(contours[i], False))
        # create an empty black image
        drawing = np.zeros((thresh.shape[0], thresh.shape[1], 3), np.uint8)

        # draw contours and hull points
        for i in range(len(contours)):
            color_contours = (0, 255, 0) # green - color for contours
            color = (125, 255, 79) # blue - color for convex hull
            # draw ith contour
            if cv2.contourArea(contours[i]) > 50:
                # cv2.drawContours(drawing, contours, i, color_contours, 1, 8, hierarchy)
            # draw ith convex hull object
                cv2.drawContours(drawing, hull, i, color, 2, 8)
        cv2.imshow('harvested',drawing)
        cv2.imshow('origin',img)
        cv2.waitKey(0)


def main():
    app_conf = {
      "service": FC_URL,
      "inputs": {
          "startproduct": [
              INPUTS[0]
            ],
          "endproduct": [
              INPUTS[1]
          ],
          "aoi": [
              AOI
          ],
          "targetResolution": [
            "10"
          ]
        }
    }
    omaforest = OmaForest()
    jc_href = omaforest.create_job_config(app_conf)
    if not jc_href:
        raise
    job_href = omaforest.launch_job(jc_href)
    if not job_href:
        raise
    job_res = omaforest.check_job_result(job_href)
    print(job_res)
    omaforest.download_tif(job_res)
    omaforest.process_tif()

if __name__ == "__main__":
    main()
