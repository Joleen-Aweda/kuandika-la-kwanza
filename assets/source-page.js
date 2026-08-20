(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var XHTML_NS = "http://www.w3.org/1999/xhtml";
  var SOURCE_CONTENT_TOP = 110;
  var SOURCE_CONTENT_BOTTOM = 1150;
  var SOURCE_PAGE_HEIGHT = 1280;
  var SOURCE_PDF_HEIGHT = 767.669;
  var CORRECTION_FONT_SIZE = 28;
  var CORRECTION_LINE_HEIGHT = 27;
  var CORRECTION_PAGES = [
    6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 20, 21, 22, 23, 24,
    27, 29, 30, 31, 32, 33, 34, 37, 39, 40, 41, 42, 44, 47, 49,
    50, 52, 54, 55, 57, 58, 60, 61, 63, 65, 66, 68, 69, 70, 72,
    74, 75, 76, 77, 79, 81, 82, 83, 84, 86, 87, 88, 89, 90, 92,
    93, 94, 95, 97, 98, 100, 101, 102, 104, 106, 107, 109, 111,
    113,
  ];
  var EXTENDED_CORRECTION_HEIGHTS = {
    55: 1200,
    57: 1200,
    60: 1200,
    61: 1200,
    63: 1200,
    65: 1200,
    66: 1250,
  };

  function pageNumberFromId(pageId) {
    var match = String(pageId || "").match(/^pg(\d{3})_/);
    return match ? Number(match[1]) : 0;
  }

  function createSvgElement(name, attributes) {
    var element = document.createElementNS(SVG_NS, name);
    Object.keys(attributes).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    return element;
  }

  function appendCorrectionText(element, value, boldTokens) {
    if (!boldTokens || !boldTokens.length) {
      element.textContent = value;
      return;
    }
    var escaped = boldTokens.map(function (token) {
      return token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    });
    var tokenPattern = new RegExp("\\b(" + escaped.join("|") + ")\\b", "g");
    value.split(tokenPattern).forEach(function (part) {
      if (!part) return;
      var span = document.createElementNS(XHTML_NS, "span");
      span.style.fontWeight = boldTokens.indexOf(part) >= 0 ? "700" : "400";
      span.textContent = part;
      element.appendChild(span);
    });
  }

  function addTocNumberOverlay(stage, pageNumber) {
    var rows = pageNumber === 3 ? [
      ["5", 260, 294, "#ffffff"],
      ["6", 331, 365, "#ffffff"],
      ["7", 432, 467, "#b6e0c7"],
      ["11", 542, 577, "#b6e0c7"],
      ["17", 641, 676, "#b6e0c7"],
      ["27", 739, 774, "#b6e0c7"],
      ["37", 846, 881, "#b6e0c7"],
      ["47", 948, 983, "#b6e0c7"],
      ["55", 1048, 1083, "#b6e0c7"],
    ] : pageNumber === 4 ? [
      ["63", 172, 208, "#b6e0c7"],
      ["72", 282, 317, "#b6e0c7"],
      ["81", 391, 426, "#b6e0c7"],
      ["90", 500, 535, "#b6e0c7"],
      ["98", 650, 685, "#b6e0c7"],
      ["116", 782, 817, "#b6e0c7"],
    ] : [];
    if (!rows.length) return;

    var svg = createSvgElement("svg", {
      class: "toc-number-overlay",
      viewBox: "0 " + String(SOURCE_CONTENT_TOP) + " 930 " +
        String(SOURCE_CONTENT_BOTTOM - SOURCE_CONTENT_TOP),
      "aria-hidden": "true",
      focusable: "false",
    });
    rows.forEach(function (row) {
      svg.appendChild(createSvgElement("rect", {
        x: "755",
        y: String(row[1]),
        width: "58",
        height: "42",
        fill: row[3],
      }));
      var text = createSvgElement("text", {
        x: "802",
        y: String(row[2]),
        "text-anchor": "end",
        fill: "#231f20",
        "font-family": "Sassoon Primary Source, sans-serif",
        "font-size": "30",
        "font-weight": "400",
      });
      text.textContent = row[0];
      svg.appendChild(text);
    });
    stage.appendChild(svg);

    var targets = pageNumber === 3 ? [
      ["Shukurani, ukurasa wa 5", "pg005_sec001.html", 150, 184],
      ["Utangulizi, ukurasa wa 6", "pg006_sec001.html", 196, 230],
      ["Sura ya Kwanza, ukurasa wa 7", "pg007_sec001.html", 235, 286],
      ["Sura ya Pili, ukurasa wa 11", "pg011_sec001.html", 301, 351],
      ["Sura ya Tatu, ukurasa wa 17", "pg017_sec001.html", 360, 410],
      ["Sura ya Nne, ukurasa wa 27", "pg027_sec001.html", 419, 469],
      ["Sura ya Tano, ukurasa wa 37", "pg037_sec001.html", 483, 533],
      ["Sura ya Sita, ukurasa wa 47", "pg047_sec001.html", 544, 594],
      ["Sura ya Saba, ukurasa wa 55", "pg055_sec001.html", 604, 654],
    ] : [
      ["Sura ya Nane, ukurasa wa 63", "pg063_sec001.html", 79, 130],
      ["Sura ya Tisa, ukurasa wa 72", "pg072_sec001.html", 145, 196],
      ["Sura ya Kumi, ukurasa wa 81", "pg081_sec001.html", 210, 261],
      ["Sura ya Kumi na Moja, ukurasa wa 90", "pg090_sec001.html", 276, 327],
      ["Sura ya Kumi na Mbili, ukurasa wa 98", "pg098_sec001.html", 341, 417],
      ["Sura ya Kumi na Tatu, ukurasa wa 116", "pg116_sec001.html", 442, 496],
    ];
    var links = document.createElement("div");
    links.className = "toc-link-layer";
    targets.forEach(function (target) {
      var link = document.createElement("a");
      link.className = "toc-hotspot";
      link.href = target[1];
      link.setAttribute("aria-label", target[0]);
      var cropTopPoints = SOURCE_CONTENT_TOP / SOURCE_PAGE_HEIGHT * SOURCE_PDF_HEIGHT;
      var cropHeightPoints = (SOURCE_CONTENT_BOTTOM - SOURCE_CONTENT_TOP) /
        SOURCE_PAGE_HEIGHT * SOURCE_PDF_HEIGHT;
      link.style.top = ((target[2] - cropTopPoints) / cropHeightPoints * 100) + "%";
      link.style.height = ((target[3] - target[2]) / cropHeightPoints * 100) + "%";
      links.appendChild(link);
    });
    stage.appendChild(links);
  }

  function addVisibleTextCorrection(stage, pageNumber) {
    var boldTokensByPage = {
      11: ["a"],
      12: ["e"],
      13: ["i", "o"],
      21: ["k"],
      23: ["d"],
      24: ["n"],
      29: ["t"],
      31: ["p"],
      33: ["s"],
      34: ["j"],
      37: ["f"],
      39: ["G"],
      41: ["y"],
      42: ["Z"],
      44: ["h"],
      47: ["r"],
      49: ["w"],
      50: ["v"],
      52: ["ch"],
      55: ["A", "a"],
      57: ["E", "e"],
      60: ["O", "o"],
      61: ["U", "u"],
      63: ["B", "b"],
      65: ["M", "m"],
      66: ["K", "k"],
    };
    var positions = {
      6: [
        {
          rectX: 110,
          rectY: 548,
          rectWidth: 510,
          firstLineY: 578,
          height: 36,
          textX: 119,
          firstLine: "1. Kumudu misingi ya kuandika;",
        },
        {
          rectX: 110,
          rectY: 588,
          rectWidth: 560,
          firstLineY: 618,
          height: 36,
          textX: 119,
          firstLine: "2. Kumudu stadi za kuandika; na",
        },
        {
          rectX: 110,
          rectY: 628,
          rectWidth: 520,
          firstLineY: 658,
          height: 36,
          textX: 119,
          firstLine: "3. Kutumia kanuni za uandishi.",
        },
      ],
      8: {
        rectY: 292,
        firstLineY: 321,
        secondLineY: 348,
        height: 70,
        firstLine: "Fuatisha michoro hii /kwa kutumia spa willi",
        secondLine: "fuatisha michoro hii",
      },
      10: {
        rectY: 278,
        firstLineY: 307,
        secondLineY: 334,
        height: 68,
        firstLine: "Fuatisha michoro hii /kwa kutumia spa willi",
        secondLine: "fuatisha michoro hii",
      },
      11: {
        rectY: 974,
        firstLineY: 1002,
        secondLineY: 1029,
        height: 65,
        firstLine: "Andika herufi ya irabu a, Andika doti ya kwanza",
        secondLine: "kwa kurudiarudia na ujaze mstari",
      },
      12: {
        rectY: 648,
        firstLineY: 675,
        secondLineY: 701,
        height: 65,
        firstLine: "Andika herufi ya irabu e, Andika doti ya kwanza",
        secondLine: "na ya tano kwa nafasi na ujaze mstari",
      },
      13: [
        {
          rectY: 319,
          firstLineY: 346,
          secondLineY: 372,
          height: 60,
          firstLine: "Andika herufi ya irabu i, Andika doti ya pili",
          secondLine: "na ya nne kwa nafasi na ujaze mstari",
        },
        {
          rectY: 982,
          firstLineY: 1008,
          secondLineY: 1034,
          height: 60,
          firstLine: "Andika herufi ya irabu o; Andika doti ya kwanza,",
          secondLine: "ya tatu na ya tano kwa nafasi na ujaze mstari",
        },
      ],
      17: {
        rectY: 976,
        firstLineY: 1004,
        secondLineY: 1030,
        height: 65,
        firstLine: "Andika doti ya kwanza na ya pili kwa nafasi",
        secondLine: "na ujaze mstari",
      },
      21: {
        rectY: 320,
        firstLineY: 347,
        secondLineY: 372,
        height: 61,
        firstLine: "Andika herufi ya konsonanti k, Andika doti ya kwanza",
        secondLine: "na ya tatu kwa nafasi na ujaze mstari.",
      },
      23: {
        rectY: 136,
        firstLineY: 163,
        secondLineY: 188,
        height: 59,
        firstLine: "Andika herufi d, Andika doti ya kwanza, ya nne",
        secondLine: "na ya tano kwa nafasi na ujaze mstari.",
      },
      24: {
        rectY: 937,
        firstLineY: 964,
        secondLineY: 990,
        height: 64,
        firstLine: "Andika herufi ya konsonanti n, Andika doti ya kwanza,",
        secondLine: "ya tatu, ya nne na ya tano kwa nafasi na ujaze mstari.",
      },
      29: {
        rectY: 451,
        firstLineY: 476,
        secondLineY: 499,
        height: 56,
        firstLine: "Andika konsonanti t Andika doti ya pili, ya tatu,",
        secondLine: "ya nne na ya tano kwa nafasi na ujaze mstari.",
      },
      31: {
        rectY: 324,
        firstLineY: 350,
        secondLineY: 376,
        height: 63,
        firstLine: "Andika herufi ya konsonanti p, Andika doti ya kwanza,",
        secondLine: "ya pili, ya tatu na ya nne kwa nafasi na ujaze mstari.",
      },
      33: {
        rectY: 331,
        firstLineY: 357,
        secondLineY: 383,
        height: 63,
        firstLine: "Andika herufi ya konsonanti s, Andika doti ya pili,",
        secondLine: "ya tatu na ya nne kwa nafasi na ujaze mstari.",
      },
      34: {
        rectY: 976,
        firstLineY: 1002,
        secondLineY: 1029,
        height: 65,
        firstLine: "Andika herufi ya konsonanti j, Andika doti ya pili,",
        secondLine: "ya nne na ya tano kwa nafasi na ujaze mstari.",
      },
      37: {
        rectY: 676,
        firstLineY: 702,
        secondLineY: 726,
        height: 57,
        firstLine: "Andika herufi ya konsonanti f Andika doti ya kwanza,",
        secondLine: "ya pili na ya nne kwa nafasi na ujaze mstari",
      },
      39: {
        rectY: 470,
        firstLineY: 497,
        secondLineY: 523,
        height: 64,
        firstLine: "Andika herufi G, Andika doti ya kwanza, ya pili,",
        secondLine: "ya nne na ya tano kwa nafasi na ujaze mstari.",
      },
      41: {
        rectY: 134,
        firstLineY: 158,
        height: 78,
        firstLine: "Andika herufi ya konsonanti y, Andika doti ya kwanza,",
        secondLine: "ya tatu, ya nne, ya tano na ya sita kwa nafasi",
        thirdLine: "na ujaze mstari.",
      },
      42: {
        rectY: 780,
        firstLineY: 804,
        secondLineY: 828,
        height: 54,
        firstLine: "Andika herufi ya konsonanti Z, Andika doti ya kwanza,",
        secondLine: "ya tatu ya tano na sita kwa nafasi na ujaze mstari.",
      },
      44: {
        rectY: 449,
        firstLineY: 472,
        secondLineY: 493,
        height: 50,
        firstLine: "Andika herufi ya konsonanti h, Andika doti ya kwanza,",
        secondLine: "ya pili na ya tano kwa nafasi na ujaze mstari.",
      },
      47: {
        rectY: 794,
        firstLineY: 821,
        secondLineY: 847,
        height: 63,
        firstLine: "Andika herufi ya konsonanti r; Andika doti ya kwanza,",
        secondLine: "ya pili, ya tatu na ya tano na kwa nafasi na ujaze mstari.",
      },
      49: {
        rectY: 584,
        firstLineY: 607,
        secondLineY: 627,
        height: 47,
        firstLine: "Andika herufi ya konsonanti w, Andika doti ya pili,",
        secondLine: "ya nne, ya tano na ya sita kwa nafasi na ujaze mstari.",
      },
      50: {
        rectY: 831,
        firstLineY: 850,
        height: 53,
        firstLine: "Andika herufi ya konsonanti v; Andika doti ya kwanza,",
        secondLine: "ya pili, ya tatu na ya sita kwa nafasi na ujaze mstari.",
      },
      52: {
        rectY: 428,
        firstLineY: 450,
        height: 78,
        firstLine: "Andika herufi ya konsonanti ch; Andika doti ya kwanza na ya nne",
        secondLine: "na doti ya kwanza, ya pili na ya tano kwa nafasi",
        thirdLine: "na ujaze",
      },
      55: [
        {
          rectY: 815,
          firstLineY: 843,
          secondLineY: 870,
          height: 56,
          firstLine: "Andika herufi ya irabu A. Andika doti ya sita na ya kwanza",
          secondLine: "kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 987,
          firstLineY: 1015,
          secondLineY: 1042,
          height: 56,
          firstLine: "Andika herufi kubwa A ikifuatiwa na herufi ndogo a kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari",
        },
      ],
      57: [
        {
          rectY: 447,
          firstLineY: 475,
          secondLineY: 502,
          height: 56,
          firstLine: "Andika herufi ya irabu E, Andika doti ya sita, ya kwanza na ya tano",
          secondLine: "kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 615,
          firstLineY: 643,
          secondLineY: 670,
          height: 56,
          firstLine: "Andika herufi kubwa E ikifuatiwa na herufi ndogo e kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari",
        },
      ],
      60: [
        {
          rectY: 424,
          firstLineY: 452,
          secondLineY: 479,
          height: 56,
          firstLine: "Andika herufi ya irabu O, Andika doti ya sita, ya kwanza, ya tatu",
          secondLine: "na ya tano kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 590,
          firstLineY: 618,
          secondLineY: 645,
          height: 56,
          firstLine: "Andika herufi kubwa O ikifuatiwa na herufi ndogo o kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
        },
      ],
      61: [
        {
          rectY: 848,
          firstLineY: 876,
          secondLineY: 903,
          height: 56,
          firstLine: "Andika herufi ya irabu U, Andika doti ya sita, ya kwanza, ya tatu",
          secondLine: "na ya sita kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 1017,
          firstLineY: 1045,
          secondLineY: 1072,
          height: 56,
          firstLine: "Andika herufi kubwa U ikifuatiwa na herufi ndogo u kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
        },
      ],
      63: [
        {
          rectY: 829,
          firstLineY: 857,
          secondLineY: 884,
          height: 56,
          firstLine: "Andika herufi ya konsonanti B, Andika doti sita, ya kwanza",
          secondLine: "na ya pili kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 999,
          firstLineY: 1027,
          secondLineY: 1054,
          height: 56,
          firstLine: "Andika herufi kubwa B ikifuatiwa na herufi ndogo b kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
        },
      ],
      65: [
        {
          rectY: 438,
          firstLineY: 466,
          secondLineY: 493,
          height: 56,
          firstLine: "Andika herufi ya konsonanti M, Andika doti ya sita, ya kwanza, ya tatu",
          secondLine: "na ya nne kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 605,
          firstLineY: 633,
          secondLineY: 660,
          height: 56,
          firstLine: "Andika herufi kubwa M ikifuatiwa na herufi ndogo m kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
        },
      ],
      66: [
        {
          rectY: 955,
          firstLineY: 983,
          secondLineY: 1010,
          height: 56,
          firstLine: "Andika herufi ya konsonanti K, Andika doti ya sita, ya kwanza",
          secondLine: "na ya tatu kwa nafasi na ujaze mstari.",
        },
        {
          rectY: 1175,
          firstLineY: 1203,
          secondLineY: 1230,
          height: 56,
          firstLine: "Andika herufi kubwa K ikifuatiwa na herufi ndogo k kwa pamoja",
          secondLine: "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
        },
      ],
      89: [
        {
          rectX: 308,
          rectY: 247,
          rectWidth: 500,
          firstLineY: 278,
          height: 36,
          textX: 315,
          firstLine: "Hamida amebeba mizigo ya bibi.",
        },
        {
          rectX: 210,
          rectY: 337,
          rectWidth: 600,
          firstLineY: 368,
          height: 36,
          textX: 218,
          firstLine: "Hawa amepewa hela ya kununua kalamu.",
        },
        {
          rectX: 210,
          rectY: 382,
          rectWidth: 600,
          firstLineY: 413,
          height: 36,
          textX: 218,
          firstLine: "Hasani na Halima wanapalilia miti.",
        },
        {
          rectX: 210,
          rectY: 427,
          rectWidth: 560,
          firstLineY: 458,
          height: 36,
          textX: 218,
          firstLine: "Hadija amehamia Hedaru.",
        },
        {
          rectX: 210,
          rectY: 470,
          rectWidth: 600,
          firstLineY: 501,
          height: 36,
          textX: 218,
          firstLine: "Hosea anawasaidia watoto wasioona",
        },
        {
          rectX: 210,
          rectY: 558,
          rectWidth: 560,
          firstLineY: 589,
          height: 36,
          textX: 218,
          firstLine: "Haruna anavuna karafuu.",
        },
      ],
      97: [
        {
          rectX: 305,
          rectY: 242,
          rectWidth: 500,
          firstLineY: 273,
          height: 36,
          textX: 315,
          firstLine: "Chiku atapika chakula siku ya",
        },
        {
          rectX: 190,
          rectY: 421,
          rectWidth: 620,
          firstLineY: 452,
          height: 36,
          textX: 199,
          firstLine: "Chacha na Chipa wameua chatu.",
        },
        {
          rectX: 190,
          rectY: 467,
          rectWidth: 620,
          firstLineY: 498,
          height: 36,
          textX: 199,
          firstLine: "Chuwa ananawa mikono kwa maji na sabuni.",
        },
        {
          rectX: 190,
          rectY: 512,
          rectWidth: 620,
          firstLineY: 543,
          height: 36,
          textX: 199,
          firstLine: "Chichi anatoa elimu ya usalama barabarani.",
        },
        {
          rectX: 190,
          rectY: 557,
          rectWidth: 520,
          firstLineY: 588,
          height: 36,
          textX: 199,
          firstLine: "Chaula anachota maji.",
        },
        {
          rectX: 190,
          rectY: 594,
          rectWidth: 520,
          firstLineY: 633,
          height: 44,
          textX: 199,
          firstLine: "Chiza atafika jumatatu.",
        },
      ],
    };
    if (CORRECTION_PAGES.indexOf(pageNumber) < 0) return;

    var overlay = document.createElement("img");
    overlay.className = "source-text-correction-image";
    overlay.addEventListener("load", function () {
      if (overlay.naturalWidth && overlay.naturalHeight) {
        stage.style.aspectRatio = overlay.naturalWidth + " / " + overlay.naturalHeight;
      }
    }, { once: true });
    overlay.src = "images/corrections/pg" + String(pageNumber).padStart(3, "0") + ".png?v=18";
    overlay.alt = "";
    overlay.setAttribute("aria-hidden", "true");
    overlay.draggable = false;
    stage.appendChild(overlay);
  }

  function initialise() {
    var image = document.querySelector(".source-facsimile-page");
    var section = document.querySelector("[data-section-id]");
    if (!image || !section || image.dataset.exactPageReady === "true") return;
    image.dataset.exactPageReady = "true";
    image.draggable = false;

    var pageId = section.getAttribute("data-section-id") || "page";
    var pageNumber = pageNumberFromId(pageId);
    var content = image.closest("#content") || image.parentElement;
    content.classList.add("exact-facsimile-content");

    var stage = document.createElement("div");
    stage.className = "exact-page-stage source-page-cropped";
    if (EXTENDED_CORRECTION_HEIGHTS[pageNumber]) {
      stage.style.aspectRatio = "930 / " + EXTENDED_CORRECTION_HEIGHTS[pageNumber];
    }
    image.parentElement.insertBefore(stage, image);
    stage.appendChild(image);
    addTocNumberOverlay(stage, pageNumber);
    addVisibleTextCorrection(stage, pageNumber);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();
