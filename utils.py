#-*- coding:utf-8 -*-
import math
import random
import time

import cv2


class Timer:
	def __init__(self):
		self.start_time = time.time()
	def point(self):
		runtime = time.time() - self.start_time
		return runtime * 1000

class Temperature:
	'''
	模拟升火，温度越高，越大概率触发
	防止游戏检测脚本
	'''
	start_temperature = 1
	increase_steps = 1.0099
	delta_temperature = 100
	def clear(self):
		self.T = Temperature.start_temperature
	def __init__(self):
		self.clear()
	def ask(self):
		self.T *= Temperature.increase_steps
		return random.random() < math.exp(-Temperature.delta_temperature / self.T)


def mark_point(img, pt):
	''' 调试用的: 标记一个点 '''
	x, y = pt
	radius = 20
	cv2.circle(img, (x, y), radius, 255, thickness=2)
	cv2.line(img, (x-radius, y), (x+radius, y), 100) # x line
	cv2.line(img, (x, y-radius), (x, y+radius), 100) # y line
	return img

def show(img):
	''' 显示一个图片 '''
	cv2.namedWindow('image', cv2.WINDOW_NORMAL)
	cv2.imshow('image', img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def find_all_template(im_source, im_search, threshold=0.5, maxcnt=0, rgb=False, bgremove=True):
	'''
	Locate image position with cv2.templateFind
	Use pixel match to find pictures.
	Args:
			im_source(string): 图像、素材
			im_search(string): 需要查找的图片
			threshold: 阈值，当相识度小于该阈值的时候，就忽略掉
	Returns:
			A tuple of found [(point, score), ...]
	Raises:
			IOError: when file read error
	'''
	# method = cv2.TM_CCORR_NORMED
	# method = cv2.TM_SQDIFF_NORMED
	method = cv2.TM_CCOEFF_NORMED
	if rgb:
		s_bgr = cv2.split(im_search) # Blue Green Red
		i_bgr = cv2.split(im_source)
		weight = (0.3, 0.3, 0.4)
		resbgr = [0, 0, 0]
		for i in range(3): # bgr
			resbgr[i] = cv2.matchTemplate(i_bgr[i], s_bgr[i], method)
		res = resbgr[0]*weight[0] + resbgr[1]*weight[1] + resbgr[2]*weight[2]
	else:
		s_gray = cv2.cvtColor(im_search, cv2.COLOR_BGR2GRAY)
		i_gray = cv2.cvtColor(im_source, cv2.COLOR_BGR2GRAY)
		# 边界提取(来实现背景去除的功能)
		if bgremove:
			s_gray = cv2.Canny(s_gray, 100, 200)
			i_gray = cv2.Canny(i_gray, 100, 200)
		res = cv2.matchTemplate(i_gray, s_gray, method)
	w, h = im_search.shape[1], im_search.shape[0]

	result = []
	while True:
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
			top_left = min_loc
		else:
			top_left = max_loc
		# if setting.DEBUG: 
		# 		P('templmatch_value(thresh:%.1f) = %.3f' %(threshold, max_val)) # not show debug
		if max_val < threshold:
			break
		# calculator middle point
		middle_point = (top_left[0]+w/2, top_left[1]+h/2)
		result.append(dict(
						result=middle_point,
						rectangle=(top_left, (top_left[0], top_left[1] + h), (top_left[0] + w, top_left[1]), (top_left[0] + w, top_left[1] + h)),
						confidence=max_val
		))
		if maxcnt and len(result) >= maxcnt:
			break
		# floodfill the already found area
		cv2.floodFill(res, None, max_loc, (-1000,), max_val-threshold+0.1, 1, flags=cv2.FLOODFILL_FIXED_RANGE)

	# P('cost ' + str(timer.log()) + ' ms')
	return result

def crop(img, pt1, pt2):
	x1, y1 = pt1
	x2, y2 = pt2
	return img[y1:y2, x1:x2]
