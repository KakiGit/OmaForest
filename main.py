import requests
import re
import pycookiecheat
import time
import cv2
import numpy as np

s = requests.Session()
fc_url = "https://f-tep.com/secure/api/v2.0/services/1"
cookies = pycookiecheat.chrome_cookies(fc_url)
fc_res = s.get(fc_url, cookies = cookies)

jc_url = "https://f-tep.com/secure/api/v2.0/jobConfigs"
INPUTS = [
    "sentinel2:///S2A_MSIL1C_20180801T095031_N0206_R079_T35VMK_20180801T134045",
    "sentinel2:///S2A_MSIL1C_20190630T100031_N0207_R122_T35VMK_20190630T120400"
]

AOI = "POLYGON((25.643131693359464 63.01498960365606,25.643131693359464 62.99755820039144,25.691101775737476 62.99755820039144,25.691101775737476 63.01498960365606,25.643131693359464 63.01498960365606))"

app_conf = {
  "service": fc_url,
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

# creating jobConfig
job_config_res = s.post(jc_url, json = app_conf, cookies = cookies)
print(job_config_res, job_config_res.text)
job_config_res_json = job_config_res.json()
job_config_href = job_config_res_json["_links"]["self"]["href"]
print(job_config_href)

# launch job
job_launch_res = s.post(job_config_href + "/launch", cookies = cookies)
print(job_launch_res, job_launch_res.text)
job_launch_res_json = job_launch_res.json()
job_href = job_launch_res_json["_links"]["self"]["href"]

# check job status
job_res = s.get(job_href, cookies = cookies)
job_res_json = job_res.json()
while r4j["status"] != "COMPLETE":
    job_res = s.get(job_href, cookies = cookies)
    job_res_json = job_res.json()
    time.sleep(1)

# download tif
dl_url = job_res_json["_links"]["output-result"]["href"] + "/dl"
dl_url = "https://f-tep.com/secure/api/v2.0/ftepFiles/120666" + "/dl"
dl_res = s.get(dl_url, cookies = cookies)
FC_TIF = "2018-2019.tif"
with open(FC_TIF, "wb") as f:
    f.write(dl_res.content)

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
