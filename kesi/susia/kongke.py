import unicodedata
import re

# from kesi.susia.pio import STANDARD_INITIALS, STANDARD_FINALS
from kesi.susia.pio import KONGKE_SIANNBO, KONGKE_UNBO

SI_TSUAN_TUASIA = 'CASE_ALL_UPPER'
SI_TSUAN_SIOSIA = 'CASE_ALL_LOWER'
SI_THAU_TUASIA = 'CASE_TITLE'


NUMBER_DIAC_MAP = {
    '1': '',
    '2': '\u0301',
    '3': '\u0300',
    '4': '',
    '5': '\u0302',
    '6': '\u030c',
    '7': '\u0304',
    '8': '\u030d',
    '9': '\u0306',
}


def detect_case_style(text):
    latin = text.replace('ⁿ', '')
    if latin.islower():
        return SI_TSUAN_SIOSIA
    elif latin[:1].isupper() and not latin[1:].isupper():
        return SI_THAU_TUASIA
    else:
        return SI_TSUAN_TUASIA


def apply_case_style(case_style, text):
    if case_style == SI_TSUAN_TUASIA:
        return text.upper()
    elif case_style == SI_TSUAN_SIOSIA:
        return text.lower()
    else:
        return text.capitalize()

# thiah
def parse_syllable(lomaji):
    syllable, tone = extract_tone_mark(lomaji)

    syllable_norm = normalize_superscript_n(syllable)
    case_style = detect_case_style(syllable_norm)

    lowercase_syllable = syllable_norm.lower()
    canonical_form = normalize_to_standard_form(lowercase_syllable)
    initial, final = split_initial_final(canonical_form)
    return initial, final, tone, case_style


def extract_tone_mark(lomaji):
    nfd = unicodedata.normalize('NFD', lomaji)
    # Numeric tone notation
    if nfd[-1:] in NUMBER_DIAC_MAP:
        return nfd[:-1], NUMBER_DIAC_MAP[nfd[-1]]
    # Traditional diacritic tone notation
    tone_match = re.search(
        '\u0301|\u0300|\u0302|\u030c|\u0304|\u030d|\u030b|\u0306', nfd)
    try:
        tone = tone_match.group(0)
    except AttributeError:
        tone = ''  # tone 1 or 4
    syllable = nfd.replace(tone, '')
    return syllable, tone


def normalize_superscript_n(syllable):
    romanization = re.sub('([a-z])(N)(h?)', r'\1ⁿ\3',syllable)
    romanization = romanization.replace('ᴺ', 'ⁿ')
    return romanization


def normalize_to_standard_form(syllable):
    normalized = (
        syllable
        .replace('ch', 'ts')
        .replace('ou', 'oo')
        .replace('o͘', 'oo')
        .replace('ⁿ', 'nn')
        .replace('oa', 'ua')
        .replace('oe', 'ue')
        .replace('eng', 'ing')
        .replace('ek', 'ik')
        .replace('oonn', 'onn')
    )
    return normalized


def split_initial_final(toneless_phonetic):
    for index in range(len(toneless_phonetic)):
        initial = toneless_phonetic[:index]
        if initial.lower() in KONGKE_SIANNBO:
            final = toneless_phonetic[index:]
            if final.lower() in KONGKE_UNBO:
                return initial, final
    raise RomanizationParseError(f'Bô tsit-khuán im-tsiat: {toneless_phonetic}')


class RomanizationParseError(ValueError):
    pass
