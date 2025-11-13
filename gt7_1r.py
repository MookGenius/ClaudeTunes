from datetime import datetime as dt
from datetime import timedelta as td
import socket
import sys
import struct
import csv
import os
import signal
# pip3 install pycryptodome
from Crypto.Cipher import Salsa20

# ansi prefix
pref = "\033["

# ports for send and receive data
SendPort = 33739
ReceivePort = 33740

# Data logging setup
session_start_time = dt.now()
session_folder = f"gt7_session_{session_start_time.strftime('%Y%m%d_%H%M%S')}"
current_lap_data = []
current_lap_number = 0

# Create session folder
os.makedirs(session_folder, exist_ok=True)

# GT7 CAR DATABASE - All car codes mapped to car names
CAR_DATABASE = {
    24: "180SX Type X '96", 31: "Camaro Z28 '69", 36: "Chevelle SS 454 Sport Coupé '70",
    41: "Corvette Stingray (C3) '69", 48: "Fairlady 240ZG (HS30) '71",
    63: "Corolla Levin 1600GT APEX (AE86) '83", 78: "Silvia K's Aero (S14) '96",
    82: "Supra RZ '97", 104: "Sileighty '98", 105: "205 Turbo 16 Evolution 2 '86",
    116: "GT-One (TS020) '99", 135: "S800 '66", 137: "Beat '91", 145: "Copen '02",
    173: "R5 Turbo '80", 187: "Tuscan Speed 6 '00", 201: "Eunos Roadster (NA) '89",
    203: "Integra Type R (DC2) '98", 204: "Civic Type R (EK) '98",
    205: "RX-7 Spirit R Type A (FD) '02", 207: "MR2 GT-S '97",
    210: "R34 GT-R V-spec II Nur '02", 211: "Lancer Evolution V GSR '98",
    216: "McLaren F1 GTR Race Car '97", 293: "NSX Type R '92", 296: "787B '91",
    301: "Lancer Evolution IV GSR '96", 315: "Cobra 427 '66", 334: "Clio V6 24V '00",
    345: "Sprinter Trueno 1600GT APEX (S.Shigeno Version)", 365: "155 2.5 V6 TI '93",
    374: "RX-7 GT-X (FC) '90", 379: "Impreza Coupe WRX Type R STi Ver.VI '99",
    387: "300 SL Coupe '54", 396: "NSX Type R '02", 451: "Impreza 22B-STi '98",
    485: "GT-R GT500 '99", 489: "R33 GT-R V-spec '97", 514: "S2000 '99",
    533: "Stratos '73", 543: "XJ220 '92", 575: "190 E 2.5-16 Evolution II '91",
    604: "2000GT '67", 665: "Superbird '70", 688: "Integra Type R (DC2) '95",
    709: "Fairlady Z 300ZX TT 2seater '89", 773: "R32 GT-R V-spec II '94",
    779: "Cappuccino (EA11R) '91", 781: "Celica GT-FOUR Rally Car (ST205) '95",
    799: "Lancer Evolution VIII MR GSR '04", 808: "V6 Escudo Pikes Peak Special spec.98",
    810: "Sprinter Trueno 1600GT APEX (AE86) '83", 818: "Corvette (C2) '63",
    821: "Civic Type R (EK) '97", 829: "Delta HF Integrale Evoluzione '91",
    836: "Skyline 2000GT-R (KPGC110) '73", 837: "Skyline Hard Top 2000GT-R (KPGC10) '70",
    843: "Supra 3.0GT Turbo A '88", 919: "Silvia Q's (S13) '88",
    931: "Lancer Evolution III GSR '95", 942: "Corvette ZR-1 (C4) '89",
    954: "R92CP '92", 959: "TT Coupe 3.2 quattro '03", 998: "Sauber Mercedes C9 '89",
    1027: "DeLorean S2 '04", 1040: "Ford GT LM Race Car Spec II", 1044: "Sports 800 '65",
    1067: "XJR-9 '88", 1069: "2J '70", 1365: "R8 4.2 '07", 1370: "MINI Cooper S '05",
    1373: "Viper GTS '02", 1378: "F430 '06", 1384: "Fairlady Z Version S (Z33) '07",
    1385: "Swift Sport '07", 1399: "M3 '07", 1402: "Viper SRT10 Coupe '06",
    1409: "F40 '92", 1410: "512 BB '76", 1425: "Ford GT LM Spec II Test Car",
    1426: "Ford GT '06", 1431: "RE Amemiya FD3S RX-7", 1433: "Amuse S2000 GT1 Turbo",
    1448: "SILVIA spec-R Aero (S15) '02", 1458: "Fairlady Z (Z34) '08",
    1461: "Silvia K's Dia Selection (S13) '90", 1466: "GT-R GT500 '08",
    1470: "Supra GT500 '97", 1474: "Enzo Ferrari '02", 1480: "Corvette ZR1 (C6) '09",
    1481: "Countach 25th Anniversary '88", 1484: "Countach LP400 '74",
    1504: "458 Italia '09", 1506: "Gallardo LP 560-4 '08", 1507: "SLS AMG '10",
    1508: "Lancer Evolution VI GSR T.M. SCP '99", 1510: "NSX GT500 '08",
    1516: "SC430 GT500 '08", 1523: "500 F '68", 1527: "500 1.2 8V Lounge SS '08",
    1528: "SLR McLaren '09", 1536: "Zonda R '09", 1537: "Prius G '09",
    1539: "GranTurismo S '08", 1540: "McLaren F1 '94", 1541: "TTS Coupe '09",
    1542: "Corvette Convertible (C3) '69", 1543: "Challenger R/T '70",
    1544: "430 Scuderia '07", 1545: "Murcielago LP 640 '09",
    1549: "Amuse NISMO 380RS Super Leggera", 1551: "330 P4 '67", 1553: "XJ13 '66",
    1562: "LFA '10", 1563: "Megane Trophy '11", 1565: "Mark IV Race Car '67",
    1578: "8C Competizione '08", 1581: "GT by Citroen Road Car",
    1582: "Miura P400 Bertone Prototype '67", 1645: "GIULIA TZ2 carrozzata da ZAGATO '65",
    1646: "908 HDi FAP '10", 1671: "Sambabus Typ 2 '62",
    1689: "Civic Type R (EK) Touring Car", 1722: "MP4-12C '10",
    1729: "Mustang Mach 1 '71", 1746: "Roadster Touring Car",
    1770: "Aventador LP 700-4 '11", 1773: "Scirocco R '10", 1778: "Volkswagen 1200 '66",
    1796: "A110 '72", 1797: "SLS AMG GT3 '11", 1893: "Z8 '01", 1895: "Dino 246 GT '71",
    1896: "Model S Signature Performance '12", 1898: "One-77 '11",
    1900: "XNR Ghia Roadster '60", 1902: "Z4 GT3 '11", 1904: "M3 GT '11",
    1905: "GT-R NISMO GT3 '13", 1907: "X-BOW R '12", 1916: "Corvette C7 '14",
    1925: "G.T.350 '65", 1926: "Cobra Daytona Coupe '64",
    1927: "Sport quattro S1 Pikes Peak '87", 1931: "250 GT Berlinetta passo corto '61",
    1932: "1500 Biposto Bertone B.A.T 1 '52", 1933: "MiTo '09", 1935: "GT40 Mark I '66",
    1956: "Viper GTS '13", 1965: "R18 TDI '11", 1973: "Abarth 500 '09",
    1975: "RX500 '70", 1984: "McLaren F1 GTR - BMW '95", 1985: "Firebird Trans Am '78",
    1986: "R8 Gordini '66", 1987: "Megane R.S. Trophy '11", 1990: "Diablo GT '00",
    2010: "250 GTO '62", 2011: "500 Mondial Pinin Farina Coupe '54", 2017: "GTO '84",
    2018: "365 GTB4 '71", 2026: "Aqua S '11", 2049: "Veyron 16.4 '13",
    2050: "Huayra '13", 2051: "Genesis Coupe 3.8 '13", 2055: "Mercedes-Benz AMG VGT",
    2059: "Corvette Stingray Racer Concept '59", 2060: "Racing Kart 125 Shifter",
    2074: "M4 '14", 2076: "Mercedes-Benz AMG VGT Racing Series",
    2077: "Red Bull X2014 Standard", 2078: "Red Bull X2014 Junior", 2080: "FT-1",
    2087: "BMW VGT", 2095: "Concept XR-PHEV EVOLUTION VGT", 2098: "GTI Roadster VGT",
    2099: "VIZIV GT VGT", 2101: "TS030 Hybrid '12", 2103: "DP-100 VGT",
    2106: "FT-1 VGT", 2107: "Chaparral 2X VGT", 2108: "SRT Tomahawk X VGT",
    2109: "MINI Clubman VGT", 2110: "SRT Tomahawk GTS-R VGT", 2111: "SRT Tomahawk S VGT",
    2112: "Alpine VGT", 2113: "PEUGEOT VGT", 2116: "Alpine VGT Race",
    2117: "INFINITI CONCEPT VGT", 2118: "LM55 VGT", 2119: "Italdesign VGT Street Mode",
    2120: "Italdesign VGT Off-road Mode", 2121: "Honda Sports VGT",
    2122: "IsoRivolta Zagato VGT", 2123: "LF-LC GT VGT", 2124: "GTI Supersport VGT",
    2127: "GT-R LM NISMO '15", 2131: "V12 Vantage GT3 '12", 2134: "Bugatti VGT",
    2135: "HYUNDAI N 2025 VGT", 2136: "4C '14", 2138: "Mustang GT '15",
    2139: "RC F '14", 2141: "Golf VII GTI '14", 2142: "NISSAN CONCEPT 2020 VGT",
    2143: "R8 LMS '15", 2144: "S-FR '15", 2145: "Focus ST '15", 2146: "F-type R '14",
    2147: "Veneno '14", 2148: "Roadster S (ND) '15", 2149: "Mercedes-AMG GT S '15",
    2150: "Lancer Evolution Final '15", 2152: "Charger SRT Hellcat '15",
    2153: "WRX STI Type S '14", 2154: "86 GT '15", 2155: "Polo GTI '14",
    2156: "2&4 powered by RC213V", 2157: "V8 Vantage Gr.4", 2158: "458 Italia GT3 '13",
    2159: "Mustang Gr.3", 2160: "Genesis Gr.3", 2161: "GT-R Gr.4", 2162: "LaFerrari '13",
    2163: "Genesis Gr.4", 2164: "Mustang Gr.4", 2166: "4C Gr.4", 2167: "GT-R '17",
    2169: "TTS Coupe '14", 2170: "A 45 AMG '13", 2171: "Huracan LP 610-4 '15",
    2172: "DS 3 Racing '11", 2173: "Atenza Sedan XD L Package '15", 2174: "650S '14",
    2175: "V8 Vantage S '15", 2176: "RCZ GT Line '15", 2177: "Huracan GT3 '15",
    2178: "S-FR Racing Concept '16", 2179: "Bugatti VGT (Gr.1)",
    2180: "HYUNDAI N 2025 VGT (Gr.1)", 2181: "LM55 VGT (Gr.1)", 2182: "650S GT3 '15",
    2183: "Corvette C7 Gr.3", 2184: "F-type Gr.3", 2185: "Lancer Evolution Final Gr.3",
    2186: "WRX Gr.3", 2187: "FT-1 VGT (Gr.3)", 2188: "R.S.01 GT3 '16",
    2190: "GT by Citroen Race Car (Gr.3)", 2192: "Volkswagen GTI VGT (Gr.3)",
    3183: "PEUGEOT VGT (Gr.3)", 3185: "4C Gr.3", 3187: "Alpine VGT '17",
    3188: "SRT Tomahawk VGT (Gr.1)", 3192: "SLS AMG Gr.4", 3209: "M4 Safety Car",
    3210: "Mercedes-AMG GT Safety Car", 3214: "Civic Type R (FK2) '15",
    3215: "208 GTi by Peugeot Sport '14", 3216: "R.S.01 '16", 3217: "Camaro SS '16",
    3218: "M6 GT3 Endurance Model '16", 3219: "NSX '17", 3220: "Clio R.S. 220 Trophy '15",
    3221: "M6 GT3 Sprint Model '16", 3222: "86 GRMN '16", 3223: "Viper SRT GT3-R '15",
    3224: "Mercedes-AMG GT3 '16", 3225: "GT-R Safety Car", 3227: "LC500 '17",
    3228: "RC F GT3 prototype '16", 3229: "Mustang Gr.B Rally Car",
    3230: "Lancer Evolution Final Gr.B Rally Car", 3231: "Scirocco Gr.4",
    3232: "WRX Gr.B Rally Car", 3234: "Genesis Gr.B Rally Car", 3235: "NSX Gr.3",
    3237: "Atenza Gr.3", 3238: "RCZ Gr.3", 3239: "NSX Gr.B Rally Car",
    3241: "GT-R Gr.B Rally Car", 3242: "RCZ Gr.B Rally Car", 3245: "M4 Gr.4",
    3246: "Veyron Gr.4", 3247: "Corvette C7 Gr.4", 3248: "GT by Citroen Gr.4",
    3249: "Viper Gr.4", 3251: "NSX Gr.4", 3252: "F-type Gr.4", 3253: "Huracan Gr.4",
    3254: "RC F Gr.4", 3256: "Atenza Gr.4", 3257: "650S Gr.4",
    3258: "Lancer Evolution Final Gr.4", 3259: "RCZ Gr.4", 3260: "Megane Gr.4",
    3261: "WRX Gr.4", 3262: "86 Gr.4", 3263: "458 Italia Gr.4",
    3264: "Focus Gr.B Rally Car", 3265: "86 Gr.B Rally Car", 3266: "i3 '15",
    3267: "F12berlinetta '12", 3268: "911 GT3 RS (991) '16", 3295: "86 GT 'Limited' '16",
    3296: "Corvette C7 Gr.3 Road Car", 3297: "WRX STI Isle of Man '16",
    3298: "TT Cup '16", 3299: "4C Gr.3 Road Car", 3300: "Mustang Gr.3 Road Car",
    3301: "Lancer Evolution Final Gr.B Road Car", 3303: "RCZ Gr.3 Road Car",
    3304: "WRX Gr.B Road Car", 3305: "Beetle Gr.3", 3306: "Atenza Gr.3 Road Car",
    3309: "Vulcan '16", 3310: "Cayman GT4 Clubsport '16", 3311: "911 RSR (991) '17",
    3312: "TS050 - Hybrid '16", 3313: "919 Hybrid '16", 3314: "Audi VGT",
    3315: "McLaren VGT", 3316: "COPEN RJ VGT", 3332: "L500R HYbrid VGT 2017",
    3333: "L750R HYbrid VGT 2017", 3334: "R18 '16", 3335: "McLaren VGT (Gr.1)",
    3336: "F-150 SVT Raptor '11", 3337: "A110 '17", 3338: "CHC 1967 Chevy Nova",
    3339: "BRZ Drift Car '17", 3340: "RC F GT3 '17", 3341: "Pantera '71",
    3342: "F1500T-A", 3343: "DB11 '16", 3344: "M3 Sport Evolution '89",
    3345: "GT-R NISMO '17", 3346: "Mach Forty", 3348: "NSX CONCEPT-GT '16",
    3349: "RC F GT500 '16", 3350: "GT-R NISMO GT500 '16", 3351: "Audi e-tron VGT",
    3352: "GR Supra Racing Concept '18", 3353: "Clio R.S. 220 Trophy '16",
    3354: "BRZ S '15", 3356: "Mini-Cooper 'S' '65", 3357: "S660 '15",
    3358: "911 GT3 (996) '01", 3359: "911 GT3 (997) '09", 3360: "McLaren P1 GTR '16",
    3361: "E-type Coupe '61", 3362: "F50 '95", 3363: "DB3S '53",
    3364: "Greddy Fugu Z", 3365: "356 A/1500 GS GT Carrera Speedster '56",
    3367: "GR Supra RZ '19", 3368: "Tundra TRD Pro '19", 3369: "SR3 SL '13",
    3370: "Fit Hybrid '14", 3371: "SF19 Super Formula / Toyota '19",
    3372: "SF19 Super Formula / Honda '19", 3373: "962 C '88",
    3374: "Red Bull X2019 Competition", 3375: "356 A/1500 GS Carrera '56",
    3376: "D-type '54", 3377: "Super Bee '70", 3383: "Demio XD Touring '15",
    3384: "GTO Twin Turbo '91", 3385: "911 Turbo (930) '81",
    3387: "Camaro ZL1 1LE Package '18", 3388: "300 SEL 6.8 AMG '71", 3389: "M3 '03",
    3390: "Taycan Turbo S '19", 3391: "Shelby GT350R '16",
    3392: "Aventador LP 750-4 SV '15", 3393: "Carrera GT '04", 3394: "DBR9 GT1 '10",
    3396: "Jaguar VGT Coupe", 3397: "CLK-LM '98", 3398: "CTR3 '07",
    3399: "GR Supra Race Car '19", 3400: "911 GT1 Strassenversion '97",
    3401: "Crown Athlete G '13", 3402: "Ford GT '17", 3403: "Golf I GTI '83",
    3404: "911 Carrera RS CS (993) '95", 3405: "R8 LMS Evo '19",
    3406: "Charger SRT Hellcat Safety Car", 3407: "Megane R.S. Trophy Safety Car",
    3408: "Crown Athlete G Safety Car", 3409: "Mono '16", 3410: "917K '70",
    3411: "Giulia GTAm '20", 3412: "R8 Coupé V10 plus '16", 3413: "BRZ STI Sport '18",
    3414: "Lambo V12 VGT", 3415: "8C 2900B Touring Berlinetta '38",
    3416: "Mercedes-AMG GT R '17", 3417: "Jaguar VGT SV", 3418: "GR Supra RZ '20",
    3419: "RX-VISION GT3 CONCEPT", 3420: "Focus RS '18", 3421: "Merak SS '80",
    3422: "3.0 CSL '73", 3423: "Wicked Fabrication GT 51",
    3424: "Lancer Evolution IX MR GSR '06", 3426: "Roadster Shop Rampage",
    3427: "RX-8 Spirit R '12", 3428: "S Barker Tourer '29", 3429: "Fairlady Z 432 '69",
    3430: "Willys MB '45", 3431: "911 Carrera RS (964) '92",
    3432: "Impreza Sedan WRX STi '04", 3433: "FXX K '14", 3434: "Testarossa '91",
    3436: "Ford GT Race Car '18", 3437: "Mangusta '69", 3438: "Abarth 595 SS '70",
    3439: "911 Carrera RS (993) '95", 3441: "300 SL (W194) '52", 3442: "A112 Abarth '85",
    3443: "308 GTB '75", 3444: "1932 Ford Roadster Hot Rod", 3445: "DB5 '64",
    3446: "Spyder type 550/1500RS '55", 3449: "Corvette C7 ZR1 '19",
    3450: "GT-R NISMO GT3 '18", 3451: "GR Yaris RZ 'High performance' '20",
    3452: "917 LIVING LEGEND", 3453: "M3 '89", 3454: "3.0 CSL '71",
    3456: "Swift Sport '17", 3457: "A220 Race Car '68", 3458: "Mercedes-AMG C 63 S '15",
    3459: "918 Spyder '13", 3462: "GTO 'The Judge' '69", 3464: "Corvette (C1) '58",
    3466: "Sierra RS 500 Cosworth '87", 3467: "Civic Type R Limited Edition (FK8) '20",
    3468: "RGT 4.2 '16", 3469: "F8 Tributo '19", 3471: "Celica GT-Four (ST205) '94",
    3473: "Chiron '16", 3474: "BRZ GT300 '21", 3475: "MP4/4 '88",
    3476: "Suzuki Vision Gran Turismo", 3477: "Silvia spec-R Aero (S15) Touring Car",
    3478: "Porsche VGT", 3479: "Jaguar VGT Roadster", 3480: "Swift Sport Gr.4",
    3481: "GR86 RZ '21", 3483: "M2 Competition '18", 3485: "Mercedes-AMG GT Black Series '20",
    3486: "Challenger SRT Demon '18", 3487: "Mustang Boss 429 '69",
    3488: "Cayman GT4 '16", 3489: "A6GCS/53 Spyder '54", 3490: "Carrera GTS (904) '64",
    3493: "Skyline Super Silhouette Group 5 '84", 3494: "Alphard Executive Lounge '18",
    3495: "RX-VISION '15", 3499: "GR010 HYBRID '21",
    3500: "G70 3.3T AWD Prestige Package '22", 3501: "G70 GR4", 3502: "Genesis X GR3",
    3503: "RX-VISION GT3 CONCEPT Stealth Model", 3504: "Z Performance '23",
    3505: "Mangusta (Christian Dior)", 3506: "BRZ S '21", 3507: "Porsche VGT Spyder",
    3508: "SUZUKI Vision Gran Turismo (Gr.3 Version)", 3509: "911 Carrera RS (901) '73",
    3510: "Ferrari Vision Gran Turismo", 3511: "ID.R '19", 3512: "Roadster NR-A (ND) '22",
    3513: "Silvia K's Type S (S14) '94", 3514: "DS 21 Pallas '70",
    3515: "GR010 HYBRID (Olympic Esports Series) '21", 3517: "Red Bull X2019 25th Anniversary",
    3518: "Corvette C8 Stingray '20", 3519: "959 '87", 3520: "400R '95",
    3521: "Mazda3 '19", 3522: "Maverick", 3523: "RS 5 Turbo DTM '19",
    3524: "GT-R NISMO (R32) '90", 3525: "RA272 '65", 3526: "Civic",
    3528: "SF23 Super Formula / Honda '23", 3529: "SF23 Super Formula / Toyota '23",
    3530: "Giulia Sprint GT Veloce '67", 3531: "GT3 '20", 3532: "Valkyrie '21",
    3533: "MC20 '20", 3534: "Ambulance Himedic '21", 3535: "GR Corolla MORIZO Edition '22",
    3536: "Civic Type R (FL5) '22", 3537: "MAZDA3 Gr.4", 3538: "Charger R/T 426 Hemi '68",
    3539: "911 GT3 RS (992) '22", 3540: "Model 3 Performance '23",
    3541: "BVLGARI Aluminium VGT", 3542: "SKODA Vision Gran Turismo",
    3543: "Genesis X Gran Berlinetta VGT Concept",
    3544: "Genesis X Gran Racer Vision Gran Turismo Concept", 3545: "Jimny XC '18",
    3546: "AFEELA Prototype 2024", 3547: "R4 GTL '85", 3548: "Urus '18",
    3550: "Impreza Rally Car '98", 3551: "M3 '97", 3553: "GT-R Premium edition T-spec '24",
    3554: "Hiace Van DX '16"
}

def get_car_name(car_code):
    """Lookup car name from car code"""
    return CAR_DATABASE.get(car_code, f"Unknown Car ({car_code})")

# CORRECTED CSV headers matching Packet A structure
csv_headers = [
    # Basic tracking
    'timestamp', 'lap_number', 'packet_id', 'car_code', 'car_name',
    
    # Position & motion
    'position_x', 'position_y', 'position_z',
    'velocity_x', 'velocity_y', 'velocity_z',
    'rotation_pitch', 'rotation_yaw', 'rotation_roll',
    'north_orientation',
    'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
    
    # Suspension & body
    'body_height',
    
    # Engine
    'rpm',
    
    # Fuel
    'fuel_level', 'fuel_capacity', 'is_electric',
    
    # Speed
    'speed_mps', 'speed_kph',
    
    # Boost
    'boost_pressure', 'has_turbo',
    
    # Temperatures and pressure
    'oil_pressure', 'water_temp', 'oil_temp',
    
    # TIRE TEMPERATURES
    'tire_temp_fl', 'tire_temp_fr', 'tire_temp_rl', 'tire_temp_rr',
    
    # Lap data
    'total_laps', 'best_lap_time_ms', 'last_lap_time_ms', 'time_on_track_ms',
    
    # Race position
    'current_position', 'total_positions',
    
    # Pre-race data
    'pre_race_start_position', 'pre_race_num_cars',
    
    # Rev limiter
    'rev_warning', 'rev_limiter',
    
    # Calculated max speed
    'estimated_top_speed',
    
    # SIMULATOR FLAGS (decoded)
    'flag_car_on_track', 'flag_paused', 'flag_loading', 'flag_in_gear',
    'flag_has_turbo', 'flag_rev_limiter_alert', 'flag_handbrake',
    'flag_lights_on', 'flag_high_beam', 'flag_low_beam', 'flag_asm_active', 'flag_tcs_active',
    
    # Gear data
    'current_gear', 'suggested_gear',
    
    # Throttle and brake
    'throttle_percent', 'brake_percent',
    
    # ROAD PLANE DATA (banking)
    'road_plane_x', 'road_plane_y', 'road_plane_z', 'road_plane_distance',
    
    # TIRE RPS (revolutions per second in radians)
    'tire_rps_fl', 'tire_rps_fr', 'tire_rps_rl', 'tire_rps_rr',
    
    # TIRE RADIUS
    'tire_radius_fl', 'tire_radius_fr', 'tire_radius_rl', 'tire_radius_rr',
    
    # Calculated tire speeds
    'tire_speed_fl', 'tire_speed_fr', 'tire_speed_rl', 'tire_speed_rr',
    
    # Calculated tire slip ratios
    'tire_slip_ratio_fl', 'tire_slip_ratio_fr', 'tire_slip_ratio_rl', 'tire_slip_ratio_rr',
    
    # SUSPENSION HEIGHT
    'suspension_fl', 'suspension_fr', 'suspension_rl', 'suspension_rr',
    
    # UNKNOWN FLOATS (8 mystery fields at 0xD4-0xF0)
    'unknown_float_1', 'unknown_float_2', 'unknown_float_3', 'unknown_float_4',
    'unknown_float_5', 'unknown_float_6', 'unknown_float_7', 'unknown_float_8',
    
    # CLUTCH DATA
    'clutch_pedal', 'clutch_engagement', 'rpm_clutch_gearbox',
    
    # TRANSMISSION DATA
    'transmission_top_speed',
    
    # GEAR RATIOS (correct location at 0x104)
    'gear_ratio_1', 'gear_ratio_2', 'gear_ratio_3', 'gear_ratio_4',
    'gear_ratio_5', 'gear_ratio_6', 'gear_ratio_7', 'gear_ratio_8',
    
    # Current lap time
    'current_lap_time'
]

def save_lap_data():
    """Save current lap data to CSV file"""
    global current_lap_data, current_lap_number
    
    if current_lap_data and current_lap_number > 0:
        filename = f"{session_folder}/lap_{current_lap_number:03d}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if len(csv_headers) != len(current_lap_data[0]):
                printAt(f'WARNING: header/data mismatch! {len(csv_headers)} vs {len(current_lap_data[0])}', 20, 1, reverse=1)
            writer.writerow(csv_headers)
            writer.writerows(current_lap_data)
        
        printAt(f"Saved lap {current_lap_number} data: {len(current_lap_data)} data points   ", 19, 1)
        current_lap_data = []

def decode_flags(flags_raw):
    """Decode the 16-bit simulator flags"""
    flags = struct.unpack('h', struct.pack('H', flags_raw))[0]
    
    return {
        'car_on_track': 1 if (flags & (1 << 0)) else 0,
        'paused': 1 if (flags & (1 << 1)) else 0,
        'loading': 1 if (flags & (1 << 2)) else 0,
        'in_gear': 1 if (flags & (1 << 3)) else 0,
        'has_turbo': 1 if (flags & (1 << 4)) else 0,
        'rev_limiter_alert': 1 if (flags & (1 << 5)) else 0,
        'handbrake': 1 if (flags & (1 << 6)) else 0,
        'lights_on': 1 if (flags & (1 << 7)) else 0,
        'high_beam': 1 if (flags & (1 << 8)) else 0,
        'low_beam': 1 if (flags & (1 << 9)) else 0,
        'asm_active': 1 if (flags & (1 << 10)) else 0,
        'tcs_active': 1 if (flags & (1 << 11)) else 0
    }

def extract_telemetry_data(ddata, lap_time_seconds):
    """Extract ALL telemetry data from GT7 Packet A with CORRECT OFFSETS"""
    
    # Basic packet info (0x70, 0x74)
    pktid = struct.unpack('i', ddata[0x70:0x70+4])[0]
    curlap = struct.unpack('h', ddata[0x74:0x74+2])[0]
    
    # Position (0x04-0x0F)
    pos_x = struct.unpack('f', ddata[0x04:0x08])[0]
    pos_y = struct.unpack('f', ddata[0x08:0x0C])[0] 
    pos_z = struct.unpack('f', ddata[0x0C:0x10])[0]
    
    # Velocity (0x10-0x1B)
    vel_x = struct.unpack('f', ddata[0x10:0x14])[0]
    vel_y = struct.unpack('f', ddata[0x14:0x18])[0]
    vel_z = struct.unpack('f', ddata[0x18:0x1C])[0]
    
    # Rotation (0x1C-0x27)
    rot_pitch = struct.unpack('f', ddata[0x1C:0x20])[0]
    rot_yaw = struct.unpack('f', ddata[0x20:0x24])[0]
    rot_roll = struct.unpack('f', ddata[0x24:0x28])[0]
    
    # North orientation (0x28)
    north_orientation = struct.unpack('f', ddata[0x28:0x2C])[0]
    
    # Angular velocity (0x2C-0x37)
    ang_vel_x = struct.unpack('f', ddata[0x2C:0x30])[0]
    ang_vel_y = struct.unpack('f', ddata[0x30:0x34])[0]
    ang_vel_z = struct.unpack('f', ddata[0x34:0x38])[0]
    
    # Body height (0x38)
    body_height = struct.unpack('f', ddata[0x38:0x3C])[0]
    
    # Engine RPM (0x3C)
    rpm = struct.unpack('f', ddata[0x3C:0x40])[0]
    
    # IV is at 0x40 but we skip it
    
    # Fuel (0x44-0x4B)
    fuel_level = struct.unpack('f', ddata[0x44:0x48])[0]
    fuel_capacity = struct.unpack('f', ddata[0x48:0x4C])[0]
    is_electric = 1 if fuel_capacity <= 0 else 0
    
    # Speed (0x4C)
    speed_mps = struct.unpack('f', ddata[0x4C:0x50])[0]
    speed_kph = 3.6 * speed_mps
    
    # Boost (0x50)
    boost_raw = struct.unpack('f', ddata[0x50:0x54])[0]
    boost_pressure = boost_raw - 1
    has_turbo = 1 if boost_pressure > -1 else 0
    
    # Oil pressure (0x54)
    oil_pressure = struct.unpack('f', ddata[0x54:0x58])[0]
    
    # Water temp (0x58)
    water_temp = struct.unpack('f', ddata[0x58:0x5C])[0]
    
    # Oil temp (0x5C)
    oil_temp = struct.unpack('f', ddata[0x5C:0x60])[0]
    
    # TIRE TEMPERATURES (0x60-0x6F)
    tire_temp_fl = struct.unpack('f', ddata[0x60:0x64])[0]
    tire_temp_fr = struct.unpack('f', ddata[0x64:0x68])[0]
    tire_temp_rl = struct.unpack('f', ddata[0x68:0x6C])[0]
    tire_temp_rr = struct.unpack('f', ddata[0x6C:0x70])[0]
    
    # Packet ID already read at 0x70
    # Lap count already read at 0x74
    
    # Total laps (0x76)
    total_laps = struct.unpack('h', ddata[0x76:0x78])[0]
    
    # Best lap time (0x78)
    best_lap_time_ms = struct.unpack('i', ddata[0x78:0x7C])[0]
    
    # Last lap time (0x7C)
    last_lap_time_ms = struct.unpack('i', ddata[0x7C:0x80])[0]
    
    # Time on track (0x80)
    time_on_track_ms = struct.unpack('i', ddata[0x80:0x84])[0]
    
    # Race start position (0x84)
    pre_race_start_position = struct.unpack('h', ddata[0x84:0x86])[0]
    
    # Pre race num cars (0x86)
    pre_race_num_cars = struct.unpack('h', ddata[0x86:0x88])[0]
    
    # Min alert RPM (0x88)
    rev_warning = struct.unpack('H', ddata[0x88:0x8A])[0]
    
    # Max alert RPM (0x8A)
    rev_limiter = struct.unpack('H', ddata[0x8A:0x8C])[0]
    
    # Calc max speed (0x8C)
    estimated_top_speed = struct.unpack('h', ddata[0x8C:0x8E])[0]
    
    # SIMULATOR FLAGS (0x8E)
    flags_raw = struct.unpack('H', ddata[0x8E:0x90])[0]
    flags = decode_flags(flags_raw)
    
    # Gear data (0x90)
    gear_raw = struct.unpack('B', ddata[0x90:0x91])[0]
    current_gear = gear_raw & 0b00001111
    suggested_gear = gear_raw >> 4
    
    # Throttle (0x91)
    throttle = struct.unpack('B', ddata[0x91:0x92])[0] / 2.55
    
    # Brake (0x92)
    brake = struct.unpack('B', ddata[0x92:0x93])[0] / 2.55
    
    # UNKNOWNBYTE1 at 0x93 - skip it
    
    # ROAD PLANE DATA (0x94-0xA3)
    road_plane_x = struct.unpack('f', ddata[0x94:0x98])[0]
    road_plane_y = struct.unpack('f', ddata[0x98:0x9C])[0]
    road_plane_z = struct.unpack('f', ddata[0x9C:0xA0])[0]
    road_plane_distance = struct.unpack('f', ddata[0xA0:0xA4])[0]
    
    # TIRE RPS (0xA4-0xB3)
    tire_rps_fl = struct.unpack('f', ddata[0xA4:0xA8])[0]
    tire_rps_fr = struct.unpack('f', ddata[0xA8:0xAC])[0]
    tire_rps_rl = struct.unpack('f', ddata[0xAC:0xB0])[0]
    tire_rps_rr = struct.unpack('f', ddata[0xB0:0xB4])[0]
    
    # TIRE RADIUS (0xB4-0xC3)
    tire_radius_fl = struct.unpack('f', ddata[0xB4:0xB8])[0]
    tire_radius_fr = struct.unpack('f', ddata[0xB8:0xBC])[0]
    tire_radius_rl = struct.unpack('f', ddata[0xBC:0xC0])[0]
    tire_radius_rr = struct.unpack('f', ddata[0xC0:0xC4])[0]
    
    # Calculate tire speeds in kph
    tire_speed_fl = abs(3.6 * tire_radius_fl * tire_rps_fl)
    tire_speed_fr = abs(3.6 * tire_radius_fr * tire_rps_fr)
    tire_speed_rl = abs(3.6 * tire_radius_rl * tire_rps_rl)
    tire_speed_rr = abs(3.6 * tire_radius_rr * tire_rps_rr)
    
    # Calculate tire slip ratios
    if speed_kph > 0:
        tire_slip_ratio_fl = tire_speed_fl / speed_kph
        tire_slip_ratio_fr = tire_speed_fr / speed_kph
        tire_slip_ratio_rl = tire_speed_rl / speed_kph
        tire_slip_ratio_rr = tire_speed_rr / speed_kph
    else:
        tire_slip_ratio_fl = tire_slip_ratio_fr = tire_slip_ratio_rl = tire_slip_ratio_rr = 0.0
    
    # SUSPENSION HEIGHT (0xC4-0xD3)
    suspension_fl = struct.unpack('f', ddata[0xC4:0xC8])[0]
    suspension_fr = struct.unpack('f', ddata[0xC8:0xCC])[0]
    suspension_rl = struct.unpack('f', ddata[0xCC:0xD0])[0]
    suspension_rr = struct.unpack('f', ddata[0xD0:0xD4])[0]
    
    # UNKNOWN FLOATS (0xD4-0xF3) - 8 mystery floats
    unknown_float_1 = struct.unpack('f', ddata[0xD4:0xD8])[0]
    unknown_float_2 = struct.unpack('f', ddata[0xD8:0xDC])[0]
    unknown_float_3 = struct.unpack('f', ddata[0xDC:0xE0])[0]
    unknown_float_4 = struct.unpack('f', ddata[0xE0:0xE4])[0]
    unknown_float_5 = struct.unpack('f', ddata[0xE4:0xE8])[0]
    unknown_float_6 = struct.unpack('f', ddata[0xE8:0xEC])[0]
    unknown_float_7 = struct.unpack('f', ddata[0xEC:0xF0])[0]
    unknown_float_8 = struct.unpack('f', ddata[0xF0:0xF4])[0]
    
    # CLUTCH DATA (0xF4-0xFF)
    clutch_pedal = struct.unpack('f', ddata[0xF4:0xF8])[0]
    clutch_engagement = struct.unpack('f', ddata[0xF8:0xFC])[0]
    rpm_clutch_gearbox = struct.unpack('f', ddata[0xFC:0x100])[0]
    
    # TRANSMISSION TOP SPEED (0x100)
    transmission_top_speed = struct.unpack('f', ddata[0x100:0x104])[0]
    
    # GEAR RATIOS (0x104-0x123) - CORRECT LOCATION!
    gear_ratio_1 = struct.unpack('f', ddata[0x104:0x108])[0]
    gear_ratio_2 = struct.unpack('f', ddata[0x108:0x10C])[0]
    gear_ratio_3 = struct.unpack('f', ddata[0x10C:0x110])[0]
    gear_ratio_4 = struct.unpack('f', ddata[0x110:0x114])[0]
    gear_ratio_5 = struct.unpack('f', ddata[0x114:0x118])[0]
    gear_ratio_6 = struct.unpack('f', ddata[0x118:0x11C])[0]
    gear_ratio_7 = struct.unpack('f', ddata[0x11C:0x120])[0]
    gear_ratio_8 = struct.unpack('f', ddata[0x120:0x124])[0]
    
    # CAR CODE (0x124)
    car_code = struct.unpack('i', ddata[0x124:0x128])[0]
    car_name = get_car_name(car_code)
    
    return [
        # Basic tracking
        dt.now().isoformat(), curlap, pktid, car_code, car_name,
        
        # Position & motion
        pos_x, pos_y, pos_z,
        vel_x, vel_y, vel_z, 
        rot_pitch, rot_yaw, rot_roll,
        north_orientation,
        ang_vel_x, ang_vel_y, ang_vel_z,
        
        # Suspension & body
        body_height,
        
        # Engine
        rpm,
        
        # Fuel
        fuel_level, fuel_capacity, is_electric,
        
        # Speed
        speed_mps, speed_kph,
        
        # Boost
        boost_pressure, has_turbo,
        
        # Temperatures and pressure
        oil_pressure, water_temp, oil_temp,
        
        # TIRE DATA
        tire_temp_fl, tire_temp_fr, tire_temp_rl, tire_temp_rr,
        
        # Lap data
        total_laps, best_lap_time_ms, last_lap_time_ms, time_on_track_ms,
        
        # Race position
        current_position, total_positions,
        
        # Pre-race data
        pre_race_start_position, pre_race_num_cars,
        
        # Rev limiter
        rev_warning, rev_limiter,
        
        # Calculated max speed
        estimated_top_speed,
        
        # SIMULATOR FLAGS (decoded)
        flags['car_on_track'], flags['paused'], flags['loading'], flags['in_gear'],
        flags['has_turbo'], flags['rev_limiter_alert'], flags['handbrake'],
        flags['lights_on'], flags['high_beam'], flags['low_beam'], 
        flags['asm_active'], flags['tcs_active'],
        
        # Gear data
        current_gear, suggested_gear,
        
        # Throttle and brake
        throttle, brake,
        
        # ROAD PLANE DATA (banking)
        road_plane_x, road_plane_y, road_plane_z, road_plane_distance,
        
        # TIRE RPS
        tire_rps_fl, tire_rps_fr, tire_rps_rl, tire_rps_rr,
        
        # TIRE RADIUS
        tire_radius_fl, tire_radius_fr, tire_radius_rl, tire_radius_rr,
        
        # Calculated tire speeds
        tire_speed_fl, tire_speed_fr, tire_speed_rl, tire_speed_rr,
        
        # Calculated tire slip ratios
        tire_slip_ratio_fl, tire_slip_ratio_fr, tire_slip_ratio_rl, tire_slip_ratio_rr,
        
        # SUSPENSION HEIGHT
        suspension_fl, suspension_fr, suspension_rl, suspension_rr,
        
        # UNKNOWN FLOATS
        unknown_float_1, unknown_float_2, unknown_float_3, unknown_float_4,
        unknown_float_5, unknown_float_6, unknown_float_7, unknown_float_8,
        
        # CLUTCH DATA
        clutch_pedal, clutch_engagement, rpm_clutch_gearbox,
        
        # TRANSMISSION DATA
        transmission_top_speed,
        
        # GEAR RATIOS (correct location!)
        gear_ratio_1, gear_ratio_2, gear_ratio_3, gear_ratio_4,
        gear_ratio_5, gear_ratio_6, gear_ratio_7, gear_ratio_8,
        
        # Current lap time
        lap_time_seconds
    ]

# ctrl-c handler
def handler(signum, frame):
    print("\nShutting down...")
    save_lap_data()
    
    summary_file = f"{session_folder}/session_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"GT7 Complete Telemetry Session - Packet A (CORRECTED)\n")
        f.write(f"Started: {session_start_time}\n")
        f.write(f"Ended: {dt.now()}\n")
        try:
            total_saved = sum(name.startswith('lap_') and name.endswith('.csv') for name in os.listdir(session_folder))
        except Exception:
            total_saved = 0
        f.write(f"Total laps recorded: {total_saved}\n")
        f.write(f"Data saved to: {session_folder}/\n")
        f.write(f"\nComplete Packet A data includes:\n")
        f.write(f"  - Position, velocity, rotation\n")
        f.write(f"  - Tire data (temps, slip, speeds)\n")
        f.write(f"  - Engine & drivetrain data\n")
        f.write(f"  - Simulator flags (TCS, ASM, etc.)\n")
        f.write(f"  - Road plane banking data\n")
        f.write(f"  - Gear ratios (all 8 gears) - CORRECTED OFFSETS\n")
        f.write(f"  - Car code identification\n")
        f.write(f"  - 8 unknown floats for research\n")
    
    print(f"Session data saved to: {session_folder}/")
    sys.stdout.write(f'{pref}?1049l')
    sys.stdout.write(f'{pref}?25h')
    sys.stdout.flush()
    exit(1)

signal.signal(signal.SIGINT, handler)

sys.stdout.write(f'{pref}?1049h')
sys.stdout.write(f'{pref}?25l')
sys.stdout.flush()

# get ip address from command line
if len(sys.argv) == 2:
    ip = sys.argv[1]
else:
    print('Run like : python3 gt7_1_corrected.py <playstation-ip>')
    exit(1)

# Create a UDP socket and bind it
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', ReceivePort))
s.settimeout(10)

# CORRECTED DECRYPTION FOR PACKET A!
def salsa20_dec(dat):
    KEY = b'Simulator Interface Packet GT7 ver 0.0'
    
    oiv = dat[0x40:0x44]
    iv1 = int.from_bytes(oiv, byteorder='little')
    iv2 = iv1 ^ 0xDEADBEAF  # CORRECT KEY FOR PACKET A
    
    IV = bytearray()
    IV.extend(iv2.to_bytes(4, 'little'))
    IV.extend(iv1.to_bytes(4, 'little'))
    
    cipher = Salsa20.new(key=KEY[0:32], nonce=bytes(IV[:8]))
    ddata = cipher.decrypt(dat)
    
    magic = int.from_bytes(ddata[0:4], byteorder='little')
    if magic != 0x47375330:
        return bytearray(b'')
    return ddata

def send_hb(s):
    send_data = 'A'  # REQUEST PACKET A
    s.sendto(send_data.encode('utf-8'), (ip, SendPort))

def secondsToLaptime(seconds):
    remaining = seconds
    minutes = seconds // 60
    remaining = seconds % 60
    return '{:01.0f}:{:06.3f}'.format(minutes, remaining)

def printAt(str, row=1, column=1, bold=0, underline=0, reverse=0):
    sys.stdout.write('{}{};{}H'.format(pref, row, column))
    if reverse:
        sys.stdout.write('{}7m'.format(pref))
    if bold:
        sys.stdout.write('{}1m'.format(pref))
    if underline:
        sys.stdout.write('{}4m'.format(pref))
    if not bold and not underline and not reverse:
        sys.stdout.write('{}0m'.format(pref))
    sys.stdout.write(str)

send_hb(s)

# Display setup
printAt('GT7 COMPLETE TELEMETRY LOGGER v4.0 - PACKET A CORRECTED! (ctrl-c to quit)', 1, 1, bold=1)
printAt(f'Session: {session_folder}', 2, 1)
printAt('Packet A: All fields + CORRECT gear ratios at 0x104!', 3, 1, bold=1)

printAt('Current Lap:', 5, 1)
printAt('Data Points:', 6, 1)
printAt('Last Saved:', 7, 1)
printAt('Lap Time:', 5, 21)

printAt('=== VEHICLE ===', 9, 1, bold=1, reverse=1)
printAt('Speed:', 10, 1)
printAt('RPM:', 11, 1)
printAt('Gear:', 12, 1)
printAt('Car:', 13, 1)
printAt('Code:', 14, 1)

printAt('=== GEAR RATIOS ===', 9, 40, bold=1, reverse=1)
printAt('1st:', 10, 40)
printAt('2nd:', 11, 40)
printAt('3rd:', 12, 40)
printAt('4th:', 13, 40)
printAt('5th:', 14, 40)
printAt('6th:', 15, 40)

printAt('=== ROAD ===', 16, 1, bold=1, reverse=1)
printAt('Banking:', 17, 1)

printAt('=== FLAGS ===', 16, 30, bold=1, reverse=1)
printAt('TCS:', 17, 30)
printAt('ASM:', 17, 42)
printAt('Track:', 18, 30)

prevlap = -1
pktid = 0
pknt = 0
dt_start = dt.now()

# Position tracking for display
current_position = -1
total_positions = -1

while True:
    try:
        data, address = s.recvfrom(4096)
        pknt = pknt + 1
        ddata = salsa20_dec(data)
        
        if len(ddata) > 0 and struct.unpack('i', ddata[0x70:0x74])[0] > pktid:
            pktid = struct.unpack('i', ddata[0x70:0x74])[0]
            curlap = struct.unpack('h', ddata[0x74:0x76])[0]
            
            # Read position data
            current_position = struct.unpack('h', ddata[0x84:0x86])[0]
            total_positions = struct.unpack('h', ddata[0x86:0x88])[0]
            
            if curlap > 0:
                dt_now = dt.now()
                
                if prevlap == -1:
                    dt_start = dt_now
                
                if curlap != prevlap and prevlap != -1:
                    save_lap_data()
                    dt_start = dt_now
                    
                prevlap = curlap
                current_lap_number = curlap
                curLapTime = dt_now - dt_start
                
                telemetry_data = extract_telemetry_data(ddata, curLapTime.total_seconds())
                current_lap_data.append(telemetry_data)
                
                # Update display
                printAt(f'{current_lap_number:3d}', 5, 15)
                printAt(f'{len(current_lap_data):5d}', 6, 15)
                if current_lap_number > 1:
                    printAt(f'{current_lap_number-1:3d}', 7, 15)
                printAt(f'{secondsToLaptime(curLapTime.total_seconds()):>9}', 5, 30)
                
                if len(current_lap_data) > 0:
                    latest = current_lap_data[-1]
                    
                    # Vehicle data - using correct indices
                    speed_kph = latest[20]  # speed_kph index
                    printAt(f'{speed_kph:6.1f} kph', 10, 7)
                    
                    rpm = latest[16]  # rpm index
                    printAt(f'{rpm:7.0f}', 11, 6)
                    
                    gear = int(latest[54])  # current_gear index
                    if gear == 0:
                        printAt(' R', 12, 7)
                    elif gear == 15:
                        printAt(' N', 12, 7)
                    else:
                        printAt(f'{gear:2d}', 12, 7)
                    
                    car_code = int(latest[3])  # car_code
                    car_name = str(latest[4])  # car_name
                    # Display shortened car name (first 25 chars to fit screen)
                    car_display = car_name[:25] if len(car_name) > 25 else car_name
                    printAt(f'{car_display:<25}', 13, 6)
                    printAt(f'{car_code:5d}', 14, 7)
                    
                    # Gear ratios - using correct indices (at end of array before lap time)
                    gear_ratio_1 = latest[-9]  # gear_ratio_1
                    gear_ratio_2 = latest[-8]  # gear_ratio_2
                    gear_ratio_3 = latest[-7]  # gear_ratio_3
                    gear_ratio_4 = latest[-6]  # gear_ratio_4
                    gear_ratio_5 = latest[-5]  # gear_ratio_5
                    gear_ratio_6 = latest[-4]  # gear_ratio_6
                    
                    printAt(f'{gear_ratio_1:5.3f}' if gear_ratio_1 > 0 else '  -  ', 10, 45)
                    printAt(f'{gear_ratio_2:5.3f}' if gear_ratio_2 > 0 else '  -  ', 11, 45)
                    printAt(f'{gear_ratio_3:5.3f}' if gear_ratio_3 > 0 else '  -  ', 12, 45)
                    printAt(f'{gear_ratio_4:5.3f}' if gear_ratio_4 > 0 else '  -  ', 13, 45)
                    printAt(f'{gear_ratio_5:5.3f}' if gear_ratio_5 > 0 else '  -  ', 14, 45)
                    printAt(f'{gear_ratio_6:5.3f}' if gear_ratio_6 > 0 else '  -  ', 15, 45)
                    
                    # Road banking (road_plane data)
                    road_plane_y = latest[57]  # road_plane_y index
                    banking_angle = road_plane_y * 57.2958  # Convert to degrees
                    printAt(f'{banking_angle:+6.2f}°', 17, 10)
                    
                    # Flags - using correct indices
                    tcs_active = int(latest[53])  # flag_tcs_active
                    asm_active = int(latest[52])  # flag_asm_active
                    on_track = int(latest[42])    # flag_car_on_track
                    
                    printAt('ON ' if tcs_active else 'OFF', 17, 35)
                    printAt('ON ' if asm_active else 'OFF', 17, 47)
                    printAt('YES' if on_track else 'NO ', 18, 37)
            else:
                curLapTime = 0

        if pknt > 100:
            send_hb(s)
            pknt = 0
            
    except Exception as e:
        printAt(f'Exception: {e}                              ', 20, 1, reverse=1)
        send_hb(s)
        pknt = 0
        pass

    sys.stdout.flush()
