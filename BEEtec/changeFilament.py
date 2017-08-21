colorHashMap =  {'021':[0.95,0.95,0.95], '022':[1,1,1], '023':[0,0,0], '024':[1,0,0], '025':[1,1,0], '026':[0,0,1], '027':[0.34,0.42,0.18], '028':[1,0,0.5], '029':[0.7,0.7,0.7], '030':[0.25,0.96,0.82], '031':[0.22,1,0.08],
                     '032':[1,0.6,0],'101':[0.95,0.95,0.95], '102':[1,1,1], '103':[0.98,0.78,0.18],'104':[1,0.66,0.01],'105':[0.730,	0.203,	0.062],'106':[0.730,	0.117,	0.062],'107':[0.585,	0.179,	0.144],
                     '108':[0.839,	0.625,  0.625],'109':[0.562,  0.199,  0.449], '110':[0.371,	0.144,	0.621],'111':[0.011,	0.484, 	0.687],'112':[0.011,	0.355,	0.546],'113':[0.011,	0.218,  0.480],'114':[0.378,	0.597,	0.230],
                     '115':[0.011,	0.542,	0.160],'116':[0.214,	0.257,	0.183], '117':[0.265,	0.183,	0.160],'118':[0.550,	0.570,	0.582],'119':[0.156,	0.156,  0.156],'120':[0.5	 ,  0.390,  0.246],'121':[0.550,	0.570,	0.582]}

filamentColorName = {'A021': 'Transparent', ' A022': 'White', 'A023': 'Black', 'A024': 'Red', 'A025': 'Yellow', 'A026': 'Blue',
     'A027': 'Olive Green', 'A028': 'Fuschia', 'A029': 'Silver', 'A030': 'Turquoise', 'A031': 'Neon Green', 'A032': 'Orange',
     'A101': 'Transparent', 'A102': 'Blanc Gris', 'A103' : 'Zinc Yellow', 'A104': 'Signal Yellow',
     'A105': 'Bright Red Orange',
     'A106': 'Traffic Red', 'A107': 'Tomato Red',
     'A108': 'Light Pink', 'A109': 'Traffic Purple',
     'A110': 'Violet', 'A111': 'Sky Blue',
     'A112': 'Traffic Blue', 'A113': 'Ultramarine Blue',
     'A114': 'Yellow Green', 'A115': 'Pure Green',
     'A116': 'Chrome Green', 'A117': 'Chocolate Brown', 'A118': 'Telegrey',
     'A119': 'Signal Black', 'A120': 'Pearl Gold',
     'A121': 'Pearl Light Grey'}

def getColor(number):
    aux = []
    if number in colorHashMap:
        aux = colorHashMap.get(number)
    else:
        aux = [1.0,1.0,1.0]
    if(len(aux) == 3):
        aux.append(1.0)
    return aux

def getColorName(text):
    if text in filamentColorName:
        return filamentColorName.get(text)
    else:
        return 'Wrong Number...'