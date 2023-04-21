"""این ماژول شامل کلاس‌ها و توابعی برای تجزیهٔ متن به عبارات اسمی، فعلی و حرف
اضافه‌ای است. **میزان دقت تجزیه‌گر سطحی در نسخهٔ حاضر ۸۹.۹ درصد [^1] است.**
[^1]:
این عدد با انتشار هر نسخه بروزرسانی می‌شود.

"""
from typing import Iterator

import nltk.tree.tree
import nltk.chunk.util
from nltk.chunk import ChunkParserI
from nltk.chunk import RegexpParser
from nltk.chunk import conlltags2tree
from nltk.chunk import tree2conlltags

from .SequenceTagger import IOBTagger


def tree2brackets(tree: type[nltk.tree.tree.Tree]) -> str:
    """خروجی درختی تابع [parse()][hazm.Chunker.Chunker.parse] را به یک ساختار
    کروشه‌ای تبدیل می‌کند.

    Examples:
        >>> chunker = Chunker(model='resources/chunker.model')
        >>> tree=chunker.parse([('نامه', 'Ne'), ('ایشان', 'PRO'), ('را', 'POSTP'), ('دریافت', 'N'), ('داشتم', 'V'), ('.', 'PUNC')])
        >>> print(tree)
        (S
          (NP نامه/Ne ایشان/PRO)
          (POSTP را/POSTP)
          (VP دریافت/N داشتم/V)
          ./PUNC)
        >>> tree2brackets(tree)
        '[نامه ایشان NP] [را POSTP] [دریافت داشتم VP] .'

    Args:
        tree: ساختار درختی حاصل از پردزاش تابع parse().

    Returns:
        رشته‌ای از کروشه‌ها که در هر کروشه جزئی از متن به همراه نوع آن جای گرفته است.

    """
    str, tag = "", ""
    for item in tree2conlltags(tree):
        if item[2][0] in {"B", "O"} and tag:
            str += tag + "] "
            tag = ""

        if item[2][0] == "B":
            tag = item[2].split("-")[1]
            str += "["
        str += item[0] + " "

    if tag:
        str += tag + "] "

    return str.strip()


class Chunker(IOBTagger, ChunkParserI):
    """این کلاس شامل توابعی برای تقطیع متن، آموزش و ارزیابی مدل است."""

    def train(self, trees: list[type[nltk.tree.tree.Tree]]) -> None:
        """از روی درخت ورودی، مدل را آموزش می‌دهد.

        Args:
            trees: لیستی از درخت‌ها برای آموزش مدل.

        """
        super().train(list(map(tree2conlltags, trees)))

    def parse(self, sentence: list[tuple[str, str]]) -> str:
        """جمله‌ای را در قالب لیستی از تاپل‌های دوتایی [(توکن, نوع), (توکن, نوع), ...]
        دریافت می‌کند و درخت تقطع‌شدهٔ آن را بر می‌گرداند.

        Examples:
            >>> chunker = Chunker(model='resources/chunker.model')
            >>> tree=chunker.parse([('نامه', 'Ne'), ('ایشان', 'PRO'), ('را', 'POSTP'), ('دریافت', 'N'), ('داشتم', 'V'), ('.', 'PUNC')])
            >>> print(tree)
            (S
              (NP نامه/Ne ایشان/PRO)
              (POSTP را/POSTP)
              (VP دریافت/N داشتم/V)
              ./PUNC)

        Args:
            sentence: جمله‌ای که باید درخت تقطیع‌شدهٔ آن تولید شود.

        Returns:
            ساختار درختی حاصل از تقطیع.
            برای تبدیل این ساختار درختی به یک ساختار کروشه‌ای و قابل‌درک‌تر
            می‌توانید از تابع `tree2brackets()` استفاده کنید.

        """
        return next(self.parse_sents([sentence]))

    def parse_sents(self, sentences: list[list[tuple[str, str]]]) -> Iterator[str]:
        """جملات ورودی را به‌شکل تقطیع‌شده و در قالب یک برمی‌گرداند.

        Args:
            جملات ورودی.

        Yields:
            یک `Iterator` از جملات تقطیع شده.

        """
        for conlltagged in super().tag_sents(sentences):
            yield conlltags2tree(conlltagged)

    def evaluate(self, gold: list[str]) -> type[nltk.chunk.util.ChunkScore]:
        """دقت مدل را ارزیابی می‌کند.

        Args:
            gold: دادهٔ مرجع برای ارزیابی دقت مدل.

        Returns:
            دقت تشخیص.

        """
        return ChunkParserI.evaluate(self, gold)


class RuleBasedChunker(RegexpParser):
    """

    Examples:
        >>> chunker = RuleBasedChunker()
        >>> tree2brackets(chunker.parse([('نامه', 'Ne'), ('۱۰', 'NUMe'), ('فوریه', 'Ne'), ('شما', 'PRO'), ('را', 'POSTP'), ('دریافت', 'N'), ('داشتم', 'V'), ('.', 'PUNC')]))
        '[نامه ۱۰ فوریه شما NP] [را POSTP] [دریافت داشتم VP] .'

    """

    def __init__(self):
        grammar = r"""

            NP:
                <P>{<N>}<V>

            VP:
                <.*[^e]>{<N>?<V>}
                {<V>}

            ADVP:
                {<ADVe?><AJ>?}

            ADJP:
                <.*[^e]>{<AJe?>}

            NP:
                {<DETe?|Ne?|NUMe?|AJe|PRO|CL|RESe?><DETe?|Ne?|NUMe?|AJe?|PRO|CL|RESe?>*}
                <N>}{<.*e?>

            ADJP:
                {<AJe?>}

            POSTP:
                {<POSTP>}

            PP:
                {<Pe?>+}

        """

        super().__init__(grammar=grammar)
