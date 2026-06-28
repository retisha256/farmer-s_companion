"""
Translation service for USSD menus.

Strategy (priority order):
  1. Django cache (24h TTL)
  2. Built-in TRANSLATIONS dictionary  ← fast, zero API cost
  3. OpenAI gpt-3.5-turbo              ← dynamic fallback
  4. English original                  ← always safe

Supported languages: en, sw (Kiswahili), lg (Luganda),
                     rn (Runyankole), ac (Acholi)
"""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Supported languages                                                  #
# ------------------------------------------------------------------ #

SUPPORTED_LANGUAGES: dict[str, str] = {
    'en': 'English',
    'sw': 'Kiswahili',
    'lg': 'Luganda',
    'rn': 'Runyankole',
    'ac': 'Acholi',
}

DEFAULT_LANGUAGE = 'en'
_CACHE_TTL = 86_400   # 24 hours

# ------------------------------------------------------------------ #
# Built-in translation dictionary                                      #
# ------------------------------------------------------------------ #

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Language selection (always shown in English) ────────────────
    "Welcome to Farmer's Companion\nChoose language:": {
        'sw': "Karibu Farmer's Companion\nChagua lugha:",
        'lg': "Tukwanulirwa mu Farmer's Companion\nSalira olulimi:",
        'rn': "Murakaza neza kuri Farmer's Companion\nHura ururimi:",
        'ac': "Wubone i Farmer's Companion\nYer leb:",
    },
    "1. English": {
        'sw': '1. Kiingereza', 'lg': '1. Olungereza',
        'rn': '1. Ikirundi',   'ac': '1. Ingiriza',
    },
    "2. Kiswahili": {
        'sw': '2. Kiswahili', 'lg': '2. Kiswahili',
        'rn': '2. Kiswahili', 'ac': '2. Kiswahili',
    },
    "3. Luganda": {
        'sw': '3. Luganda', 'lg': '3. Oluganda',
        'rn': '3. Oluganda', 'ac': '3. Luganda',
    },
    "4. Runyankole": {
        'sw': '4. Runyankole', 'lg': '4. Runyankole',
        'rn': '4. Runyankole', 'ac': '4. Runyankole',
    },
    "5. Acholi": {
        'sw': '5. Acholi', 'lg': '5. Acholi',
        'rn': '5. Acholi', 'ac': '5. Leb Acholi',
    },

    # ── Main menu ───────────────────────────────────────────────────
    "Welcome to Farmer's Companion": {
        'sw': "Karibu kwenye Farmer's Companion",
        'lg': "Tukwanulirwa mu Farmer's Companion",
        'rn': "Murakaza neza kuri Farmer's Companion",
        'ac': "Wubone i Farmer's Companion",
    },
    "1. Weather Forecast": {
        'sw': '1. Hali ya Hewa',
        'lg': "1. Obulagirizi bw'omusana",
        'rn': "1. Amakuru y'ikirere",
        'ac': '1. Cik me Cua',
    },
    "2. Market Prices": {
        'sw': '2. Bei za Masoko',
        'lg': "2. Bbeeyi ez'olusuku",
        'rn': "2. Ibiciro by'amasoko",
        'ac': '2. Wel pa Cen',
    },
    "3. Pest Diagnosis": {
        'sw': '3. Utambuzi wa Wadudu',
        'lg': "3. Endwadde y'ebimera",
        'rn': "3. Indwara z'ubuhinzi",
        'ac': '3. Temo pa Kongo',
    },
    "4. Farming Tips": {
        'sw': '4. Vidokezo vya Kilimo',
        'lg': "4. Ebiragiro eby'obulimi",
        'rn': "4. Inama z'ubuhinzi",
        'ac': '4. Pwony pa Jami',
    },
    "5. Ask AI": {
        'sw': '5. Uliza AI',
        'lg': '5. Buuza AI',
        'rn': '5. Baza AI',
        'ac': '5. Penyo AI',
    },
    "6. My Profile": {
        'sw': '6. Wasifu Wangu',
        'lg': '6. Porofayilo yange',
        'rn': '6. Umwirondoro wange',
        'ac': '6. Aketa pa An',
    },
    "7. Change Language": {
        'sw': '7. Badilisha Lugha',
        'lg': '7. Kyusa olulimi',
        'rn': '7. Hindura ururimi',
        'ac': '7. Loko Leb',
    },
    "0. Exit": {
        'sw': '0. Toka',   'lg': '0. Vamu',
        'rn': '0. Sohoka', 'ac': '0. Wot',
    },

    # ── Weather ─────────────────────────────────────────────────────
    "Weather Forecast": {
        'sw': 'Hali ya Hewa',
        'lg': "Obulagirizi bw'omusana",
        'rn': "Amakuru y'ikirere",
        'ac': 'Cik me Cua',
    },
    "1. Today's weather": {
        'sw': "1. Hali ya hewa leo",
        'lg': "1. Omusana wa leero",
        'rn': "1. Ikirere k'uyu munsi",
        'ac': '1. Cua wa Tin',
    },
    "2. 7-day forecast": {
        'sw': '2. Utabiri wa siku 7',
        'lg': '2. Obulagirizi bwa naku 7',
        'rn': '2. Amakuru ya iminsi 7',
        'ac': '2. Cik me Nino Abiro',
    },
    "0. Back": {
        'sw': '0. Rudi', 'lg': '0. Ddayo',
        'rn': '0. Garuka', 'ac': '0. Dok',
    },

    # ── Market prices ───────────────────────────────────────────────
    "Market Prices": {
        'sw': 'Bei za Masoko',
        'lg': "Bbeeyi ez'olusuku",
        'rn': "Ibiciro by'amasoko",
        'ac': 'Wel pa Cen',
    },
    "1. Maize": {
        'sw': '1. Mahindi', 'lg': '1. Kasooli',
        'rn': '1. Kasooli', 'ac': '1. Kal',
    },
    "2. Beans": {
        'sw': '2. Maharagwe', 'lg': '2. Ebijanjaalo',
        'rn': '2. Ibishyimbo', 'ac': '2. Latooma',
    },
    "3. Cassava": {
        'sw': '3. Muhogo', 'lg': '3. Muwogo',
        'rn': '3. Imyumbati', 'ac': '3. Bao',
    },
    "4. Coffee": {
        'sw': '4. Kahawa', 'lg': '4. Kawuufu',
        'rn': '4. Ikawa', 'ac': '4. Kawa',
    },

    # ── Pest diagnosis ──────────────────────────────────────────────
    "Pest Diagnosis": {
        'sw': 'Utambuzi wa Wadudu',
        'lg': "Endwadde y'ebimera",
        'rn': "Indwara z'ubuhinzi",
        'ac': 'Temo pa Kongo',
    },
    "Describe your crop problem:": {
        'sw': 'Elezea tatizo la zao lako:',
        'lg': "Nnyonnyola obuzibu bw'ekimera kyo:",
        'rn': "Sobanura ikibazo cy'igihingwa cyawe:",
        'ac': 'Nyut can pa cek megi:',
    },
    "1. Yellow/wilting leaves": {
        'sw': '1. Majani ya njano/yanayoanguka',
        'lg': '1. Ebijanjalo ebirutirutira/ebikwansa',
        'rn': '1. Amababi y\'umuhondo/agadindira',
        'ac': '1. Pot maleng/ma golo',
    },
    "2. Holes in leaves": {
        'sw': '2. Mashimo kwenye majani',
        'lg': '2. Embuzi mu ebijanjalo',
        'rn': '2. Imy구멍 mu mababi',
        'ac': '2. Bal i pot',
    },
    "3. Stunted growth": {
        'sw': '3. Ukuaji uliosimama',
        'lg': '3. Enkula ennono',
        'rn': '3. Kwiyongera guke',
        'ac': '3. Nen matidi',
    },
    "4. Other (describe)": {
        'sw': '4. Nyingine (elezea)',
        'lg': '4. Ekirala (nnyonnyola)',
        'rn': '4. Ikindi (sobanura)',
        'ac': '4. Mukene (nyut)',
    },

    # ── Ask AI ──────────────────────────────────────────────────────
    "Ask AI": {
        'sw': 'Uliza AI',    'lg': 'Buuza AI',
        'rn': 'Baza AI',     'ac': 'Penyo AI',
    },
    "1. Crop advice": {
        'sw': '1. Ushauri wa mazao',
        'lg': "1. Ebiragiro eby'ebimera",
        'rn': "1. Inama z'ibihingwa",
        'ac': '1. Pwony pa Cek',
    },
    "2. Soil tips": {
        'sw': '2. Vidokezo vya udongo',
        'lg': '2. Ebiragiro ku ttaka',
        'rn': '2. Inama ku butaka',
        'ac': '2. Pwony pa Ngom',
    },
    "3. Fertilizer guide": {
        'sw': '3. Mwongozo wa mbolea',
        'lg': '3. Ebiragiro ku bbombo',
        'rn': '3. Inama ku ifumbire',
        'ac': '3. Pwony pa Mwolo',
    },
    "4. Irrigation tips": {
        'sw': '4. Vidokezo vya umwagiliaji',
        'lg': '4. Ebiragiro ku nsuuzi',
        'rn': '4. Inama ku kuhira amazi',
        'ac': '4. Pwony pa Pi',
    },

    # ── Farming tips ────────────────────────────────────────────────
    "Farming Tips": {
        'sw': 'Vidokezo vya Kilimo',
        'lg': "Ebiragiro eby'obulimi",
        'rn': "Inama z'ubuhinzi",
        'ac': 'Pwony pa Jami',
    },
    "1. Planting tips": {
        'sw': '1. Vidokezo vya kupanda',
        'lg': "1. Ebiragiro eby'okusiga",
        'rn': '1. Inama zo gutera',
        'ac': '1. Pwony pa Cibo Cek',
    },
    "2. Pest & disease alerts": {
        'sw': '2. Tahadhari za wadudu na magonjwa',
        'lg': "2. Obulamu bw'endwadde n'ensowera",
        'rn': "2. Amakuru y'indwara n'ibyounyi",
        'ac': '2. Lok pa Kite ki Two',
    },
    "3. Harvest advice": {
        'sw': '3. Ushauri wa mavuno',
        'lg': "3. Ebiragiro eby'okuŋŋaba",
        'rn': '3. Inama zo gusarura',
        'ac': '3. Pwony pa Kayo Cek',
    },

    # ── Weather response labels ──────────────────────────────────────
    "Weather in": {
        'sw': 'Hali ya hewa huko',
        'lg': 'Obulagirizi e',
        'rn': "Ikirere i",
        'ac': 'Cua i',
    },
    "Temp": {
        'sw': 'Joto', 'lg': 'Obutiti',
        'rn': 'Ubushyuhe', 'ac': 'Lyeto',
    },
    "Humidity": {
        'sw': 'Unyevu', 'lg': 'Amaizi mu bbanga',
        'rn': 'Ubunyumu', 'ac': 'Pii i kin',
    },
    "forecast": {
        'sw': 'utabiri', 'lg': 'obulagirizi',
        'rn': 'amakuru', 'ac': 'cik',
    },
    # Weather conditions from OpenWeatherMap (most common ones)
    "light rain": {
        'sw': 'mvua ndogo', 'lg': 'enkuba entono',
        'rn': 'imvura nkeya', 'ac': 'kot matidi',
    },
    "moderate rain": {
        'sw': 'mvua ya wastani', 'lg': 'enkuba ennungi',
        'rn': 'imvura yo hagati', 'ac': 'kot malac',
    },
    "heavy rain": {
        'sw': 'mvua kubwa', 'lg': 'enkuba ennene',
        'rn': 'imvura nyinshi', 'ac': 'kot mapol',
    },
    "clear sky": {
        'sw': 'anga wazi', 'lg': 'eggulu erikutte',
        'rn': 'ijuru ritagatifu', 'ac': 'polo yar',
    },
    "few clouds": {
        'sw': 'mawingu machache', 'lg': 'ebire bisusse mangu',
        'rn': 'ibicu bike', 'ac': 'kor manok',
    },
    "scattered clouds": {
        'sw': 'mawingu yaliyotawanyika', 'lg': 'ebire ebisasaanye',
        'rn': 'ibicu byarasambye', 'ac': 'kor ma olwelo',
    },
    "overcast clouds": {
        'sw': 'mawingu mengi', 'lg': 'ebire bingi',
        'rn': 'ibicu byinshi', 'ac': 'kor mapol',
    },
    "thunderstorm": {
        'sw': 'dhoruba ya radi', 'lg': 'kibugwe',
        'rn': 'inkuba', 'ac': 'nywel',
    },
    "mist": {
        'sw': 'ukungu', 'lg': 'omufu',
        'rn': 'ibihu', 'ac': 'pek',
    },
    "haze": {
        'sw': 'ukungu mwembamba', 'lg': 'omufu omutono',
        'rn': 'umwotsi', 'ac': 'pek matidi',
    },
    "sunny": {
        'sw': 'jua kali', 'lg': 'omusana',
        'rn': 'izuba', 'ac': 'cawa',
    },
    "partly cloudy": {
        'sw': 'mawingu kidogo', 'lg': 'ebire bisusse',
        'rn': 'ibicu bike', 'ac': 'kor manok',
    },

    # ── Farming tips (full text) ─────────────────────────────────────
    "Planting tips: Prepare land 2 weeks early. Use certified seeds. Plant at start of rains. Space maize 75x25cm.": {
        'sw': (
            "Vidokezo vya kupanda: Tayarisha ardhi wiki 2 mapema. "
            "Tumia mbegu zilizoidhinishwa. Panda mwanzo wa mvua. "
            "Nafasi ya mahindi: 75x25cm."
        ),
        'lg': (
            "Ebiragiro eby'okusiga: Tegeka ettaka wiiki 2 nga tonnasiga. "
            "Kozesa ensigo ez'eby'obuwangwa. Siga nga enkuba egenda okutandika. "
            "Jjuza kasooli 75x25cm."
        ),
        'rn': (
            "Inama zo gutera: Tegura ubutaka inshuro 2 mbere yo gutera. "
            "Koresha imbuto zemewe. Tera mu ntangiriro y'imvura. "
            "Bane kasooli 75x25cm."
        ),
        'ac': (
            "Pwony pa cibo cek: Cik ngom wiik 2 cok. "
            "Tic ki kal ma gitic. Cib i tum me kot. "
            "Wek kakang 75x25cm."
        ),
    },
    "Pest alerts: Check for Fall Armyworm on maize. Spray neem early morning. Report outbreaks to extension officer.": {
        'sw': (
            "Tahadhari za wadudu: Angalia Armyworm kwenye mahindi. "
            "Nyunyiza dawa ya mwarobaini asubuhi. "
            "Ripoti mlipuko kwa afisa ugani."
        ),
        'lg': (
            "Obulamu bw'ensowera: Noonya ensowera ku kasooli. "
            "Siiga omuzizi gw'omuyembe mangu mu makya. "
            "Buulira omulabirizi w'obulimi."
        ),
        'rn': (
            "Amakuru y'ibyounyi: Reba ibyounyi ku kasooli. "
            "Siga umuti w'umuyembe vuba mu gitondo. "
            "Menyesha umujyanama w'ubuhinzi."
        ),
        'ac': (
            "Lok pa kite: Rot kite i kal. "
            "Wir yat pa oliiti odiko. "
            "Leb labong pa jami."
        ),
    },
    "Harvest advice: Harvest maize when husks are dry. Dry grain below 13% moisture. Use hermetic bags for storage.": {
        'sw': (
            "Ushauri wa mavuno: Vuna mahindi maganda yake yatakapokauka. "
            "Kausha nafaka chini ya 13% unyevu. "
            "Tumia mifuko maalum kuhifadhi."
        ),
        'lg': (
            "Ebiragiro eby'okuŋŋaba: Ŋŋaba kasooli ng'empumba eyombye. "
            "Umba emmere wansi wa 13% amaizi. "
            "Kozesa ensawo ezizikiriza okutereka."
        ),
        'rn': (
            "Inama zo gusarura: Satura kasooli amahundo gakaze. "
            "Humeka inyabura munsi ya 13%. "
            "Koresha amasaho yihariye yo kubika."
        ),
        'ac': (
            "Pwony pa kayo cek: Kayo kal i kare ocoo oyoo. "
            "Kang kal piny pa 13% pii. "
            "Tic ki poto ma kite ok donyo pi meko."
        ),
    },

    # ── Static AI fallback responses ────────────────────────────────
    "Plant maize at start of long rains (Mar-May). Use certified seed at 75x25cm spacing. Apply CAN fertilizer 6 weeks after planting.": {
        'sw': (
            "Panda mahindi mwanzo wa mvua ndefu (Mar-Mei). "
            "Tumia mbegu zilizoidhinishwa kwa nafasi ya 75x25cm. "
            "Weka mbolea ya CAN wiki 6 baada ya kupanda."
        ),
        'lg': (
            "Siga kasooli nga enkuba empanvu etandika (Mar-Mei). "
            "Kozesa ensigo ez'eby'obuwangwa mu 75x25cm. "
            "Teeka bbombo ya CAN wiiki 6 ng'onasiga."
        ),
        'rn': (
            "Tera kasooli mu ntangiriro y'imvura ndefu (Mar-Mei). "
            "Koresha imbuto zemewe 75x25cm. "
            "Shyira ifumbire ya CAN inshuro 6 nyuma yo gutera."
        ),
        'ac': (
            "Cib kal i tum me kot malac (Mar-Mei). "
            "Tic ki kal ma gitic 75x25cm. "
            "Ket mwolo pa CAN wiik 6 bang cibo."
        ),
    },
    "Add compost or manure before tilling. Rotate crops each season to restore soil nutrients. Avoid burning crop residues — dig them in instead.": {
        'sw': (
            "Ongeza mboji au samadi kabla ya kulima. "
            "Badilisha mazao kila msimu kurejesha virutubisho. "
            "Usichome mabaki ya mazao — yafukuzie ardhini."
        ),
        'lg': (
            "Yongeza omukuyu oba ebisaasiro nga tonnalima. "
            "Kyusa ebimera buli season okuzzaamu emisingi. "
            "Tolokya amasaasiro ga ebimera — biwumba mu ttaka."
        ),
        'rn': (
            "Ongereza urumogi cyangwa amase mbere yo guhinga. "
            "Hindura ibihingwa buri gihe kugira ngo ubutaka busubire. "
            "Ntukomereze imisibo y'ibihingwa — yimike mu butaka."
        ),
        'ac': (
            "Ket lubuku onyo labol ka piny pe ilimo. "
            "Loko cek buk buk me miyo ngom odwog. "
            "Pe wil gik ma dong i cek — por i ngom."
        ),
    },
    "Apply DAP at planting (1 bag per acre). Top-dress with CAN 6 weeks later. Use urea only on well-watered soil to avoid leaf burn.": {
        'sw': (
            "Weka DAP wakati wa kupanda (gunia 1 kwa ekari). "
            "Ongeza CAN wiki 6 baadaye. "
            "Tumia urea kwenye udongo wenye maji ya kutosha."
        ),
        'lg': (
            "Teeka DAP ng'osiga (musawo 1 mu ekari). "
            "Yongeza CAN wiiki 6 oluvannyuma. "
            "Kozesa urea ku ttaka eriko amazzi mangi."
        ),
        'rn': (
            "Shyira DAP iyo utera (isaki 1 ku ekari). "
            "Ongereza CAN inshuro 6 nyuma. "
            "Koresha urea gusa ku butaka bufite amazi ahagije."
        ),
        'ac': (
            "Ket DAP i kare cibo (poto 1 pa ekari). "
            "Onyo CAN wiik 6 lacen. "
            "Tic ki urea i ngom ma pii rom."
        ),
    },
    "Water crops early morning to reduce evaporation. Use mulch around plants to retain soil moisture. Dig simple water channels to direct rain runoff to crops.": {
        'sw': (
            "Mwagilia mazao asubuhi na mapema kupunguza uvukizi. "
            "Tumia matandazo kuzuia unyevu. "
            "Chimba mifereji rahisi kuelekeza maji ya mvua."
        ),
        'lg': (
            "Nawula ebimera mangu mu makya okukebera okubba kw'amazzi. "
            "Kozesa ebiwumba okujjirira amaizi mu ttaka. "
            "Kimba ensalire okukwata amazzi g'enkuba."
        ),
        'rn': (
            "Hira ibihingwa vuba mu gitondo kugabanya ubushuhe. "
            "Koresha uburembo kubika ubunyumu bw'ubutaka. "
            "Imba imiyoboro yoroshye yo guherekeza amazi."
        ),
        'ac': (
            "Wir cek odiko ma con pi cuko camo pii. "
            "Tic ki gik ma tino pi gwoko pii i ngom. "
            "Kim yo pii matidi pi tero pii kot i cek."
        ),
    },
    "Yellow leaves may indicate nitrogen deficiency or mosaic virus. Remove affected plants and apply foliar fertilizer. Use certified disease-free seeds next season.": {
        'sw': (
            "Majani ya njano yanaweza kuonyesha upungufu wa nitrojeni au virusi. "
            "Ondoa mimea iliyoathiriwa na weka mbolea ya majani. "
            "Tumia mbegu zilizo salama msimu ujao."
        ),
        'lg': (
            "Ebijanjalo eby'obuterere bisobola okutegeeza obunono bwa nitrogen oba endwadde. "
            "Ggyamu ebimera ebikyamye okewolereze bbombo. "
            "Kozesa ensigo zitalina ndwadde mu season ejja."
        ),
        'rn': (
            "Amababi y'umuhondo ashobora kwerekana ubukene bwa azote cyangwa virus. "
            "Kura ibihingwa byononekaye usige ifumbire ku mababi. "
            "Koresha imbuto zidafite indwara mu gihe gikurikira."
        ),
        'ac': (
            "Pot maleng twero nyuto two me nitrogen onyo tuo. "
            "Kwar cek ma two opoto i wiye ki mwolo me pot. "
            "Tic ki kal ma ki two i buk ma bino."
        ),
    },
    "Check local weather before applying pesticides or fertilizer. Avoid planting just before heavy rains — wait 2 days. Harvest before forecast rain to protect grain quality.": {
        'sw': (
            "Angalia hali ya hewa kabla ya dawa au mbolea. "
            "Epuka kupanda kabla ya mvua kubwa — subiri siku 2. "
            "Vuna kabla ya mvua iliyotabiriwa."
        ),
        'lg': (
            "Kebera obulagirizi bw'omusana nga tonnateekawo dawa oba bbombo. "
            "Wewale okusiga mangu enkuba ennene ng'edda — linda naku 2. "
            "Ŋŋaba nga enkuba etannajja okuggya."
        ),
        'rn': (
            "Reba ikirere mbere yo gushyira imiti cyangwa ifumbire. "
            "Irinda gutera mbere y'imvura nyinshi — tegereza iminsi 2. "
            "Satura mbere y'imvura ihanganywaho."
        ),
        'ac': (
            "Rot cua ka piny ka ki wir yat onyo mwolo. "
            "Juk cibo cok ka kot mapol — kur nino 2. "
            "Kayo cek ka piny ka kot ma gire obino."
        ),
    },
    "Keep a simple farm diary to track planting dates and yields. Join a local farmer group to share knowledge and inputs. Contact your extension officer for free advice on your crops.": {
        'sw': (
            "Weka daftari rahisi la shamba kufuatilia tarehe za kupanda. "
            "Jiunge na kikundi cha wakulima kushiriki ujuzi. "
            "Wasiliana na afisa ugani kwa ushauri wa bure."
        ),
        'lg': (
            "Tereka buku entono ey'okulima okusiga emiramwa. "
            "Yingira mu kibiina ky'abalimi okusangira omulembe. "
            "Kukumba omulabirizi w'obulimi okufuna ebiragiro."
        ),
        'rn': (
            "Bika igitabo gito cy'ubuhinzi gukurikirana iminsi yo gutera. "
            "Injira itsinda ry'abahinzi gusangira ubwenge. "
            "Vugana n'umujyanama w'ubuhinzi kubona inama."
        ),
        'ac': (
            "Gwok buk matidi me jami pi nongo nino me cibo. "
            "Donyo i kal pa jo jami pi poko ni kwano. "
            "Neng labong pa jami pi koya kel ma pe lim."
        ),
    },

    # ── System messages ─────────────────────────────────────────────
    "Thank you for using Farmer's Companion. Goodbye!": {
        'sw': "Asante kwa kutumia Farmer's Companion. Kwaheri!",
        'lg': "Webale okukozesa Farmer's Companion. Weraba!",
        'rn': "Murakoze gukoresha Farmer's Companion. Murabeho!",
        'ac': "Apwoyo pi tiyo ki Farmer's Companion. Wot Maber!",
    },
    "Invalid option. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
        'ac': 'Yero maber. Tem doki.',
    },
    "Invalid choice. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
        'ac': 'Yero maber. Tem doki.',
    },
    "Could not retrieve weather right now. Try again later.": {
        'sw': 'Haikuweza kupata hali ya hewa sasa. Jaribu baadaye.',
        'lg': "Tetusobodde kubona omulabirizi w'omusana. Gezaako oluvannyuma.",
        'rn': "Ntabwo twashoboye kuronka amakuru y'ikirere. Gerageza nyuma.",
        'ac': 'Peke twero nongo cik pa cua kina. Tem lacen.',
    },
    "You are not registered yet.\nSend REGISTER <name> via SMS\nor visit our website to sign up.": {
        'sw': 'Bado hujasajiliwa.\nTuma REGISTER <jina> kwa SMS\nau tembelea tovuti yetu.',
        'lg': 'Tonnateeka nnawe.\nTuma REGISTER <erinnya> mu SMS\noba laba website yaffe.',
        'rn': 'Ntabwo wanditse.\nHereza REGISTER <izina> kuri SMS\ncyangwa sura website yacu.',
        'ac': 'Peke icoyo nyiŋ ducu.\nCwal REGISTER <nyiŋ> pi SMS\nkadi lim website waŋwa.',
    },
    "AI service is unavailable. Try again later.": {
        'sw': 'Huduma ya AI haipo. Jaribu baadaye.',
        'lg': 'Obuweereza bwa AI tebulipo. Gezaako oluvannyuma.',
        'rn': 'Serivisi ya AI ntiboneka. Gerageza nyuma.',
        'ac': 'Tic pa AI pe tye. Tem lacen.',
    },
}


# ------------------------------------------------------------------ #
# Public API                                                           #
# ------------------------------------------------------------------ #

def translate(text: str, language: str) -> str:
    """
    Translate *text* into *language*.
    Falls back to the English original if no translation is found.
    """
    if language == DEFAULT_LANGUAGE or language not in SUPPORTED_LANGUAGES:
        return text

    cache_key = _cache_key(text, language)
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Built-in dictionary
    result = TRANSLATIONS.get(text, {}).get(language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    # OpenAI fallback — only if not obviously quota-exhausted
    # (check the ai_assistant quota flag to avoid wasting time)
    try:
        from apps.ussd.services.ai_assistant import _last_failure_was_quota
        if _last_failure_was_quota.get('gemini', False):
            # Both AI providers are quota-exhausted — fall back to English immediately
            logger.debug("Translation skipping OpenAI (quota exhausted) for lang=%s", language)
            return text
    except ImportError:
        pass

    result = _openai_translate(text, language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    logger.warning("No translation for lang=%s text='%.40s', using English", language, text)
    return text


def get_menu(lines: list[str], language: str, prefix: str = 'CON') -> str:
    """
    Build a USSD menu string from a list of lines, translating each one.
    prefix is 'CON' (keep session open) or 'END' (close session).
    """
    translated = [translate(line, language) for line in lines]
    return prefix + ' ' + '\n'.join(translated)


# ------------------------------------------------------------------ #
# Internal helpers                                                     #
# ------------------------------------------------------------------ #

def _cache_key(text: str, language: str) -> str:
    digest = hashlib.md5(text.encode()).hexdigest()[:12]
    return f"ussd_trans_{language}_{digest}"


def _openai_translate(text: str, language: str) -> str | None:
    """Call OpenAI to translate text. Returns None on any failure.
    max_retries=0 and timeout=3s to stay within the USSD 5s budget.
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, max_retries=0, timeout=3.0)
        lang_name = SUPPORTED_LANGUAGES[language]
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        f'You are a translator for a farmer USSD app in Uganda. '
                        f'Translate the following text to {lang_name}. '
                        f'Preserve all newlines and numbering exactly as given. '
                        f'Return only the translated text — no explanations.'
                    ),
                },
                {'role': 'user', 'content': text},
            ],
            max_tokens=300,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI translation failed: %s", str(exc)[:200])
        return None
