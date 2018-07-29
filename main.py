#-*- coding:utf-8 -*-
import random
import time
import logging

import cv2
import uiautomator2 as u2

import setting
import utils

def get_logger(name):
	logger = logging.getLogger(name)
	logger.setLevel(logging.INFO)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger

log = get_logger('swbot')
random.seed(time.time())
d = u2.connect()

class Screen:
	def __init__(self):
		self.__LAST_SCREEN = None
		self.__KEEP_SCREEN = False
	def update(self):
		if self.__KEEP_SCREEN:
			return self.__LAST_SCREEN
		self.__LAST_SCREEN = d.screenshot(format='opencv')
		return self.__LAST_SCREEN
	def get(self):
		return self.__LAST_SCREEN
	def lock(self):
		self.__KEEP_SCREEN = True
	def unlock(self):
		self.__KEEP_SCREEN = False
	def __enter__(self):
		self.update()
		self.__KEEP_SCREEN = True
	def __exit__(self, _type, _value, _trace):
		self.__KEEP_SCREEN = False

screen = Screen()

def click(x, y):
	if setting.LOCK_CLICK:
		log.info('will click %s.', (x, y))
		img = screen.update().copy()
		utils.mark_point(img, (x, y))
		utils.show(img)
		return
	d.long_click(x, y, random.uniform(0.5, 2.5))

class Region:
	def __init__(self, l, r):
		self.l = l
		self.r = r
	def exist(self, template, **arg):
		img = self.get()
		res = utils.find_all_template(img, template, **arg)
		return True if len(res) > 0 else False
	def match(self, template, **arg):
		img = self.get()
		res = utils.find_all_template(img, template, **arg)
		return res
	def get(self):
		return utils.crop(screen.update(), self.l, self.r)
	def random_click(self):
		x = random.randint(self.l[0], self.r[0])
		y = random.randint(self.l[1], self.r[1])
		click(x, y)

def find_region(img, **arg):
	res = utils.find_all_template(screen.update(), img, **arg)
	if not res:
		return None
	res = res[0]['rectangle']
	return Region(res[0], res[3])

def R(path):
	return cv2.imread(path)
# def P(arg):
# 	if setting.DEBUG:
# 		print(arg)
# 	return arg
def sleep(t):
	time.sleep(t / 1000.0)
def write_tmp_images(prefix='main'):
	filename = './tmp/%s.%f.png' % (prefix, time.time())
	cv2.imwrite(filename, screen.update())

START_BATTLE = 'START_BATTLE.png'
UNDERGROUND = 'UNDERGROUND.png'
MANUAL_ICON = 'MANUAL_ICON.png'
AUTO_ICON = 'AUTO_ICON.png'
BATTLE_END = 'BATTLE_END.png'
BATTLE_FAILED = 'BATTLE_FAILED.png'
GET_RUNE = 'GET_RUNE.png'
GET_OTHER_REWARD = 'GET_OTHER_REWARD.png'
CLOSE_BUTTON = 'CLOSE_BUTTON.png'
START_AGAIN = 'START_AGAIN.png'
GIANT_UNDERGROUND = 'GIANT_UNDERGROUND.png'
GIANT_BOSS = 'GIANT_BOSS.png'
YELLOW = 'YELLOW.png'
MAIN_REGION = Region((0, 0), (d.info['displayWidth'], d.info['displayHeight']))
BATTLE_NAV_REGION = Region((0, 0), (1280, 50))
START_REGION = Region((970, 460), (1190, 555))
AUTO_REGION = Region((215, 655), (250, 690))
CENTER_REGION = Region((400, 200), (900, 500))
START_AGAIN_REGION = Region((230, 360), (580, 425))
REVIVE_REGION = Region((710, 440), (950, 500))
YELLOW_REGION = Region((30, 10), (200, 50))
BOSS_REGION = Region((600, 255), (670, 380))

class Basic_Battle:
	class App_Status:
		FINE = 0
		UNKNOWN = 1
		STOP = 2
		CONTINUE = 3
	def __init__(self, max_runtimes=-1, max_filltimes=0, wait_time=1500):
		self.max_runtimes = max_runtimes
		self.max_filltimes = max_filltimes
		self.wait_time = wait_time
		self.current_runtimes = 0
		self.current_winwimes = 0
		self.current_filltimes = 0
		self.last_event = None
		self.last_env = None
		self.last_status = Basic_Battle.App_Status.FINE
		self.constant_unknown_status = 0
		self.max_constant_unknown_status = 10
	def _get_status(self, event, env):
		return event, env
	def get_status(self):
		event, env = 'UNKNOWN', {}
		with screen:
			if MAIN_REGION.exist(R(START_BATTLE)):
				event = 'START_BATTLE'
			elif MAIN_REGION.exist(R(MANUAL_ICON), threshold=0.8):
				event = 'IN_BATTLE'
				env['auto'] = False
			elif MAIN_REGION.exist(R(AUTO_ICON), threshold=0.8):
				event = 'IN_BATTLE'
				env['auto'] = True
			elif MAIN_REGION.exist(R(BATTLE_END)):
				event = 'BATTLE_END'
				env['win'] = True
			elif MAIN_REGION.exist(R(BATTLE_FAILED)):
				event = 'BATTLE_END'
				env['win'] = False
			elif MAIN_REGION.exist(R(GET_RUNE)):
				event = 'GET_REWARD'
				env['type'] = 'RUNE'
			elif MAIN_REGION.exist(R(GET_OTHER_REWARD)):
				event = 'GET_REWARD'
				env['type'] = 'GET_OTHER_REWARD'
			elif MAIN_REGION.exist(R(START_AGAIN)):
				event = 'START_AGAIN'
			event, env = self._get_status(event, env)
		return event, env
	def _single_run(self, app_status, event, env):
		return app_status
	def _handle_reward(self, event, env):
		screen.lock()
		find_region(R(CLOSE_BUTTON)).random_click()
		screen.unlock()
	def _report(self):
		pass
	def single_run(self):
		AS = Basic_Battle.App_Status
		app_status = AS.FINE
		event, env = self.get_status()
		log.info('event = %s, env = %s', event, env)
		app_status = self._single_run(app_status, event, env)
		if app_status in (AS.STOP, AS.CONTINUE, AS.UNKNOWN):
			return app_status
		if event == 'UNKNOWN':
			return Basic_Battle.App_Status.UNKNOWN
		if event == 'START_BATTLE':
			START_REGION.random_click()
		elif event == 'IN_BATTLE':
			if not env['auto']: AUTO_REGION.random_click()
		elif event == 'BATTLE_END':
			self.current_runtimes += 1
			if env['win']:
				self.current_winwimes += 1
				CENTER_REGION.random_click()
				sleep(1000)
				CENTER_REGION.random_click()
			else:
				log.info('Not REVIVE!!')
				REVIVE_REGION.random_click()
				sleep(1200)
				CENTER_REGION.random_click()
				sleep(200)
		elif event == 'GET_REWARD':
			self._handle_reward(event, env)	
		elif event == 'START_AGAIN':
			START_AGAIN_REGION.random_click()
	def run(self):
		AS = Basic_Battle.App_Status
		wt = self.wait_time
		while True:
			sleep(wt)
			timer = utils.Timer()
			current_app_status = self.single_run()
			log.info('Single run was finished, cost around %d ms.', timer.point())
			log.info('Current run times: %d, win wimes: %d.', self.current_runtimes, self.current_winwimes)
			self._report()
			if current_app_status == AS.STOP:
				break
			if current_app_status == AS.CONTINUE:
				continue
			if current_app_status == AS.UNKNOWN and self.last_status == AS.UNKNOWN:
				self.constant_unknown_status += 1
				if self.constant_unknown_status == self.max_constant_unknown_status:
					log.info('UNKNOWN status keeps %d times. Write the screen img to disc.')
					write_tmp_images()
				if self.constant_unknown_status >= self.max_constant_unknown_status:
					wt *= 1.1
					log.info('Retry... Wait around %d ms', wt)
			else:
				self.constant_unknown_status = 0
				wt = self.wait_time
			self.last_status = current_app_status

class Underground_Battle(Basic_Battle):
	def __init__(self, target_boss=True, **args):
		super().__init__(**args)
		self.get_rune_times = 0
		self.get_other_reward_times = 0
		self.target_boss = target_boss
		self.targeted_boss = False
	def _get_status(self, event, env):
		if event == 'IN_BATTLE' and self.target_boss:
			env['boss'] = YELLOW_REGION.exist(R(YELLOW), rgb=True)
		return event, env
	def should_keep_runes(self):
		screen.update()
		identity = False
		if not identity:
			write_tmp_images(prefix='rune')
			return True
		return True
	def _report(self):
		log.info('Rune: %d, Other reward: %d.', self.get_rune_times, self.get_other_reward_times)
	def _handle_reward(self, event, env):
		screen.lock()
		if env['type'] == 'RUNE':
			self.get_rune_times += 1
			if self.should_keep_runes():
				find_region(R(GET_RUNE)).random_click()
			else:
				pass
		else:
			self.get_other_reward_times += 1
			find_region(R(CLOSE_BUTTON)).random_click()
		screen.unlock()
	def _single_run(self, app_status, event, env):
		if event == 'IN_BATTLE' and self.target_boss:
			if 'boss' in env and env['boss']:
				if not self.targeted_boss:
					BOSS_REGION.random_click()
					self.targeted_boss = True
			else:
				self.targeted_boss = False

if __name__ == '__main__':
	Underground_Battle(**setting.UNDERGROUND_SETTINGS).run()
	# tmp_img = MAIN_REGION.get()
	# cv2.imwrite('img.png', tmp_img)
