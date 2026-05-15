from .butkian.ku import Ku
from .butkian.ku import TuiBeTse
from .butkian.kongiong import normalize_taibun
from .butkian.kongiong import PUNC as PIAUTIAM
from .susia.kongke import parse_syllable, RomanizationParseError


def kam_haphuat(tsit_ji_lomaji):
    try:
        parse_syllable(tsit_ji_lomaji)
    except RomanizationParseError:
        return False
    return True


__all__ = [
    'Ku', 'TuiBeTse', 'normalize_taibun',
    'kam_haphuat', PIAUTIAM,
]
