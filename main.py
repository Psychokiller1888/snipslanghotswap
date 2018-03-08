#!/usr/bin/python
# -*- coding: utf-8 -*-

# 2018 - Psychokiller1888 / Laurent Chervet
# If you find any bugs, please report on github
# If reusing keep credits

import json
import paho.mqtt.client 	as mqtt
import sqlite3
import subprocess
import time

_INTENT_SWITCH_LANGUAGE 	= 'hermes/intent/Psychokiller1888:languageSwitch'
_INTENT_ASK_LANGUAGE 		= 'hermes/intent/Psychokiller1888:askLanguage'

_LANGUAGES = {
	u'english'		: 'en',
	u'englisch'		: 'en',
	u'anglais'		: 'en',
	u'french' 		: 'fr',
	u'français'		: 'fr',
	u'französisch' 	: 'fr',
	u'german' 		: 'de',
	u'deutsch' 		: 'de',
	u'allemand' 	: 'de'
}

_CONFIRMATIONS = {
	u'en': "Sure, let's speak english!",
	u'fr': "D'accord, parlons français!",
	u'de': "Sicher, lass uns deutsch sprechen!"
}

_ANSWERS = {
	u'en': "I speak english",
	u'fr': "Je parle français",
	u'de': "Ich spreche deutsch"
}

_mqttClient = mqtt.Client()
_configs = {}

def onConnect(client, userdata, flags, rc):
	_mqttClient.subscribe(_INTENT_SWITCH_LANGUAGE)
	_mqttClient.subscribe(_INTENT_ASK_LANGUAGE)

def onMessage(client, userdata, message):
	data = json.loads(message.payload)
	sessionId = data['sessionId']
	slots = dict((slot['slotName'], slot['rawValue']) for slot in data['slots'])

	if message.topic == _INTENT_SWITCH_LANGUAGE:

		if 'language' not in slots or slots['language'].lower() not in _LANGUAGES:
			print('Sorry, this language is not supported ({})'.format(slots['language'].lower()))
			return
		else:
			languageCode = _LANGUAGES[slots['language'].lower()]

		if updateConfig('language', languageCode):
			# End this session
			_mqttClient.publish('hermes/dialogueManager/endSession', json.dumps({
				'sessionId': sessionId,
				'text': ''
			}))

			time.sleep(0.5)
			subprocess.call(['./langSwitch.sh', languageCode])

			# Confirm the switch
			_mqttClient.publish('hermes/dialogueManager/startSession', json.dumps({
				'init': {
					'type': 'notification',
					'text': _CONFIRMATIONS[languageCode]
				}
			}))
		else:
			print('Error updating language configuration, aborting')

	elif message.topic == _INTENT_ASK_LANGUAGE:
		_mqttClient.publish('hermes/dialogueManager/endSession', json.dumps({
			'sessionId': sessionId,
			'text': _ANSWERS[_configs['language']]
		}))

def loadConfigs():
	database = sqlite3.connect('data.db')
	cursor = database.cursor()
	try:
		cursor.execute("SELECT configName, configValue FROM configs")
		rows = cursor.fetchall()
		for row in rows:
			_configs[row[0]] = row[1]
	except sqlite3.OperationalError as e:
		print('Error fetching data from database, makesure data.db is available')
		raise e
	finally:
		database.close()

def updateConfig(configName, configValue):
	database = sqlite3.connect('data.db')
	cursor = database.cursor()
	try:
		statement = "UPDATE configs SET configValue=:value WHERE configName=:name"
		cursor.execute(statement, {'value': configValue, 'name': configName})
		database.commit()
		_configs[configName] = configValue
	except sqlite3.OperationalError:
		print("Couldn't update config")
		return False
	finally:
		database.close()

	return True

if __name__ == '__main__':
	loadConfigs()
	_mqttClient = mqtt.Client()
	_mqttClient.on_connect = onConnect
	_mqttClient.on_message = onMessage
	_mqttClient.connect('localhost', 1883)
	print('Demo started in "{}"'.format(_configs['language']))
	_mqttClient.loop_forever()