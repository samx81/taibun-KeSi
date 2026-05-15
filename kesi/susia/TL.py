import unicodedata
from kesi.susia.kongke import parse_syllable, apply_case_style, RomanizationParseError
from kesi.butkian.kongiong import NEUTRAL_SYMBOL


def toTL(text):
    is_neutral = text.startswith(NEUTRAL_SYMBOL)
    if is_neutral:
        text = text.replace(NEUTRAL_SYMBOL, '')
    try:
        initial, final, tone, case_style = parse_syllable(text)
    except RomanizationParseError:
        return text
    tailo = kapTL(initial, final, tone)
    kiatko = apply_case_style(case_style, tailo)
    if is_neutral:
        kiatko = '--{}'.format(kiatko)
    return kiatko


def kapTL(siann, un, tiau):
    tiau = tsuan_TL_tiau(tiau)
    un = tau_tiauhu(un, tiau)
    return unicodedata.normalize(
        'NFC', siann + un)


def tsuan_TL_tiau(tiau):
    if tiau == '\u0306':
        return '\u030b'
    return tiau


def tau_tiauhu(un, tiau):
    lomaji = ''
    if 'a' in un:
        lomaji = un.replace('a', 'a' + tiau)
    elif 'oo' in un:
        lomaji = un.replace('oo', 'o' + tiau + 'o')
    elif 'ere' in un:
        lomaji = un.replace('ere', 'ere' + tiau)
    elif 'e' in un:
        lomaji = un.replace('e', 'e' + tiau)
    elif 'o' in un:
        lomaji = un.replace('o', 'o' + tiau)
    elif 'ui' in un:
        lomaji = un.replace('i', 'i' + tiau)
    elif 'iu' in un:
        lomaji = un.replace('u', 'u' + tiau)
    elif 'iri' in un:
        lomaji = un.replace('iri', 'iri' + tiau)
    elif 'i' in un:
        lomaji = un.replace('i', 'i' + tiau)
    elif 'u' in un:
        lomaji = un.replace('u', 'u' + tiau)
    elif 'ng' in un:
        # ng, mng
        lomaji = un.replace('ng', 'n' + tiau + 'g')
    elif 'm' in un:
        lomaji = un.replace('m', 'm' + tiau)
    return lomaji
