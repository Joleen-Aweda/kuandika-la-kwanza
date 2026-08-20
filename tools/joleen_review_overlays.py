"""Exact-font overlay locations for the Joleen review corrections."""

from __future__ import annotations

from apply_instruction_expansions import (
    EXPANSIONS,
    VIDEO_CAPITAL_CONSONANTS,
    VIDEO_IRABU,
    VIDEO_SMALL_CONSONANTS,
    write_instruction,
)


LINE_NAMES = ("firstLine", "secondLine", "thirdLine", "fourthLine", "fifthLine", "sixthLine")


def chunks(value: str, count: int) -> list[str]:
    words = value.split()
    result: list[str] = []
    start = 0
    for remaining in range(count, 0, -1):
        end = len(words) if remaining == 1 else start + round((len(words) - start) / remaining)
        result.append(" ".join(words[start:end]))
        start = end
    return result


def correction(
    text_id: str,
    rect_y: int,
    *,
    line_count: int = 2,
    rect_x: int = 100,
    rect_width: int = 730,
    text_x: int = 110,
    first_line_y: int | None = None,
    gap: int | None = None,
    layout_offset: int | None = None,
    fill: tuple[int, int, int, int] | None = None,
    align: str | None = None,
) -> dict:
    value = EXPANSIONS[text_id][1]
    return positioned(
        value,
        rect_y,
        line_count=line_count,
        rect_x=rect_x,
        rect_width=rect_width,
        text_x=text_x,
        first_line_y=first_line_y,
        gap=gap,
        layout_offset=layout_offset,
        fill=fill,
        align=align,
    )


def positioned(
    value: str,
    rect_y: int,
    *,
    line_count: int = 2,
    rect_x: int = 100,
    rect_width: int = 730,
    text_x: int = 110,
    first_line_y: int | None = None,
    gap: int | None = None,
    layout_offset: int | None = None,
    fill: tuple[int, int, int, int] | None = None,
    align: str | None = None,
) -> dict:
    values = chunks(value, line_count)
    result = {
        "rectX": rect_x,
        "rectY": rect_y,
        "rectWidth": rect_width,
        "firstLineY": first_line_y if first_line_y is not None else rect_y + 28,
        "height": (line_count * 27) + 5,
        "textX": text_x,
        "gap": gap if gap is not None else max(0, (line_count - 1) * 30),
    }
    for name, line in zip(LINE_NAMES, values):
        result[name] = line
    if layout_offset is not None:
        result["layoutOffset"] = layout_offset
    if fill is not None:
        result["fill"] = list(fill)
    if align is not None:
        result["textAlign"] = align
    return result


WHITE = (255, 255, 255, 255)
EXERCISE_YELLOW = (255, 253, 217, 255)


OVERLAY_POSITIONS: dict[str, list[dict] | dict] = {
    "6": [
        positioned("1. Kumudu misingi ya kuandika;", 548, line_count=1, rect_x=110, rect_width=560, text_x=119, first_line_y=578, gap=0),
        positioned("2. Kumudu stadi za kuandika; na", 588, line_count=1, rect_x=110, rect_width=580, text_x=119, first_line_y=618, gap=0),
        positioned("3. Kutumia kanuni za uandishi.", 628, line_count=1, rect_x=110, rect_width=560, text_x=119, first_line_y=658, gap=0),
        correction("pg006_n0016", 665, line_count=1, rect_x=110, rect_width=650, text_x=119, first_line_y=695, gap=0),
    ],
    "7": correction("pg007_n0008", 489, line_count=2, rect_x=110, rect_width=710, text_x=120, first_line_y=517, gap=30),
    "8": correction("pg008_n0005", 292, line_count=2, rect_x=110, rect_width=700, text_x=119, first_line_y=321, gap=0),
    "9": correction("pg009_n0002", 132, line_count=2, rect_x=110, rect_width=700, text_x=120, first_line_y=160, gap=0),
    "10": [
        correction("pg010_n0005", 278, line_count=2, rect_x=110, rect_width=700, text_x=120, first_line_y=307, gap=30),
        correction("pg010_n0006", 700, line_count=2, rect_x=110, rect_width=720, text_x=120, first_line_y=729, gap=30),
    ],
    "11": [correction("pg011_n0014", 604, line_count=2), correction("pg011_n0016", 772, line_count=2), correction("pg011_n0028", 974, line_count=2)],
    "12": [correction("pg012_n0005", 281, line_count=2), correction("pg012_n0009", 452, line_count=2), correction("pg012_n0021", 648, line_count=2), correction("pg012_n0034", 989, line_count=2)],
    "13": [correction("pg013_n0007", 319, line_count=2), correction("pg013_n0028", 641, line_count=2), correction("pg013_n0018", 982, line_count=2)],
    "14": correction("pg014_n0006", 254, line_count=2),
    "16": positioned(VIDEO_IRABU, 220, line_count=6, rect_x=185, rect_width=420, text_x=195, first_line_y=252, gap=0, fill=WHITE, align="center"),
    "17": [correction("pg017_n0013", 615, line_count=2), correction("pg017_n0014", 792, line_count=2), correction("pg017_n0025", 976, line_count=2)],
    "19": [correction("pg019_n0008", 506, line_count=2), correction("pg019_n0010", 672, line_count=2)],
    "20": correction("pg020_n0030", 951, line_count=2),
    "21": [correction("pg021_n0002", 139, line_count=2), correction("pg021_n0008", 320, line_count=2)],
    "22": [correction("pg022_n0019", 817, line_count=2), correction("pg022_n0021", 981, line_count=2)],
    "23": correction("pg023_n0002", 136, line_count=2),
    "24": [correction("pg024_n0015", 577, line_count=2), correction("pg024_n0018", 746, line_count=2), correction("pg024_n0031", 937, line_count=3)],
    "27": [correction("pg027_n0008", 598, line_count=2), correction("pg027_n0009", 790, line_count=2), correction("pg027_n0018", 981, line_count=2)],
    "29": [correction("pg029_n0006", 285, line_count=2), correction("pg029_n0011", 451, line_count=2)],
    "30": correction("pg030_n0026", 953, line_count=2),
    "31": [correction("pg031_n0002", 137, line_count=2), correction("pg031_n0006", 324, line_count=2)],
    "32": correction("pg032_n0025", 978, line_count=2),
    "33": [correction("pg033_n0002", 137, line_count=2), correction("pg033_n0012", 331, line_count=2)],
    "34": [correction("pg034_n0020", 774, line_count=2), correction("pg034_n0031", 976, line_count=2)],
    "37": [correction("pg037_n0018", 517, line_count=2), correction("pg037_n0029", 676, line_count=2)],
    "39": [correction("pg039_n0005", 263, line_count=2), correction("pg039_n0018", 470, line_count=2)],
    "40": correction("pg040_n0032", 975, line_count=3),
    "41": correction("pg041_n0002", 134, line_count=3),
    "42": [correction("pg042_n0015", 588, line_count=2), correction("pg042_n0020", 780, line_count=2)],
    "44": [correction("pg044_n0005", 274, line_count=2), correction("pg044_n0011", 449, line_count=2)],
    "47": [correction("pg047_n0013", 602, line_count=2), correction("pg047_n0020", 794, line_count=2)],
    "49": [correction("pg049_n0006", 252, line_count=2), correction("pg049_n0009", 420, line_count=3), correction("pg049_n0023", 584, line_count=2)],
    "50": [correction("pg050_n0014", 675, line_count=2), correction("pg050_n0019", 831, line_count=2)],
    "52": [correction("pg052_n0005", 268, line_count=3), correction("pg052_n0013", 428, line_count=3)],
    "54": positioned(VIDEO_SMALL_CONSONANTS, 245, line_count=6, rect_x=365, rect_width=420, text_x=375, first_line_y=277, gap=0, fill=WHITE, align="center"),
    "55": [
        correction("pg055_n0007", 672, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya irabu", "A", 6, 1), 815, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa A ikifuatiwa na herufi ndogo a kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 987, line_count=2, layout_offset=90, gap=0),
    ],
    "57": [
        correction("pg057_n0005", 306, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya irabu", "E", 6, 1, 5), 447, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa E ikifuatiwa na herufi ndogo e kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 615, line_count=2, layout_offset=90, gap=0),
    ],
    "58": correction("pg058_n0018", 837, line_count=2),
    "60": [
        correction("pg060_n0004", 283, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya irabu", "O", 6, 1, 3, 5), 424, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa O ikifuatiwa na herufi ndogo o kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 590, line_count=2, layout_offset=90, gap=0),
    ],
    "61": [
        correction("pg061_n0023", 711, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya irabu", "U", 6, 1, 3, 6), 848, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa U ikifuatiwa na herufi ndogo u kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 1017, line_count=2, layout_offset=90, gap=0),
    ],
    "63": [
        correction("pg063_n0013", 682, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya konsonanti", "B", 6, 1, 2), 829, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa B ikifuatiwa na herufi ndogo b kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 999, line_count=2, layout_offset=90, gap=0),
    ],
    "65": [
        correction("pg065_n0005", 306, line_count=2, layout_offset=60, gap=0),
        positioned(write_instruction("ya konsonanti", "M", 6, 1, 3, 4), 438, line_count=2, layout_offset=90, gap=0),
        positioned("Andika herufi kubwa M ikifuatiwa na herufi ndogo m kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 605, line_count=2, layout_offset=90, gap=0),
    ],
    "66": [
        correction("pg066_n0032", 834, line_count=2, layout_offset=50, gap=0),
        positioned(write_instruction("ya konsonanti", "K", 6, 1, 3), 955, line_count=2, layout_offset=80, gap=0),
        positioned("Andika herufi kubwa K ikifuatiwa na herufi ndogo k kwa pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.", 1175, line_count=2, layout_offset=80, gap=0),
    ],
    "68": correction("pg068_n0005", 297, line_count=2),
    "69": correction("pg069_n0019", 940, line_count=2),
    "70": correction("pg070_n0002", 135, line_count=2),
    "72": correction("pg072_n0015", 544, line_count=2),
    "74": correction("pg074_n0005", 305, line_count=3),
    "75": correction("pg075_n0023", 990, line_count=3),
    "76": correction("pg076_n0002", 134, line_count=3),
    "77": [correction("pg077_n0013", 530, line_count=2), correction("pg077_n0017", 701, line_count=2)],
    "79": [correction("pg079_n0005", 287, line_count=2), correction("pg079_n0010", 448, line_count=2)],
    "81": [correction("pg081_n0013", 551, line_count=2), correction("pg081_n0023", 726, line_count=2)],
    "82": correction("pg082_n0029", 994, line_count=3),
    "83": correction("pg083_n0002", 136, line_count=3),
    "84": [correction("pg084_n0022", 716, line_count=3), correction("pg084_n0027", 895, line_count=3)],
    "86": [correction("pg086_n0006", 296, line_count=3), correction("pg086_n0011", 487, line_count=3)],
    "87": correction("pg087_n0016", 990, line_count=2),
    "88": correction("pg088_n0002", 133, line_count=2),
    "89": [
        positioned("Hamida amebeba mizigo ya bibi.", 247, line_count=1, rect_x=308, rect_width=500, text_x=315, first_line_y=278, gap=0, fill=EXERCISE_YELLOW),
        positioned("Hawa amepewa hela ya kununua kalamu.", 337, line_count=1, rect_x=210, rect_width=600, text_x=218, first_line_y=368, gap=0, fill=EXERCISE_YELLOW),
        positioned("Hasani na Halima wanapalilia miti.", 382, line_count=1, rect_x=210, rect_width=600, text_x=218, first_line_y=413, gap=0, fill=EXERCISE_YELLOW),
        positioned("Hadija amehamia Hedaru.", 427, line_count=1, rect_x=210, rect_width=560, text_x=218, first_line_y=458, gap=0, fill=EXERCISE_YELLOW),
        positioned("Hosea anawasaidia watoto wasioona", 470, line_count=1, rect_x=210, rect_width=600, text_x=218, first_line_y=501, gap=0, fill=EXERCISE_YELLOW),
        positioned("Haruna anavuna karafuu.", 558, line_count=1, rect_x=210, rect_width=560, text_x=218, first_line_y=589, gap=0, fill=EXERCISE_YELLOW),
    ],
    "90": [correction("pg090_n0012", 569, line_count=3), correction("pg090_n0022", 735, line_count=3)],
    "92": [correction("pg092_n0004", 291, line_count=3), correction("pg092_n0011", 491, line_count=3)],
    "93": correction("pg093_n0027", 989, line_count=3),
    "94": correction("pg094_n0002", 136, line_count=3),
    "95": [correction("pg095_n0021", 701, line_count=4, gap=120), correction("pg095_n0031", 879, line_count=4, gap=120)],
    "97": [
        positioned("Chiku atapika chakula siku ya", 242, line_count=1, rect_x=305, rect_width=500, text_x=315, first_line_y=273, gap=0, fill=EXERCISE_YELLOW),
        positioned("Chacha na Chipa wameua chatu.", 421, line_count=1, rect_x=190, rect_width=620, text_x=199, first_line_y=452, gap=0, fill=EXERCISE_YELLOW),
        positioned("Chuwa ananawa mikono kwa maji na sabuni.", 467, line_count=1, rect_x=190, rect_width=620, text_x=199, first_line_y=498, gap=0, fill=EXERCISE_YELLOW),
        positioned("Chichi anatoa elimu ya usalama barabarani.", 512, line_count=1, rect_x=190, rect_width=620, text_x=199, first_line_y=543, gap=0, fill=EXERCISE_YELLOW),
        positioned("Chaula anachota maji.", 557, line_count=1, rect_x=190, rect_width=520, text_x=199, first_line_y=588, gap=0, fill=EXERCISE_YELLOW),
        positioned("Chiza atafika jumatatu.", 594, line_count=1, rect_x=190, rect_width=520, text_x=199, first_line_y=633, gap=0, fill=EXERCISE_YELLOW),
        positioned(VIDEO_CAPITAL_CONSONANTS, 735, line_count=6, rect_x=380, rect_width=410, text_x=390, first_line_y=767, gap=0, fill=WHITE, align="center"),
    ],
    "98": [correction("pg098_n0016", 602, line_count=3, gap=90), correction("pg098_n0018", 781, line_count=3, gap=90)],
    "100": correction("pg100_n0022", 988, line_count=4, gap=120),
    "101": correction("pg101_n0002", 134, line_count=4, gap=120),
    "102": [correction("pg102_n0013", 654, line_count=3, gap=90), correction("pg102_n0015", 826, line_count=3, gap=90)],
    "104": [correction("pg104_n0028", 806, line_count=4, gap=120), correction("pg104_n0035", 985, line_count=4, gap=120)],
    "106": correction("pg106_n0031", 983, line_count=4, gap=120),
    "107": correction("pg107_n0002", 133, line_count=4, gap=120),
    "109": [correction("pg109_n0005", 225, line_count=3, gap=90), correction("pg109_n0011", 381, line_count=3, gap=90)],
    "111": [correction("pg111_n0003", 248, line_count=3, gap=90), correction("pg111_n0010", 400, line_count=3, gap=90)],
    "113": [correction("pg113_n0005", 280, line_count=3, gap=90), correction("pg113_n0011", 457, line_count=3, gap=90)],
}


BOLD_TOKENS = {
    page: [letter]
    for page, letter in {
        "11": "a", "12": "e", "13": "i", "17": "b", "19": "m",
        "21": "k", "22": "d", "23": "d", "24": "n", "27": "l",
        "29": "t", "31": "p", "33": "s", "34": "j", "37": "f",
        "39": "g", "40": "y", "41": "y", "42": "z", "44": "h",
        "47": "r", "49": "w", "50": "v", "52": "ch", "55": "A",
        "57": "E", "58": "I", "60": "O", "61": "U", "63": "B",
        "65": "M", "66": "K", "68": "D", "69": "N", "70": "N",
        "72": "L", "74": "T", "75": "P", "76": "P", "77": "S",
        "79": "J", "81": "F", "82": "G", "83": "G", "84": "Y",
        "86": "Z", "87": "H", "88": "H", "90": "R", "92": "W",
        "93": "V", "94": "V", "95": "CH", "98": "sh", "100": "th",
        "101": "th", "102": "mb", "104": "ny", "106": "ng", "107": "ng",
        "109": "nd", "111": "kw", "113": "mw",
    }.items()
}
