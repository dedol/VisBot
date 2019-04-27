# -*- coding: utf-8 -*-
import vk_api
import requests
import time
import json
import random
import sys
import argparse
import re
from python_rucaptcha import ImageCaptcha
import hashlib
import vkcoin

dicts = []
file = open('dict.txt', 'r', encoding='utf-8')
for line in file:
	dicts.append(line.split("\n")[0])

null_stat = {
	'а': 0, 'б': 0, 'в': 0, 'г': 0, 'д': 0, 'е': 0, 'ё': 0, 'ж': 0, 'з': 0, 'и': 0, 
	'й': 0, 'к': 0, 'л': 0, 'м': 0,	'н': 0, 'о': 0, 'п': 0, 'р': 0, 'с': 0, 'т': 0, 
	'у': 0, 'ф': 0, 'х': 0, 'ц': 0, 'ч': 0, 'ш': 0, 'щ': 0, 'ъ': 0, 'ы': 0, 'ь': 0,
	'э': 0, 'ю': 0, 'я': 0
}

def get_next_letter(search, exclude):
	search_list = [x for x in search+exclude]
	if "*" not in search_list:
		print("Маска должна содержать *")
		return 0

	usedChars = dict(null_stat)
	used = (search + exclude).lower().replace("*", '')

	for i in range(0, len(used)):
		usedChars[used[i]] = True

	if (used):
		exc = "[^" + used + "]"
	else:
		exc = "."

	patt = "^" + search.replace("*", exc) + "$";
	length = len(search)
	stat = dict(null_stat)

	for i in range(0, len(dicts)):
		word = dicts[i]
		result = re.search(patt, word)
		if result is None:
			continue
	
		letters_in_word = []
		for j in range(0, length):
			if word[j] not in search_list:
				if word[j] not in letters_in_word:
					stat[word[j]] += 1
					letters_in_word.append(word[j])
	
	for i in stat:
		if i[0] in search_list:
			stat[i[0]] = -1
	
	stat = list(stat.items())
	stat.sort(key=lambda i: i[1])
	return (stat[-1][0])

def captcha_handler(captcha):
	global captcha_count
	if captcha_enable:
		image_link = format(captcha.get_url()).strip()
		user_answer = ImageCaptcha.ImageCaptcha(rucaptcha_key=rucaptcha_key).captcha_handler(captcha_link=image_link)
		
		if not user_answer['error']:
			# print(console_time(), "captcha:", user_answer['captchaSolve'])
			key = user_answer['captchaSolve']
			captcha_count += 1
	
		elif user_answer['error']:
			key = "error"
			print(user_answer['errorBody']['text'])
			print(user_answer['errorBody']['id'])
	else:
		key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
		captcha_count += 1

	return captcha.try_again(key)

def createParser ():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-t', '--token', default='')
	parser.add_argument ('-c', '--captcha', default='')
	parser.add_argument ('-gi', '--games_interval', default=10)
	parser.add_argument ('-mi', '--messages_interval', default=2)
	parser.add_argument ('-wv', '--withdraw_value', default=100000)
	parser.add_argument ('-k', '--key', default='')
	parser.add_argument ('-m', '--master_id', default=0)
	return parser

def console_time():
	# string = "[" + time.strftime('%d-%m-%Y %H:%M:%S') + "][" + str(user_id) + "]"
	string = "[" + time.strftime('%d %b %H:%M:%S') + "][id" + str(user_id) + "]"
	return string

def send(text):
	random_id = random.randint(-2147483648, 2147483647)
	vk.method("messages.send", {"peer_id": peer_id, "message": text, "random_id": random_id})

def withdraw_to_wallet():
	if (balance >= withdraw_value) and (balance > 3000) and (withdraw_value != 0):
		time.sleep(5)
		withdraw_amount = balance - 3000
		print(console_time(), "Делаем запрос на вывод", withdraw_amount, "coins")
		send("&#9194; Вывести")
		time.sleep(5)
		send(withdraw_amount)
		balance_text = get_balanse_text(balance - withdraw_amount)
		# print(console_time(), "Текущий баланс:", balance_text, "coins")
		if vkcoin_enable:
			time.sleep(5)
			vkcoin_balance = merchant.get_my_balance()["response"][str(user_id)]
			time.sleep(1)
			transfer = merchant.send_coins(master_id, vkcoin_balance)
			print(console_time(), "Переводено", int(vkcoin_balance/1000), "coins на аккаунт", master_id)
	else:
		withdraw_amount = 0
	return balance - withdraw_amount

def get_balanse_text(balance):
	if balance > 0:
		if int(balance/1000) > 0:
			balance_text = str(int(balance/1000)) + "к"
		else:
			balance_text = balance
	else:
		balance_text = 0
	return balance_text

print("")
print("VisBot for vk.com/vcoingame1")
print("Version: 1.2 | 27 Apr 2019")
print("(c) dedol.ru, 2019")
print("")

try:
	parser = createParser()
	namespace = parser.parse_args(sys.argv[1:])
	 
	token = namespace.token
	rucaptcha_key = namespace.captcha
	games_interval = int(namespace.games_interval)
	messages_interval = int(namespace.messages_interval)
	withdraw_value = int(namespace.withdraw_value) + 3000
	key = namespace.key
	master_id = int(namespace.master_id)

	vk = vk_api.VkApi(token = token, captcha_handler=captcha_handler)
	
	user_id = vk.method("users.get")[0]["id"]

	vkcoin_enable = False
	if (key != "") and (master_id != 0):
		vkcoin_enable = True
		merchant = vkcoin.VKCoinApi(user_id=user_id, key=key)

except Exception as E:
	print("Exception:", E)
	print("Ошибка при запуске программы! Проверьте свой vk token и параметры запуска!")
	input()
	sys.exit(1)

captcha_enable = True
if rucaptcha_key == "":
	captcha_enable = False

balance = 0
win_count = 0
lose_count = 0
captcha_count = 0
message_count = 0
peer_id = -181113882
first_message = True

send("&#128176; Баланс")
while True:
	try:
		time.sleep(0.5)
		messages = vk.method("messages.getConversations", {"offset": 0, "count": 20, "filter": "all"})["items"]
		
		for message in messages:
			if message["conversation"]["peer"]["id"] == peer_id:
				first_message = False
				if message["last_message"]["text"].split("\n")[0].find("Отгаданные буквы") == -1:
	
					if message["last_message"]["text"].split("\n")[0].find("Вы проиграли") > -1:
						lose_count += 1
						balance -= 1000
						balance_text = get_balanse_text(balance)
						print(console_time(), " Поражение! Баланс: ", balance_text, " | Статистика: [", win_count, "|", lose_count, "] | Капч: ", captcha_count, sep="")
						# print(console_time(), " Поражение! (", win_count, "|", lose_count, ") ", "Баланс: ", balance_text, " | Капч: ", captcha_count, sep="")
						time.sleep(games_interval)
					elif message["last_message"]["text"].split("\n")[0].find("Вы выиграли") > -1:
						win_count += 1
						balance += 1000
						balance_text = get_balanse_text(balance)
						print(console_time(), " Победа! Баланс: ", balance_text, " | Статистика: [", win_count, "|", lose_count, "] | Капч: ", captcha_count, sep="")
						# print(console_time(), " Победа! (", win_count, "|", lose_count, ") ", "Баланс: ", balance_text, " | Капч: ", captcha_count, sep="")
						balance = withdraw_to_wallet()
						time.sleep(games_interval)
					elif message["last_message"]["text"].split("\n")[0].find("Ваш баланс") > -1:
						balance = int(message["last_message"]["text"].split("\n")[0].split(":")[1].split(".")[0].strip())
						balance_text = get_balanse_text(balance)
						print(console_time(), "Ваш баланс:", balance_text, "coins")
						# print(console_time(), "Начнем игру через", messages_interval, "сек!")
						time.sleep(messages_interval)
					elif message["last_message"]["text"].split("\n")[0].find("сегодня слишком много") > -1:
						print(console_time(), "Вы выиграли сегодня слишком много! Пауза 30 мин!")
						time.sleep(30*60)
					else:
						# print(console_time(), "Начнем игру через", messages_interval, "сек!")
						time.sleep(messages_interval)
					send("&#127924; Играть")
					# print(console_time(), "Играть")
	
				else:
					word_mask = message["last_message"]["text"].split("\n")[0].split(":")[1].strip()
					not_in_word = message["last_message"]["text"].split("\n")[1].split(":")[1].strip().replace(", ", "")
	
					# print(console_time(), word_mask, "|", not_in_word)
		
					next_letter = get_next_letter(word_mask, not_in_word)
	
					time.sleep(messages_interval)
					send(next_letter)
					# print(console_time(), next_letter)
					message_count += 1
	
		if (first_message):
			send("&#127924; Играть")

		if message_count > 100:
			send("&#128176; Баланс")
			message_count = 0

	except Exception as E:
		print(console_time(), "Exception:", E)
