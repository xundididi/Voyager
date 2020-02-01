import random
import string
import re
import difflib

from difflib import SequenceMatcher

from app.lib.thirdparty.wafcheck.config import DYNAMICITY_BOUNDARY_LENGTH
from app.lib.thirdparty.wafcheck.config import UPPER_RATIO_BOUND


def randomInt(length=4):
    """
    Returns random integer value with provided number of digits

    >>> randomInt(6)
    963638
    """

    choice = random.choice

    return int("".join(choice(string.digits if _ != 0 else string.digits.replace('0', '')) for _ in range(0, length)))


def randomStr(length=4, lowercase=False, alphabet=None):
    """
    Returns random string value with provided number of characters

    >>> randomStr(6)
    'FUPGpY'
    """

    choice = random.choice

    if alphabet:
        retVal = "".join(choice(alphabet) for _ in range(0, length))
    elif lowercase:
        retVal = "".join(choice(string.ascii_lowercase) for _ in range(0, length))
    else:
        retVal = "".join(choice(string.ascii_letters) for _ in range(0, length))

    return retVal


def removeReflectiveValues(content, payload):
    """
     简单粗暴的消除返回文本中有请求参数的函数
    """

    if payload in content:
        new_content = content.replace(payload)

        return new_content
    else:
        return content


def trimAlphaNum(value):
    """
    Trims alpha numeric characters from start and ending of a given value

    >>> trimAlphaNum('AND 1>(2+3)-- foobar')
    ' 1>(2+3)-- '
    """

    while value and value[-1].isalnum():
        value = value[:-1]

    while value and value[0].isalnum():
        value = value[1:]

    return value


def findDynamicContent(firstPage, secondPage):
    """
    This function checks if the provided pages have dynamic content. If they
    are dynamic, proper markings will be made

    >>> findDynamicContent("Lorem ipsum dolor sit amet, congue tation referrentur ei sed. Ne nec legimus habemus recusabo, natum reque et per. Facer tritani reprehendunt eos id, modus constituam est te. Usu sumo indoctum ad, pri paulo molestiae complectitur no.", "Lorem ipsum dolor sit amet, congue tation referrentur ei sed. Ne nec legimus habemus recusabo, natum reque et per. <script src='ads.js'></script>Facer tritani reprehendunt eos id, modus constituam est te. Usu sumo indoctum ad, pri paulo molestiae complectitur no.")
    >>> dynamicMarkings
    [('natum reque et per. ', 'Facer tritani repreh')]
    """

    if not firstPage or not secondPage:
        return

    # infoMsg = "searching for dynamic content"
    # singleTimeLogMessage(infoMsg)

    blocks = list(SequenceMatcher(None, firstPage, secondPage).get_matching_blocks())
    dynamicMarkings = []

    # Removing too small matching blocks
    for block in blocks[:]:
        (_, _, length) = block

        if length <= 2 * DYNAMICITY_BOUNDARY_LENGTH:
            blocks.remove(block)

    # Making of dynamic markings based on prefix/suffix principle
    if len(blocks) > 0:
        blocks.insert(0, None)
        blocks.append(None)

        for i in range(len(blocks) - 1):
            prefix = firstPage[blocks[i][0]:blocks[i][0] + blocks[i][2]] if blocks[i] else None
            suffix = firstPage[blocks[i + 1][0]:blocks[i + 1][0] + blocks[i + 1][2]] if blocks[i + 1] else None

            if prefix is None and blocks[i + 1][0] == 0:
                continue

            if suffix is None and (blocks[i][0] + blocks[i][2] >= len(firstPage)):
                continue

            if prefix and suffix:
                prefix = prefix[-DYNAMICITY_BOUNDARY_LENGTH:]
                suffix = suffix[:DYNAMICITY_BOUNDARY_LENGTH]

                for _ in (firstPage, secondPage):
                    match = re.search(r"(?s)%s(.+)%s" % (re.escape(prefix), re.escape(suffix)), _)
                    if match:
                        infix = match.group(1)
                        if infix[0].isalnum():
                            prefix = trimAlphaNum(prefix)
                        if infix[-1].isalnum():
                            suffix = trimAlphaNum(suffix)
                        break

            dynamicMarkings.append((prefix if prefix else None, suffix if suffix else None))

    return dynamicMarkings


def removeDynamicContent(page, dynamicMarkings):
    """
    Removing dynamic content from supplied page basing removal on
    precalculated dynamic markings
    """

    if page:
        for item in dynamicMarkings:

            prefix, suffix = item

            if prefix is None and suffix is None:
                continue
            elif prefix is None:
                page = re.sub(r"(?s)^.+%s" % re.escape(suffix), suffix.replace('\\', r'\\'), page)
            elif suffix is None:
                page = re.sub(r"(?s)%s.+$" % re.escape(prefix), prefix.replace('\\', r'\\'), page)
            else:
                page = re.sub(r"(?s)%s.+%s" % (re.escape(prefix), re.escape(suffix)),
                              "%s%s" % (prefix.replace('\\', r'\\'), suffix.replace('\\', r'\\')), page)

    return page


def _comparison(first_page, second_page):
    seqMatcher = difflib.SequenceMatcher(None)

    seqMatcher.set_seq1(first_page)
    seqMatcher.set_seq2(second_page)

    ratio = round(seqMatcher.quick_ratio(), 3)

    if ratio < UPPER_RATIO_BOUND:
        return False

    else:
        return True
