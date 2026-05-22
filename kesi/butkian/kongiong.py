# -*- coding: utf-8 -*-
# 瀏覽器希望無音愛有空白，但是處理標音時希望較好認
import unicodedata
import re
from unicodedata import normalize


CONNECT_SYMBOL = '-'
NEUTRAL_SYMBOL = '--'
# 句中是為著加速標音
PUNC_IN_SENT = {
    '、', '﹑', '､', '-', '—', '~', '～',
    '·', '‧',  # 外國人名中間
    "'", '＇', '"', '‘', '’', '“', '”', '〝', '〞', '′', '‵',
    '「', '」', '｢', '｣', '『', '』',
    '【', '】', '〈', '〉', '《', '》', '（', '）', '＜', '＞',
    '(', ')', '<', '>', '[', ']', '{', '}',
    '+', '*', '/', '=', '^', '＋', '－', '＊', '／', '＝', '$', '#', '#',
    ':', '：', '﹕', '–', '—', '―', '─', '──', '｜', '︱',
    '•',
}

# 斷句是考慮著翻譯，閣有語音合成愛做的正規化
PUNC_NEW_SENT = (
    {'\n', } |
    {'，', '。', '．', '！', '？', '…', '……', '...', } |
    {',', '.', '!', '?', } |
    {'﹐', '﹒', '﹗', '﹖', } |
    {';', '；', '﹔', }
)

punctuation_mapping = {
    '。':'.', '．':' ', '，':',', '、':',', '！':'!', '？':'?', '；':';', '：':':',
    '）':')', '］':']', '】':']', '（':'(', '［':'[', '【':'['
}
full_width_punc = "「」〈〉《》『』～・" + ''.join(punctuation_mapping.keys())

NON_PRINTABLE_CHARS = re.compile(
    r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]'
)


# Siann-tiāu / TONE
HAGFA_TIAU = {
    '', 'ˊ', 'ˋ', 'ˇ', '+', '^'
}
NGOO_SIU_LE = {
    '0': '˙', '1': '', '2': 'ˋ', '3': '˪',
    '4': '', '5': 'ˊ', '6': '˫', '7': '˫',
    '8': '㆐', '9': '^', '10': '㆐'
}

# 造字
KIP_TSOJI = {
    '\uE701': '\U0002A736',
    '\uF5E9': '\U0002B74F',
    '\uE35C': '\U0002B75B',
    '\uF5EA': '\U0002B77A',
    '\uF5EE': '\U0002B77B',
    '\uE703': '\U0002B7BC',
    '\uF5EF': '\U0002B7C2',
    '\uE705': '\U0002C9B0',
    '\uF5E7': '\U000308FB',
}

TONE_SYMBOL = (
    HAGFA_TIAU |
    set(NGOO_SIU_LE.values())
) - {''}


PUNC = PUNC_IN_SENT | PUNC_NEW_SENT

COMPOSITION_SYMBOL = '⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿿'

# Ll　小寫， Lu　大寫， Md　數字， Mn　有調號英文，Lo　其他, So 組字式符號…
_統一碼羅馬字類 = {'Ll', 'Lu', 'Mn'}


def is_lomaji(jiguan):
    return is_roman(jiguan) or jiguan.isdigit()

def is_han(char):
    try:
        cat = unicodedata.category(char)
    except TypeError:
        return False
    return cat == 'Lo' or char in full_width_punc

def norm_diacritic(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def is_roman(char):
    try:
        種類 = unicodedata.category(char)
    except TypeError:
        return False
    return 種類 in _統一碼羅馬字類 or char in ['ⁿ', "'", '_', 'ᴺ', ]


def is_bopomofo(字元):
    return unicodedata.name(字元, '').startswith('BOPOMOFO LETTER')


def normalize_kautian(taibun):
    for ji_kautian, ji_unicode in KIP_TSOJI.items():
        taibun = taibun.replace(ji_kautian, ji_unicode)
    return taibun


def normalize_taibun(taibun):
    taibun = re.sub(NON_PRINTABLE_CHARS, ' ', taibun)
    taibun = normalize_kautian(taibun)
    taibun = normalize('NFC', taibun)
    return taibun
