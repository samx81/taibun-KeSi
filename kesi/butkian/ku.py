import re
import shutil
from typing import Literal
from dataclasses import dataclass

from kesi.butkian.kongiong import (
    COMPOSITION_SYMBOL,
    CONNECT_SYMBOL,
    TONE_SYMBOL,
    HALF_WIDTH_PUNC,
    PUNC,
    is_roman,
    is_bopomofo,
    is_lomaji,
    is_han,
    norm_diacritic,
    normalize_taibun,
)
from kesi.butkian.su import Su
from kesi.butkian.ji import Ji

taibun_hint_shown = False
def get_taibun_converter():
    global taibun_hint_shown
    try:
        from taibun import Converter
    except Exception as e:
        if not taibun_hint_shown:
            print(e)
            print(
                'This function need taibun support\n'
                'Please install with `pip install taibun`'
            )
        taibun_hint_shown = True
        return None
    return Converter(tone_format='number')

@dataclass
class ErrInfo:
    han_tokens: list[str]
    tailo_tokens: list[str]
    message: str


class Ku:
    """
    ku = Ku()
    su = Su()
    ji = Ji()

    for su in ku:
        for ji in su:
            for guan in ji.hanlo:
    """
    
    _split_word_pattern = re.compile('(([^ ｜]*[^ ]｜[^ ][^ ｜]*) ?|[^ ]+)')
    _multi_char_punctuation = re.compile(r'(\.\.\.)|(……)|(──)')
    _whitespace_pattern = re.compile(r'[^\S\n]+')
    _hyphen_pattern = re.compile(r'{}+'.format(CONNECT_SYMBOL))
    _digit_chars = set('0123456789')

    def __init__(self, hanlo=None, lomaji=None, remove_han_dash=False, raise_unmatch=True):
        self.remove_han_dash = remove_han_dash
        self.err_info = None

        if hanlo is not None:
            hanlo = normalize_taibun(hanlo)
        if lomaji is not None:
            lomaji = normalize_taibun(lomaji)

        # Ku(lomaji='Goa')
        if hanlo is None:
            hanlo = lomaji
            lomaji = None

        if hanlo is None:
            self._su = []
        elif lomaji is None:
            (
                split_chars,
                char_neutral_tone_flags,
                word_boundary_flags,
            ) = self._analyze_sentence(hanlo)

            word_chunks, neutral_tone_chunks = self._group_words(
                split_chars,
                char_neutral_tone_flags,
                word_boundary_flags,
            )

            self._su = self._build_su_list(word_chunks, neutral_tone_chunks)

        else:
            """Use romanization segmentation as primary source"""

            split_hanlo, _, _ = self._analyze_sentence(hanlo)

            (
                split_lomaji,
                char_neutral_tone_flags, 
                word_boundary_flags,
            ) = self._analyze_sentence(lomaji)

            if len(split_hanlo) != len(split_lomaji):
                han_align, lomaji_align, hint_align = self.align_error_tokens(split_hanlo, split_lomaji)

                terminal_width = shutil.get_terminal_size().columns
                terminal_width //= 10

                exc_msg = ( 
                    f'Tokens not matched -> '
                    f'Hanlo tokens: {len(split_hanlo)}, lomaji tokens: {len(split_lomaji)}\n'
                )
                for sub_i in range(0, len(han_align), terminal_width):
                    sub_i_end = sub_i+terminal_width
                    exc_msg += f"| {' | '.join(han_align[sub_i:sub_i_end])} |\n| {' | '.join(lomaji_align[sub_i:sub_i_end])} |\n" 
                    exc_msg += f"| {' | '.join(hint_align[sub_i:sub_i_end])} |\n"
                # exc_msg += f"{hanlo}\n{lomaji}\n"
                if raise_unmatch:
                    raise TuiBeTse(exc_msg)
                else:
                    self.err_info = ErrInfo(split_hanlo, split_lomaji, exc_msg)

            grouped_hanlo, _ = self._group_words(
                split_hanlo,
                char_neutral_tone_flags,
                word_boundary_flags,
            )

            grouped_lomaji, neutral_tones = self._group_words(
                split_lomaji,
                char_neutral_tone_flags,
                word_boundary_flags,
            )

            self._su = self._build_paired_su_list(
                grouped_hanlo,
                grouped_lomaji,
                neutral_tones,
            )

    def __str__(self):
        return self.hanlo

    def __iter__(self):
        yield from self._su

    def __getitem__(self, index):
        return self._su[index]

    def __len__(self):
        return len(self._su)

    def __eq__(self, other):
        return self._su == other._su
    
    def align_error_tokens(self, split_hanlo, split_lomaji):
        han_align = []
        lomaji_align = []
        hint_align = []
        max_len = max(len(split_hanlo), len(split_lomaji))
        taibun_conv = get_taibun_converter()
        taibun_dict = taibun_conv.word_dict.word_dict if taibun_conv else {}
        for i in range(max_len):
            h = split_hanlo[i] if i < len(split_hanlo) else ''
            t = split_lomaji[i] if i < len(split_lomaji) else ''
            arrow = '' if (h == t) or (taibun_conv and h and t and taibun_dict.get(h) == taibun_conv.to_mark(t)) else '^'

            han_len = sum(2 if is_han(c) else 1 for c in h)
            common_len = max(han_len, len(norm_diacritic(t)))

            han_align.append(h.ljust(common_len - len(h)))
            lomaji_align.append(t.ljust(common_len))
            hint_align.append(arrow.ljust(common_len))

        return han_align, lomaji_align, hint_align

    def _build_su_list(self, words, word_neutral_tones):
        su_list = []
        for word, neutral_tones in zip(words, word_neutral_tones):
            su = Su()
            for char, is_neutral_tone in zip(word, neutral_tones):
                su.append(
                    Ji(char, is_neutral=is_neutral_tone)
                )
            su_list.append(su)
        return su_list

    def _build_paired_su_list(self, hanlo_words, lomaji_words, word_neutral_tones):
        su_list = []
        for hanlo, lomaji, neutral_tones in zip(
                hanlo_words, lomaji_words, word_neutral_tones):
            su = Su()
            for char, lomaji_char, is_neutral_tone in zip(
                    hanlo, lomaji, neutral_tones):
                su.append(
                    Ji(char, lomaji=lomaji_char,
                        is_neutral=is_neutral_tone)
                )
            su_list.append(su)
        return su_list
    
    def format_string(self, mode: Literal['hanlo', 'lomaji', 'kiphanlo'], remove_dash=False):
        """
        Normalize text:
        preserve romanization spaces,
        remove unnecessary spaces elsewhere.
        """

        output = []
        prev_word_endswith_lomaji = False
        for su in self:
            # print(su, remove_dash)
            su.remove_han_dash = remove_dash
            word = getattr(su, mode)
            if not word:
                continue
            #
            #  判斷愛先添空白符無
            #    H, H -> 'HH'
            #    H, L -> 'HL'
            #    L, L -> 'L L'
            #
            if prev_word_endswith_lomaji and is_lomaji(word[0]):
                output.append(' ')
            if output and output[-1] == ' ' and word in HALF_WIDTH_PUNC:
                output.pop()
            output.append(word)
            
            # TODO: change mode
            if word in HALF_WIDTH_PUNC:
                output.append(' ')
            prev_word_endswith_lomaji = is_lomaji(word[-1])
        return ''.join(output)


    @property
    def hanlo(self):
        return self.format_string('hanlo', self.remove_han_dash)

    @property
    def lomaji(self):
        return self.format_string('lomaji')

    @property
    def kiphanlo(self):
        return self.format_string('kiphanlo')

    def iter_chars(self):
        """
        Equivalent to: 臺灣言語工具.拆文分析器.篩出字物件
        """
        for word in self:
            yield from word

    def POJ(self):
        self._su = [su.POJ() for su in self]
        return self

    def TL(self):
        self._su = [su.TL() for su in self]
        return self

    KIP = TL

    def _group_words(self, char_list, neutral_tone_flags,word_boundary_flags):
        grouped_words = []
        grouped_neutral_tones = []
        index = 0
        while index < len(char_list):
            end = index
            while end < len(word_boundary_flags) and not word_boundary_flags[end]:
                end += 1
            end += 1
            grouped_words.append(char_list[index:end])
            grouped_neutral_tones.append(neutral_tone_flags[index:end])
            index = end
        return grouped_words, grouped_neutral_tones

    def _analyze_sentence(self, sentence):
        state = self._ParserState()
        if self._whitespace_pattern.fullmatch(sentence):
            return state.result()
        previous_char = None
        previous_was_hyphen = False
        previous_was_whitespace = False
        previous_was_neutral_tone_symbol = False
        previous_was_bopomofo = False
        index = 0
        while index < len(sentence):
            char = sentence[index]
            is_hyphen = False
            is_whitespace = False
            is_neutral_tone_symbol = False
            is_char_bopomofo = is_bopomofo(char)
            if state.is_composition_mode():
                state.add_char_to_current(char)
                state.add_composition_char(char)
                if state.is_composition_complete():
                    state.flush_current_char()
                    state.switch_to_normal_mode()
            elif state.is_normal_mode():
                hyphen_match = self._hyphen_pattern.match(sentence[index:])
                if hyphen_match:
                    state.flush_current_char()
                    hyphen_length = len(hyphen_match.group(0))
                    if hyphen_length == 1:
                        if not state.has_data() or previous_was_whitespace:
                            state.add_direct_char(CONNECT_SYMBOL)
                            state.mark_word_boundary()
                        else:
                            state.mark_same_word()
                            is_hyphen = True
                            state.mark_has_hyphen()
                    elif hyphen_length == 2:
                        is_neutral_tone_symbol = True
                        state.mark_neutral_tone_word()
                        if not previous_was_whitespace:
                            # hó --lah -> ['hó', '--lah']
                            # hó--lah -> ['hó--lah']
                            state.mark_same_word()
                    else:
                        for _ in range(hyphen_length):
                            state.add_direct_char(CONNECT_SYMBOL)
                            state.mark_word_boundary()
                    index += hyphen_length - 1
                elif self._whitespace_pattern.fullmatch(char):
                    state.flush_current_char()
                    state.mark_word_boundary()
                    if previous_was_hyphen or previous_was_neutral_tone_symbol:
                        state.add_direct_char(CONNECT_SYMBOL)
                        state.mark_word_boundary()
                    if previous_was_neutral_tone_symbol:
                        state.add_direct_char(CONNECT_SYMBOL)
                        state.mark_word_boundary()
                        state.add_direct_char(CONNECT_SYMBOL)
                        state.mark_word_boundary()
                    is_whitespace = True
                # 羅馬字接做伙
                elif is_roman(char):
                    # 頭前是羅馬字抑是輕聲、外來語的數字
                    # 「N1N1」、「g0v」濫做伙名詞，「sui2sui2」愛變做兩个字，予粗胚處理。
                    if (
                        not is_roman(previous_char) and
                        previous_char not in self._digit_chars
                    ):
                        # 頭前愛清掉
                        state.flush_current_char()
                        state.mark_word_boundary()
                    if previous_was_neutral_tone_symbol:
                        state.mark_current_as_neutral_tone()

                    state.add_char_to_current(char)
                # 數字
                elif char in self._digit_chars:
                    if (
                        previous_char not in self._digit_chars and
                        not is_roman(previous_char) and
                        not previous_was_bopomofo
                    ):
                        state.flush_current_char()
                        state.mark_word_boundary()
                    state.add_char_to_current(char)
                # 音標後壁可能有聲調符號 uainnˊ
                elif char in TONE_SYMBOL and is_roman(previous_char):
                    state.add_char_to_current(char)
                # 處理注音，輕聲、注音、空三个後壁會當接注音
                elif is_char_bopomofo:
                    if (
                        previous_char not in TONE_SYMBOL and
                        not previous_was_bopomofo
                    ):
                        state.flush_current_char()
                    state.add_char_to_current(char)
                # 注音後壁會當接聲調
                elif char in TONE_SYMBOL and previous_was_bopomofo:
                    state.add_char_to_current(char)

                elif char in PUNC:
                    multi_punct_match = self._multi_char_punctuation.match(sentence[index:])
                    if char == '•' and state.ends_with_o_sound():
                        state.add_char_to_current(char)
                    elif multi_punct_match:
                        symbol = multi_punct_match.group(0)
                        state.flush_current_char()
                        state.mark_word_boundary()
                        state.add_direct_char(symbol)
                        state.mark_word_boundary()
                        index += len(symbol) - 1
                    else:
                        state.flush_current_char()
                        state.mark_word_boundary()
                        state.add_direct_char(char)
                        state.mark_word_boundary()
                else:
                    if state.current_is_all_digits():
                        state.flush_current_char()
                        state.mark_word_boundary()
                    elif is_roman(previous_char):
                        state.flush_current_char()
                        state.mark_word_boundary()
                    else:
                        state.flush_current_char()
                    if previous_was_neutral_tone_symbol:
                        state.mark_current_as_neutral_tone()

                    state.add_char_to_current(char)

                    if char in COMPOSITION_SYMBOL:
                        state.switch_to_composition_mode()
                    else:
                        state.flush_current_char()
            index += 1
            previous_char = char
            previous_was_hyphen = is_hyphen
            previous_was_whitespace = is_whitespace
            previous_was_neutral_tone_symbol = is_neutral_tone_symbol
            previous_was_bopomofo = is_char_bopomofo
        if state.has_current_char():
            if state.is_normal_mode():
                state.flush_current_char()
            else:
                raise 解析錯誤('語句組字式無完整，語句＝{0}'.format(str(sentence)))
        if previous_was_hyphen:
            state.add_direct_char(CONNECT_SYMBOL)
            state.mark_word_boundary()
        if previous_was_neutral_tone_symbol:
            state.add_direct_char(CONNECT_SYMBOL)
            state.mark_word_boundary()
            state.add_direct_char(CONNECT_SYMBOL)
            state.mark_word_boundary()
        return state.result()

    class _ParserState:

        def __init__(self):
            self._char_list = []
            self._neutral_tone_flags = []
            self._word_boundary_flags = []
            self.switch_to_normal_mode()
            # 組字式抑是數羅會超過一个字元
            self._current_char = ''
            self._current_is_neutral_tone = False
            self._inside_neutral_tone_word = False
            self._neutral_tone_word_continues = False

        def result(self):
            return self._char_list, self._neutral_tone_flags, self._word_boundary_flags

        def has_data(self):
            return len(self._char_list) > 0 or self.has_current_char()

        def has_current_char(self):
            return self._current_char != ''

        def current_is_all_digits(self):
            return self._current_char.isdigit()

        def switch_to_normal_mode(self):
            self._mode = 'normal'
            self._composition_length = 0

        def switch_to_composition_mode(self):
            self._mode = 'composition'
            self._composition_length = -1

        def is_normal_mode(self):
            return self._mode == 'normal'

        def is_composition_mode(self):
            return self._mode == 'composition'

        def add_composition_char(self, char):
            if char in COMPOSITION_SYMBOL:
                self._composition_length -= 1
            else:
                self._composition_length += 1

        def is_composition_complete(self):
            return self._composition_length == 1

        def add_char_to_current(self, char):
            self._current_char += char

        def mark_current_as_neutral_tone(self):
            self._current_is_neutral_tone = True

        def mark_neutral_tone_word(self):
            self._inside_neutral_tone_word = True
            self._neutral_tone_word_continues = True

        def mark_has_hyphen(self):
            if self._inside_neutral_tone_word:
                self._neutral_tone_word_continues = True

        def add_direct_char(self, char):
            self._char_list.append(char)
            self._neutral_tone_flags.append(False)
            self._word_boundary_flags.append(None)

        def flush_current_char(self):
            if self._current_char != '':
                if self._inside_neutral_tone_word:
                    if not self._neutral_tone_word_continues:
                        self.mark_word_boundary()
                        self._inside_neutral_tone_word = False
                    self._neutral_tone_word_continues = False

                self._char_list.append(self._current_char)
                self._neutral_tone_flags.append(self._current_is_neutral_tone)
                self._word_boundary_flags.append(None)
                self._current_char = ''
                self._current_is_neutral_tone = False

        def mark_same_word(self):
            try:
                self._word_boundary_flags[-1] = False
            except IndexError:
                pass

        def mark_word_boundary(self):
            try:
                if self._word_boundary_flags[-1] is None:
                    self._word_boundary_flags[-1] = True
            except IndexError:
                pass

        def ends_with_o_sound(self):
            for o in ['o', 'ó', 'ò', 'ô', 'ǒ', 'ō', 'o̍', 'ő']:
                if self._current_char.endswith(o):
                    return True
            return False


class 解析錯誤(Exception):
    pass


class TuiBeTse(ValueError):
    pass
