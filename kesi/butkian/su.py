# -*- coding: utf-8 -*-
from typing import Literal

from kesi.butkian.kongiong import CONNECT_SYMBOL, is_lomaji
from kesi.butkian.kongiong import NEUTRAL_SYMBOL


class Su:

    def __init__(self, ji: list=None):
        self._ji = ji if ji else []
        self.remove_han_dash = False

    def __iter__(self):
        yield from self._ji

    def __len__(self):
        return len(self._ji)

    def __eq__(self, other):
        return self._ji == other._ji
    
    def format_string(self, mode: Literal['hanlo', 'lomaji']):
        """
        會 kā 文本標準化：
        判斷愛先添連字符無
          H, H -> 'HH'
          H, L -> 'HL'
          L, H -> 'LH'
          L, L -> 'L-L'
          L, --L -> 'L--L'
        """
        tokens = []
        prev_char_is_lomaji = False
        word_has_neutral = False

        for char in self:
            text = getattr(char, mode)
            # print(text, not self.remove_han_dash,  not char.CJK)
            # print(text, self.remove_han_dash, (mode == 'hanlo' and not self.remove_han_dash), (mode == 'lomaji' and not char.CJK))
            # if (mode == 'hanlo' and not self.remove_han_dash) or \
            #     (mode == 'lomaji' and not char.CJK):
            if not self.remove_han_dash or not char.CJK:
                if char.is_neutral:
                    " Mài thinn liân-jī-hû "
                    text = f"{NEUTRAL_SYMBOL}{text}"
                    word_has_neutral = True
                elif prev_char_is_lomaji and is_lomaji(text[0]):
                    " L, L -> 'L-L' "
                    tokens.append(CONNECT_SYMBOL)
                elif word_has_neutral:
                    " --H, H -> '--H-H' "
                    tokens.append(CONNECT_SYMBOL)
            else:
                if prev_char_is_lomaji:
                    tokens.append(" ")
            tokens.append(text)
            prev_char_is_lomaji = is_lomaji(text[-1])
        return ''.join(tokens)

    @property
    def hanlo(self):
        return self.format_string('hanlo')

    @property
    def lomaji(self):
        return self.format_string('lomaji')

    @property
    def kiphanlo(self):
        """
        會 kā 文本標準化：
        判斷愛先添連字符無
          H, H -> 'HH'
          H, L -> 'HL'
          L, H -> 'LH'
          L, L -> 'L-L'
          L, --L -> 'L--L'
        """
        tokens = []
        prev_char_is_lomaji = False

        for w in self:
            hanlo = w.kiphanlo

            if prev_char_is_lomaji and is_lomaji(hanlo[0]):
                " L, L -> 'L-L' "
                if w.is_neutral:
                    tokens.append(NEUTRAL_SYMBOL)
                else:
                    tokens.append(CONNECT_SYMBOL)

            tokens.append(hanlo)
            prev_char_is_lomaji = is_lomaji(hanlo[-1])
        return ''.join(tokens)

    def append(self, ji):
        self._ji.append(ji)

    def POJ(self):
        return Su([ji.POJ() for ji in self])

    def TL(self):
        return Su([ji.TL() for ji in self])


    KIP = TL
