from random import uniform, random
from yargy import Parser, rule, or_
from yargy.predicates import eq, type as type_, in_, dictionary
from yargy.predicates.bank import gram
from loguru import logger
from loader import  dbAlerts, token_send, token_inc, chat_id_send, chat_id_inc, chat_id_send_new_format_chanel
import requests, time

import re

EDIT_BY_MIN = 0.01 / 100
EDIT_BY_MAX = 0.02 / 100

LATIN = type_('LATIN')
PUNCT = type_('PUNCT')
INT = type_('INT')
FLOAT = rule(
    INT,
    in_(',.'),
    INT
)
MIX = or_(FLOAT, rule(INT))
RANGE = rule(
    MIX,
    in_("−-"),
    MIX
)
VALUE_ = or_(MIX, RANGE)
MIXEG =  rule(VALUE_, eq(',').optional())
NOUN = gram('NOUN')
RU = type_('RU')
RUL_PAIR = or_(
    rule(dictionary({'название'}), dictionary({'стратегии'}), PUNCT.optional(), LATIN,),
    rule(LATIN, dictionary({'по', 'на'}), VALUE_),
    rule(LATIN, PUNCT.optional(), dictionary({'по', 'на', 'берите'}), dictionary({'берем', 'спот', 'лонг', 'шорт'}).optional()),
    rule(LATIN, PUNCT.optional(),  dictionary({'берем', 'хедж', 'спот', 'лонг', 'шорт'})),
    rule(dictionary({'если', 'точка'}), dictionary({'цена', 'входа'}), eq('(').optional(), dictionary({'пробивает', 'может'}), dictionary({'ещё'}).optional(), dictionary({'измениться'}).optional(), eq(')').optional(), eq(':').optional(), VALUE_),
    rule(dictionary({'вход', 'по'}), eq(':').optional(), VALUE_),
    rule(dictionary({'стоп'}), eq('-').optional(), dictionary({'лимит', 'лосс'}).optional(), eq(':').optional(), VALUE_)
)
RUL_DEPOSITE = or_(
    rule(dictionary({'на'}), VALUE_, eq('%').optional(), dictionary({'от'}), dictionary({'депо'})),
    rule(dictionary({'депозит'}), eq(':').optional(), VALUE_, eq('%').optional())
)
RUL_STOP = rule(dictionary({'стоп'}), eq('-').optional(), dictionary({'лимит'}).optional(), eq(':').optional(), VALUE_)
RUL_TYPE_OF = rule(dictionary({"Спот", "Лонг", "Шорт", "Споту", "Лонгу", "Шорту"}))

LIST_WELCOME = ["Спот", "Лонг", "Шорт"]

RUL_GOAL = or_(
    rule(dictionary({'цель'}), INT.optional(), eq(':').optional(), MIXEG.repeatable()),
    rule(dictionary({'без', 'нет'}), dictionary({'цель'}))
)
RUL_LENGHT = or_(
    rule(dictionary({'плечо'}), eq(':').optional(), VALUE_, eq('x').optional())
)
RUL_FIX = or_(
    rule(RU.optional(), dictionary({'фикс'}), RU.optional()),
    rule(dictionary({'прибыль'}), eq(':').optional(), VALUE_, eq('%').optional())
)
RUL_LIM = or_(
    rule(dictionary({'если'}), dictionary({'цена'}), dictionary({'пробивает'})),
    rule(dictionary({'приготовится'}), dictionary({'к'}))
)
RUL_MRK = or_(
    rule(dictionary({'лонг'}), dictionary({'с'}), dictionary({'текущих'})),
    rule(dictionary({'лонг'}), dictionary({'возможность'}).optional(), in_('.|').optional(), dictionary({'текущая'}), dictionary({'цена'})),
    rule(dictionary({'текущая'}), dictionary({'цена'})),
    rule(dictionary({'текущая'}), dictionary({'цена'}), eq(':').optional(), VALUE_)
)


parse_lim = Parser(RUL_LIM)
pars_mrk = Parser(RUL_MRK)

pars_0 = Parser(RUL_PAIR)
pars_1 = Parser(RUL_DEPOSITE)
pars_2 = Parser(RUL_STOP)
pars_3 = Parser(RUL_TYPE_OF)
pars_4 = Parser(RUL_GOAL)
pars_5 = Parser(RUL_LENGHT)
pars_6 = Parser(RUL_FIX)

def edit_number(number) -> float:
    is_negative = random() < 0.5
    edit_by = uniform(number*EDIT_BY_MIN, number*EDIT_BY_MAX)
    if is_negative:
        edit_by = -(edit_by)
    number += edit_by
    return number

# def return_pars_0():
#     pars_0 = 'test'
#     return pars_0

def edit_mes(message):
    text = []
    for string in message.split("\n"):
        if string != "":
            text.append(string)

    pair = ""
    type_of = ""
    price =  ""
    goal = ""
    auth_price = "Вход: "
    deposit_price = "Депозит: "
    length_price = "Плечо: "
    out_text = ""
    stop = ""
    res = {
        "symbol": "",
        "type": "",
        "price": "",
        "take_profit": [],
        "stop_price": "",
        "side" : "",
        'text': ""
    }

    
    refactoring_message = message.split("\n")

    # Делаем проверку на наличие Аномальных монет
    no_icon_symbol = refactoring_message[0].replace("📩", "")
    symbol_refactoring = no_icon_symbol.replace("#", "")
    symbol_refactoring = symbol_refactoring.replace(" ", "")
    
    if symbol_refactoring == '1000SHIBUSDTPERP':
        pair = '1000SHIBUSDTPERP'
    elif symbol_refactoring == '1INCHUSDTPERP':
        pair = '1INCHUSDTPERP' 
    elif symbol_refactoring == 'C98USDTPERP':
        pair = 'C98USDTPERP'

    # - Необходимо передать переменную message
    for matc in pars_3.findall(message):

        LONG = ['Лонг', 'Лонгу']
        SHORT = ['Шорт', 'Шорту']
        SPOT = ['Спот', 'Споту']

        type_of = [x.value for x in matc.tokens][0]

        if type_of in LONG:
            type_of = 'Лонг'
        elif type_of in SHORT:
            type_of = 'Шорт'
        else:
            type_of = 'Спот'

    for matc in pars_0.findall(message):
        if pair != "" and auth_price != "Вход: " and goal != "":
            out_text += pair + " " + type_of
            if deposit_price != "Депозит: ":
                out_text += "\n" + deposit_price
            if auth_price != "Вход: ":
                out_text += "\n" + auth_price
            if length_price != "Плечо: ":
                out_text += "\n" + length_price + "x"
            out_text += "\n" + goal

            if symbol_refactoring == '1000SHIBUSDTPERP':
                pair = '1000SHIBUSDTPERP'
            elif symbol_refactoring == '1INCHUSDTPERP':
                pair = '1INCHUSDTPERP'
            elif symbol_refactoring == 'C98USDTPERP':
                pair = 'C98USDTPERP'
            else:
                pair = ""
            goal = ""
            auth_price = "Вход: "
            length_price = "Плечо: "
            if stop != "":
                out_text += "\n\n" + stop + "\n\n"
            else:
                out_text += "\n"

        if pair == "" or auth_price == "Вход: ":
            for i in range(len(matc.tokens)):
                if [x.type for x in matc.tokens][i] == 'LATIN':
                    if pair == "":
                        pair = [x.value for x in matc.tokens][i]
                elif [x.type for x in matc.tokens][i] == 'INT':
                    auth_price += [x.value for x in matc.tokens][i]
                elif [x.type for x in matc.tokens][i] == 'PUNCT' and auth_price != "Вход: ":
                    auth_price += [x.value for x in matc.tokens][i]
        elif auth_price != "Вход: ":
            auth_price += " "
            for i in range(len(matc.tokens)):
                if [x.type for x in matc.tokens][i] == 'INT':
                    auth_price += [x.value for x in matc.tokens][i]
                elif [x.type for x in matc.tokens][i] == 'PUNCT' and [x.value for x in matc.tokens][i] != ":" and [x.value for x in matc.tokens][i] != "-" and [x.value for x in matc.tokens][i] != "!":
                    auth_price += [x.value for x in matc.tokens][i]

    for matc in parse_lim.findall(message):
        if res['type'] == '':
            res['type'] = 'limit'

    for matc in pars_mrk.findall(message):
        if res['type'] == '':
            res['type'] = 'market'
        if price == "":
            for i in range(len(matc.tokens)):
                if ([x.type for x in matc.tokens][i] == 'INT' or [x.type for x in matc.tokens][i] == 'PUNCT') and [x.value for x in matc.tokens][i] != ":":
                    price += [x.value for x in matc.tokens][i]
                elif [x.value for x in matc.tokens][i] == "−":
                    price += "-"

    for matc in pars_2.findall(string):
        if res['stop_price'] == "":
            for i in range(len(matc.tokens)):
                if ([x.type for x in matc.tokens][i] == 'INT' or [x.type for x in matc.tokens][i] == 'PUNCT') and [x.value for x in matc.tokens][i] != ":":
                    if [x.value for x in matc.tokens][i] != "−" and [x.value for x in matc.tokens][i] != '-':
                        res['stop_price'] += [x.value for x in matc.tokens][i]

    for matc in pars_4.findall(message):
        if len(matc.tokens) >= 2 and ([x.type for x in matc.tokens][1] == 'INT' or [x.type for x in matc.tokens][1] == 'PUNCT') :
            goal += "Цель: "
            pq = 0
            if [x.type for x in matc.tokens][1] == 'INT' and [x.value for x in matc.tokens][2] == ':':
                pq = 2
            for i in range(pq, len(matc.tokens)):
                if ([x.type for x in matc.tokens][i] == 'INT' or [x.type for x in matc.tokens][i] == 'PUNCT') and [x.value for x in matc.tokens][i] != ":":
                    if [x.value for x in matc.tokens][i] != ",":
                        goal += [x.value for x in matc.tokens][i]
                    else:
                        goal += "$" + [x.value for x in matc.tokens][i] + ' '
            goal += "$\n"
        else:
            goal += message + "\n"

    for matc in pars_5.findall(message):
        if length_price == "Плечо: ":
            for i in range(len(matc.tokens)):
                if ([x.type for x in matc.tokens][i] == 'INT' or [x.type for x in matc.tokens][i] == 'PUNCT') and [x.value for x in matc.tokens][i] != ":":
                    length_price += [x.value for x in matc.tokens][i]
                elif [x.value for x in matc.tokens][i] == "−":
                    length_price += "-"

    out_text += pair + " " + type_of
    if res['type'] == 'limit':
        out_text += "\n\nОтложенным ордером\n"
    elif res['type'] == 'market':
        out_text += "\n\nВход по рынку\n"
    if price != "":
        if res['type'] == "market":
            out_text += "\nТекущая цена: " + price 
        elif res['type'] == "limit": 

            auth_price_entrance =  auth_price.split(" ")[1]
            auth_price_entrance = '%.5f' % float(auth_price_entrance.replace(":", ""))
            out_text += "\nТочка входа: " + str(auth_price_entrance)
            
            # re.sub("[,|$]","",auth_price).split()[1] + "$"
            
    if deposit_price != "Депозит: ":
        out_text += "\n" + deposit_price

    if auth_price != "Вход: ":
        res["price"] = re.sub("[Вход:|,|$]","",auth_price).split()

    if type_of == "Лонг":
        res['side'] = "BUY"
    else:
        res['side'] = "SELL"
    if length_price != "Плечо: ":
        out_text += "\n" + length_price + "x"

    out_text +=  "\n" + goal
    res["symbol"] = pair
    res['take_profit'] = goal.replace("Цель:", "").replace(" ", "").replace(",", "")[:-2].split("$")

    if res['type'] == "limit":
        out_text += "\n" + 'Стоп: ' + auth_price.split()[2]
        res["stop_price"] = auth_price.split()[2]
    else:
        out_text += "\n" + 'Стоп: ' + auth_price.split(":")[1]
        res["stop_price"] = auth_price.split(" ")[1]

    res['text'] = out_text

    # print(f'Сообщение: \n {res["text"]} \n')

    return res

def edit_fix(message):
    text = []
    for string in message.split("\n"):
        if string != "":
            text.append(string)

    numb = ""
    pair = text[0]
    fix = ""
    fin = "Прибыль: "
    for string in text:
        for matc in pars_6.findall(string):

            for i in range(len(matc.tokens)):
                if ([x.type for x in matc.tokens][i] == 'RU'):
                    try:
                        if ('ADJF' in [x.forms for x in matc.tokens][i][0].grams.values) and ('Anum' in [x.forms for x in matc.tokens][i][0].grams.values):
                            numb = [x.forms for x in matc.tokens][i][0].normalized
                    except:
                        pass
                elif [x.type for x in matc.tokens][i] == 'INT':
                    fin += [x.value for x in matc.tokens][i]
                elif [x.type for x in matc.tokens][i] == 'PUNCT' and fin != "Прибыль: ":
                    fin += [x.value for x in matc.tokens][i]

    fix = "Фикс " + numb
    out = pair + fix + '\n' + fin

    return out

def refactoring_message_current_price(text):
    refactoring_message_for_candles_detected = text.split("\n")
    current_price = refactoring_message_for_candles_detected[1].split("|")[1]
    return current_price

def refactoring_message_candles_detected(text):
    candles_detected = ''
    refactoring_message_for_candles_detected = text.split("\n")
    for r in refactoring_message_for_candles_detected:
        for u in r.split(" "):
            if u == 'аномальные':
                candles_detected = "❗ Слишом резкое изменение цены - 4.32%. Повышенный риск!" + "\n\n"
                break
    return candles_detected

def value_for_purposes(varr):
    return '%.6f' % float(varr.split(":")[1].split(" ")[1].split("$")[0])

def main():
    time.sleep(3)
    message_all_card = dbAlerts.fetchall('SELECT * FROM message WHERE edited_post IS NULL AND send=0')

    i = 1
    meds = "["
    file_code = 0
    files = {}
    f_torg = False
    date_med = ""
    length = len(message_all_card)
    length_for_comparison = length - length
    if length != 0:
        for message_card in message_all_card:
            # i = i + 1
            id_out = ""
            text_original = message_card[5]  
            text_original = text_original.replace('#', '')
            
            if message_card[3] == "новости":
                if message_card[2] != 'Test open':
                    original_text = text_original.split("\n")
                    refactoring_text_repaer = [x for x in original_text if x]  
                    item = refactoring_text_repaer[0].split(" ")
                    first_item = "📄 " + "<b>Прошлые закрытые сделки: </b>" + "\n\n"
                    
                    repair = refactoring_text_repaer[-1].split(" ")[-1]
                    refactoring_text_repaer.pop(0)
                    refactoring_text_repaer.pop(-1)
                    refactoring_text_repaer.pop(-1)

                    coins_trade_repair = ''
                    for r in refactoring_text_repaer:
                        a = r.split(" ")
                        if a[0] != 'ETHUSDT' or a[0] != 'BTCUSDT':
                            a[0] = a[0][:-4]
                        r = " ".join(a)
                        
                        coins_trade_repair += r + "\n"
                    
                    
                    send_text = first_item + coins_trade_repair + "\n" + "Дата отчета: " + repair
                    try:
                        res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_send_new_format_chanel}&text={send_text}&parse_mode=HTML')

                        res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_inc}&text={text_original}&parse_mode=HTML')

                        dbAlerts.query(f'UPDATE message SET send=1 WHERE id={message_card[0]}')
                    except Exception as e:
                        print(e)


            if message_card[3] == "Отчет":
                if message_card[2] != 'Test open':

                    refactoring_text_repaer = text_original.split("\n")

                    item = refactoring_text_repaer[0].split(" ")
                    
                    s = item[3][:-4]
                    first_item = "📄 " + " " + item[1] + " " + item[2] + " " + s + "\n" + "(previous closed deal)" + "\n" + "------------------" + "\n"
                    two_item = ''
                    three_item = ''
                    four_item = ''
                    five_item = ''
                    for r in refactoring_text_repaer:
                        for i in r.split(" "):
                            if i == 'Пик.':
                                two_item = r + "\n"
                            elif i == 'Шорт':
                                i = r.split(" ")
                                item_price = i[-1]
                                three_item = "📉 " + "Шорт от " + item_price + "\n" 
                            elif i == 'Лонг':
                                i = r.split(" ")
                                item_price = i[-1]
                                three_item = "📈 " + "Лонг от " + item_price + "\n"
                            elif i == 'Время:':
                                four_item = r + "\n\n"
                            elif i == 'цели' or i == 'цель' or i == 'цель' or i == 'целей':
                                
                                a = r.split()
                                b = a[1]
                                if int(b) > 5:
                                    a[0] = '🔥'
                                    r = " ".join(a)
                                else:
                                    a[0] = '🎯'
                                    r = " ".join(a)

  
                                five_item = r

                    send_text = first_item + two_item + three_item + four_item + f'<b>{five_item}</b>'

                    try:
                        res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_send_new_format_chanel}&text={send_text}&parse_mode=HTML')

                        res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_inc}&text={text_original}&parse_mode=HTML')

                        dbAlerts.query(f'UPDATE message SET send=1 WHERE id={message_card[0]}')
                    except Exception as e:
                        print(e)

                    
            if message_card[3] == "торговый сигнал":

                # Аномальное изменение цены
                candles_detected = refactoring_message_candles_detected(message_card[5])

                if message_card[4] == 0:
                    text = edit_mes(message_card[5])['text']
                elif message_card[4] == 1:
                    text = message_card[5]  
                elif message_card[4] == 2:
                    text = message_card[5]

                if message_card[6] == None:

                    original_text = text.split("\n")
                    original_text = [x for x in original_text if x]
                                        
                    item_one = original_text[0].split(" ")
                    symbol = item_one[0][:-4]
                    
                    if item_one[1] == "Лонг" and original_text[1] == "Отложенным ордером":
                        one_item = "🚨 " + f'<b>{symbol}</b>' + "\n"
                        two_item = "⏱ Готовимся к лонгу" + "\n\n" + original_text[2] + "\n\n"
                        four_item = "- Детали сигнала -" + "\n" + "(могут измениться)" + "\n"
                    elif item_one[1] == "Шорт" and original_text[1] == "Отложенным ордером":
                        one_item = "🚨 " + f'<b>{symbol}</b>' + "\n"
                        two_item = "⏱ Готовимся к шорту" + "\n\n" + original_text[2] + "\n\n"
                        four_item = "- Детали сигнала -" + "\n" + "(могут измениться)" + "\n"
                    elif item_one[1] == "Лонг" and original_text[1] != "Отложенным ордером":
                        one_item = "🚀 " + f'<b>{symbol}</b>' + "\n"
                        two_item = "✅ Лонг" + " | " + "Цена: " + original_text[2].split(" ")[2] + "\n\n"
                        four_item = "- Детали сигнала -" + "\n"
                    elif item_one[1] == "Шорт" and original_text[1] != "Отложенным ордером":
                        one_item = "🚀 " + f'<b>{symbol}</b>' + "\n"
                        two_item = "✅ Шорт" + " | " + "Цена: " + original_text[2].split(" ")[2] + "\n\n"
                        four_item = "- Детали сигнала -" + "\n"
                    else:
                        # Пропускаем
                        print('⛔ Неизвестное сообщение для Николая Петровича - пропускаем.')

                    
                    # Преобразовываем тейки
                    probabilitys = message_card[5].split("\n")
                    probabilitys = [x for x in probabilitys if x]
                    
                    probabilitys_list = {}
                    item = 0
                    for p in probabilitys:
                        for u in p.split(" "):
                            if u == 'вероятность':
                                item = item + 1
                                probabilitys_list[f'{item}'] = p.split(" ")[5]
                    
                    value_for_purposes
                    # Значения целей
                    first_value = '%.6f' % float(original_text[4].split(":")[1].split(" ")[1].split("$")[0])
                    two_value = '%.6f' % float(original_text[5].split(":")[1].split(" ")[1].split("$")[0])
                    three_value = '%.6f' % float(original_text[6].split(":")[1].split(" ")[1].split("$")[0])
                    four_value = '%.6f' % float(original_text[7].split(":")[1].split(" ")[1].split("$")[0])
                    five_value = '%.6f' % float(original_text[8].split(":")[1].split(" ")[1].split("$")[0])
                    six_value = '%.6f' % float(original_text[9].split(":")[1].split(" ")[1].split("$")[0])

                    first_take = "Цель 1: " + str(first_value) + f" - вероятность {probabilitys_list['1']}"
                    two_take = "Цель 2: " + str(two_value) + f" - вероятность {probabilitys_list['2']}"
                    three_take = "Цель 3: " + str(three_value) + f" - вероятность {probabilitys_list['3']}"
                    four_take = "Цель 4: " + str(four_value) + f" - вероятность {probabilitys_list['4']}"
                    five_take = "Цель 5: " + str(five_value) + f" - вероятность {probabilitys_list['5']}"
                    six_take = "Цель 6: " +  str(six_value) + f" - вероятность {probabilitys_list['6']}"

                    five_item = first_take + "\n" + two_take + "\n" + three_take + "\n" + four_take + "\n" + five_take + "\n" + six_take + "\n\n"
                    
                    stop = '%.5f' % float(original_text[10].split(":")[1])
                    six_item = "⛔ Стоп: " + str(stop) + "\n\n"

                    seven_item = "🏦 Плечо: 5-10x изолированное" + "\n" + "💰 Объем: 5-10% от депозита"
        
                    if original_text[1] == "Отложенным ордером":
                        send_text = one_item + two_item + candles_detected + four_item + five_item + six_item + seven_item
                    else:
                        recomendations = "1. Фиксируйте прибыль частями по мере роста." + "\n" + "2. После достижения 2-4 цели, передвигайте SL на точку входа." + "\n" + "3. Закрывайте 80% позиции на 3-5 цели."
                        send_text = one_item + two_item + candles_detected + four_item + five_item + six_item + seven_item + "\n\n" + "- 👨‍💻 Рекомендации по стратегии -" + "\n" + recomendations

                    if message_card[2] != 'Test open':
                        res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_inc}&text={text_original}&parse_mode=HTML')
                        id_out += str(res.json()["result"]["message_id"])
                        dbAlerts.query(f'UPDATE message SET send=1, send_id="{id_out}" WHERE id={message_card[0]}')                
                        try:
                            res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_send_new_format_chanel}&text={send_text}&parse_mode=HTML')
                            dbAlerts.query(f'UPDATE message SET send=1, edited_post="{send_text}" WHERE id={message_card[0]}')
                        except Exception as e:
                            print(e)
                    
                    res = requests.get(f'https://api.telegram.org/bot{token_send}/sendMessage?chat_id={chat_id_send}&text={send_text}&parse_mode=HTML')
                    dbAlerts.query(f'UPDATE message SET send=1, edited_post="{send_text}" WHERE id={message_card[0]}')

                else:
                    f_torg = True

            if message_card[6] == None:
                pass
            else:

                if meds == "[" and date_med != message_card[1]:
                    date_med = message_card[1]
                    id_main = message_card[0]
                if date_med == message_card[1]:
                    if message_card[6][-3:] == "jpg" or message_card[6][-3:] == "png":
                        type_med = "photo"
                    elif message_card[6][-3:] == "ogg" or message_card[6][-3:] == "oga":
                        type_med = "voice"
                    elif message_card[6][-3:] == "mp3":
                        type_med = "audio"
                    else:
                        type_med = "document"
                    files.update({f"name{file_code}": open(message_card[6], "rb")})
                    meds += "{"
                    if f_torg == True and text_original != "":
                        meds += f'"type": "{type_med}", "media": "attach://name{file_code}", "caption": "{text}"'
                        dbAlerts.query(f'UPDATE message SET send=1, edited_post="{text}" WHERE id={message_card[0]}')
                    elif f_torg == False and text_original != "":
                        meds += f'"type": "{type_med}", "media": "attach://name{file_code}", "caption": "{text_original}"'
                    elif text_original == "":
                        meds += f'"type": "{type_med}", "media": "attach://name{file_code}"'
                    meds += "},"
                    file_code += 1
                    dbAlerts.query(f'UPDATE message SET send=1 WHERE id={message_card[0]}')


                    
                elif meds != "[" and (date_med != message_card[1] or message_all_card.index(message_card) == length_for_comparison):
                # elif meds != "[" and (date_med != message_card[1] or i == length):
                    meds += "]"
                    id_out = ""
                    if f_torg == True:
                        params = {
                        "chat_id": chat_id_send,
                        "media": meds
                        }
                        if message_card[11] != "":
                            params.update({"reply_to_message_id": message_card[11].split("|")[0]})
                        res = requests.post(f'https://api.telegram.org/bot{token_send}/sendMediaGroup', params=params, files=files)
                        id_out += str(res.json()["result"][0]["message_id"]) + "|"
                    params = {
                        "chat_id": chat_id_inc,
                        "media": meds
                    }
                    if message_card[11] != "" and f_torg == True:
                        params.update({"reply_to_message_id": message_card[11].split("|")[1]})
                    elif message_card[11] != "" and f_torg != True:
                        params.update({"reply_to_message_id": message_card[11].split("|")[0]})
                    res = requests.post(f'https://api.telegram.org/bot{token_inc}/sendMediaGroup', params=params, files=files)
                    id_out += str(res.json()["result"][0]["message_id"])
                    dbAlerts.query(f'UPDATE message SET send_id="{id_out}" WHERE id={id_main}')




if __name__ == '__main__':
    while True:
        main()
        time.sleep(1)
