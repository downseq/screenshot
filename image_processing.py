import cv2
import numpy as np
import postgresql
import os
import datetime
import error_log
import db_conf
from PIL import Image, ImageGrab
import time

images_folder = "images/"

def searchCards(screen_area, deck, list_length, iteration_count):
    # begin_time = time.time()
    hand = ''
    threshold = 0.98
    for item in range(iteration_count):
        hand = ''
        for value in deck:
            try:
                path = getLastScreen(screen_area)
                path = path[0]['image_path']
                img_rgb = cv2.imread(path, 0)
                template = cv2.imread(str(value['image_path']), 0)
                res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= threshold)
                if len(loc[0]) != 0:
                    hand += value['alias']
                if len(hand) == list_length:
                    # end_time = time.time()
                    # print(end_time - begin_time)
                    return hand
            except Exception as e:
                error_log.errorLog('searchCards', str(e))
                print(e)
        threshold -= 0.01
    return hand

#Вставка пути к изображению в бд
def insertImagePathIntoDb(image_path,screen_area):
    try:
        db = postgresql.open(db_conf.connectionString())
        insert = db.prepare("insert into screenshots (image_path,screen_area) values($1,$2)")
        insert(image_path, screen_area)
    except Exception as e:
        error_log.errorLog('insertImagePathIntoDb',str(e))


#Получение информации об области экрана, на которой будет делаться скриншот
def getScreenData():
    try:
        db = postgresql.open(db_conf.connectionString())
        data = db.query("select x_coordinate,y_coordinate,width,height,screen_area,x_mouse,y_mouse from screen_coordinates "
                        "where active = 1 and alias = 'workspace'")
        return data
    except Exception as e:
        error_log.errorLog('getScreenData',str(e))

#Проверка на существование папок
def checkIsFolderExist():
    folder_name = images_folder + str(datetime.datetime.now().date())
    if not os.path.exists(str(folder_name)):
        os.makedirs(str(folder_name))
    db = postgresql.open(db_conf.connectionString())
    data = db.query("select screen_area from screen_coordinates "
                    "union select screen_area from opponent_screen_coordinates")
    for value in data:
        if not os.path.exists(str(folder_name) + "/" + str(value['screen_area'])):
            os.makedirs(str(folder_name) + "/" + str(value['screen_area']))

#Получение путей к изображениям шаблонов карт
def getCards():
    db = postgresql.open(db_conf.connectionString())
    data = db.query("select trim(image_path) as image_path, trim(alias) as alias from cards")
    return data

#Получение путей к изображениям шаблонов карт флопа
def getFlopCards():
    db = postgresql.open(db_conf.connectionString())
    data = db.query("select trim(image_path) as image_path,card,suit,trim(alias) as alias from flop_cards")
    return data

#Получение последнего скрина для текущей области экрана
def getLastScreen(screen_area, limit='1'):
    db = postgresql.open(db_conf.connectionString())
    data = db.query("select trim(image_path)as image_path from screenshots where screen_area = " + str(screen_area) + " order by id desc limit " + limit)
    return data

#Получение инфа для поиска элемента на изображении
def getUIButtonData(alias):
    try:
        db = postgresql.open(db_conf.connectionString())
        data = db.query("select x_coordinate,y_coordinate,width,height,screen_area,x_mouse,y_mouse from screen_coordinates "
                        "where active = 1 and alias = '" + alias + "'")
        return data
    except Exception as e:
        error_log.errorLog('getUIButtonData',str(e))
        print(e)

# Делаем скрин указанной области экрана
def madeScreenshot(x_coordinate, y_coordinate, width, height):
    image = ImageGrab.grab(bbox=(x_coordinate, y_coordinate, width, height))
    return image

def imaging(x_coordinate, y_coordinate, width, height, image_path, screen_area):
    image = madeScreenshot(x_coordinate, y_coordinate, width, height)
    image.save(image_path, "PNG")
    insertImagePathIntoDb(image_path, screen_area)

def searchElement(screen_area, elements, folder):
    for item in elements:
        path = getLastScreen(screen_area)
        path = path[0]['image_path']
        img_rgb = cv2.imread(path, 0)
        template = cv2.imread(folder + item + '.png', 0)
        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.98
        loc = np.where(res >= threshold)

        if len(loc[0]) != 0:
            return True
        return False

def getCurrentCards(condition):
    db = postgresql.open(db_conf.connectionString())
    data = db.query("select trim(image_path) as image_path, trim(alias) as alias from cards where alias in(" + condition + ")")
    return data

def convertHand(hand):
    hand = '\'' +  hand[0] + hand[1] + '\'' + ',' + '\'' + hand[2] + hand[3] + '\''
    return hand

def checkCurrentHand(screen_area, hand):
    current_hand = convertHand(hand)
    deck = getCurrentCards(current_hand)
    if len(searchCards(screen_area, deck, 4, 1)) == 4:
        return True
    else: return False