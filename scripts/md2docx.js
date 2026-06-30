const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  WidthType,
  AlignmentType,
  BorderStyle,
  ShadingType,
  PageBreak,
  Header,
  Footer,
  PageNumber,
  NumberFormat,
  TabStopPosition,
  TabStopType,
  convertInchesToTwip,
  LevelFormat,
} = require("docx");

// ── Read the markdown file ──
const mdPath = path.resolve(__dirname, "..", "04_system_architecture_v1.md");
const mdContent = fs.readFileSync(mdPath, "utf-8");
const lines = mdContent.split("\n");

// ── Styling constants ──
const FONT = "Times New Roman";
const FONT_CODE = "Consolas";
const COLOR_PRIMARY = "1B4F72";
const COLOR_HEADING1 = "1A5276";
const COLOR_HEADING2 = "2471A3";
const COLOR_HEADING3 = "2E86C1";
const COLOR_CODE_BG = "F4F6F7";
const COLOR_TABLE_HEADER = "2C3E50";
const COLOR_TABLE_ALT = "F2F4F4";

// ── Helpers ──
function textRun(text, opts = {}) {
  return new TextRun({
    text,
    font: opts.font || FONT,
    size: opts.size || 24, // 12pt
    bold: opts.bold || false,
    italics: opts.italics || false,
    color: opts.color || "000000",
    ...(opts.extra || {}),
  });
}

function codeRun(text) {
  return new TextRun({
    text,
    font: FONT_CODE,
    size: 18, // 9pt
    color: "2C3E50",
  });
}

function emptyParagraph() {
  return new Paragraph({ children: [textRun("")], spacing: { after: 60 } });
}

// ── Parse inline formatting (bold, italic, code) ──
function parseInline(text) {
  const runs = [];
  // Simple regex-based inline parser
  const regex =
    /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`|~~(.+?)~~)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Text before match
    if (match.index > lastIndex) {
      runs.push(textRun(text.slice(lastIndex, match.index)));
    }
    if (match[2]) {
      // ***bold italic***
      runs.push(textRun(match[2], { bold: true, italics: true }));
    } else if (match[3]) {
      // **bold**
      runs.push(textRun(match[3], { bold: true }));
    } else if (match[4]) {
      // *italic*
      runs.push(textRun(match[4], { italics: true }));
    } else if (match[5]) {
      // `code`
      runs.push(
        new TextRun({
          text: match[5],
          font: FONT_CODE,
          size: 20,
          color: "C0392B",
          shading: {
            type: ShadingType.CLEAR,
            fill: "F9EBEA",
          },
        })
      );
    } else if (match[6]) {
      // ~~strikethrough~~
      runs.push(
        textRun(match[6], { extra: { strike: true }, color: "999999" })
      );
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    runs.push(textRun(text.slice(lastIndex)));
  }
  return runs.length ? runs : [textRun(text)];
}

// ── Parse a markdown table ──
function parseTable(tableLines) {
  const rows = tableLines
    .map((line) =>
      line
        .split("|")
        .map((c) => c.trim())
        .filter((c) => c.length > 0)
    )
    .filter((r) => r.length > 0);

  if (rows.length < 2) return null;

  // Check if second row is separator
  const isSeparator = rows[1].every((c) => /^[-:]+$/.test(c));
  const dataRows = isSeparator ? [rows[0], ...rows.slice(2)] : rows;
  const colCount = dataRows[0].length;

  const tableRows = dataRows.map((row, rowIdx) => {
    const isHeader = rowIdx === 0;
    const isAlt = rowIdx % 2 === 0 && rowIdx > 0;

    const cells = [];
    for (let i = 0; i < colCount; i++) {
      const cellText = row[i] || "";
      cells.push(
        new TableCell({
          children: [
            new Paragraph({
              children: parseInline(cellText),
              spacing: { before: 40, after: 40 },
              alignment: AlignmentType.LEFT,
            }),
          ],
          shading: {
            type: ShadingType.CLEAR,
            fill: isHeader
              ? COLOR_TABLE_HEADER
              : isAlt
              ? COLOR_TABLE_ALT
              : "FFFFFF",
          },
          verticalAlign: "center",
          ...(isHeader
            ? {
                children: [
                  new Paragraph({
                    children: [
                      textRun(cellText, {
                        bold: true,
                        color: "FFFFFF",
                        size: 22,
                      }),
                    ],
                    spacing: { before: 40, after: 40 },
                  }),
                ],
              }
            : {}),
        })
      );
    }

    return new TableRow({ children: cells });
  });

  return new Table({
    rows: tableRows,
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}

// ── Main document builder ──
function buildDocument() {
  const children = [];
  let i = 0;
  let inCodeBlock = false;
  let codeLines = [];

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // ── Code blocks ──
    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        // End code block
        inCodeBlock = false;
        // Add the code block as a shaded box
        const codeText = codeLines.join("\n");
        const codeParaLines = codeText.split("\n");
        for (const cl of codeParaLines) {
          children.push(
            new Paragraph({
              children: [codeRun(cl || " ")],
              spacing: { before: 0, after: 0, line: 260 },
              shading: {
                type: ShadingType.CLEAR,
                fill: COLOR_CODE_BG,
              },
              indent: { left: convertInchesToTwip(0.3) },
            })
          );
        }
        children.push(emptyParagraph());
        codeLines = [];
      } else {
        inCodeBlock = true;
        codeLines = [];
      }
      i++;
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      i++;
      continue;
    }

    // ── Horizontal rule ──
    if (/^---+$/.test(trimmed) || /^\*\*\*+$/.test(trimmed)) {
      children.push(
        new Paragraph({
          children: [],
          spacing: { before: 120, after: 120 },
          border: {
            bottom: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC" },
          },
        })
      );
      i++;
      continue;
    }

    // ── Empty lines ──
    if (trimmed === "") {
      i++;
      continue;
    }

    // ── Headings ──
    const h1Match = trimmed.match(/^#\s+(.+)/);
    const h2Match = trimmed.match(/^##\s+(.+)/);
    const h3Match = trimmed.match(/^###\s+(.+)/);
    const h4Match = trimmed.match(/^####\s+(.+)/);

    if (h1Match) {
      children.push(
        new Paragraph({
          children: [
            textRun(h1Match[1], {
              bold: true,
              size: 36,
              color: COLOR_HEADING1,
            }),
          ],
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 360, after: 200 },
        })
      );
      i++;
      continue;
    }

    if (h2Match) {
      children.push(
        new Paragraph({
          children: [
            textRun(h2Match[1], {
              bold: true,
              size: 30,
              color: COLOR_HEADING2,
            }),
          ],
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 300, after: 160 },
        })
      );
      i++;
      continue;
    }

    if (h3Match) {
      children.push(
        new Paragraph({
          children: [
            textRun(h3Match[1], {
              bold: true,
              size: 26,
              color: COLOR_HEADING3,
            }),
          ],
          heading: HeadingLevel.HEADING_3,
          spacing: { before: 240, after: 120 },
        })
      );
      i++;
      continue;
    }

    if (h4Match) {
      children.push(
        new Paragraph({
          children: [
            textRun(h4Match[1], { bold: true, size: 24, color: "34495E" }),
          ],
          heading: HeadingLevel.HEADING_4,
          spacing: { before: 200, after: 100 },
        })
      );
      i++;
      continue;
    }

    // ── Tables ──
    if (trimmed.startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      const table = parseTable(tableLines);
      if (table) {
        children.push(table);
        children.push(emptyParagraph());
      }
      continue;
    }

    // ── Blockquotes ──
    if (trimmed.startsWith(">")) {
      const quoteText = trimmed.replace(/^>\s*/, "");
      children.push(
        new Paragraph({
          children: parseInline(quoteText),
          spacing: { before: 60, after: 60 },
          indent: { left: convertInchesToTwip(0.4) },
          border: {
            left: { style: BorderStyle.SINGLE, size: 12, color: COLOR_PRIMARY },
          },
          shading: { type: ShadingType.CLEAR, fill: "EBF5FB" },
        })
      );
      i++;
      continue;
    }

    // ── Bullet lists ──
    if (/^[-*+]\s/.test(trimmed)) {
      const bulletText = trimmed.replace(/^[-*+]\s+/, "");
      children.push(
        new Paragraph({
          children: [textRun("•  "), ...parseInline(bulletText)],
          spacing: { before: 40, after: 40 },
          indent: { left: convertInchesToTwip(0.4) },
        })
      );
      i++;
      continue;
    }

    // ── Numbered lists ──
    const numMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
    if (numMatch) {
      children.push(
        new Paragraph({
          children: [
            textRun(`${numMatch[1]}. `, { bold: true }),
            ...parseInline(numMatch[2]),
          ],
          spacing: { before: 40, after: 40 },
          indent: { left: convertInchesToTwip(0.4) },
        })
      );
      i++;
      continue;
    }

    // ── Indented list items ──
    const indentMatch = line.match(/^(\s+)[-*+]\s+(.+)/);
    if (indentMatch) {
      const indentLevel = Math.floor(indentMatch[1].length / 2);
      children.push(
        new Paragraph({
          children: [textRun("  ◦  "), ...parseInline(indentMatch[2])],
          spacing: { before: 20, after: 20 },
          indent: {
            left: convertInchesToTwip(0.4 + indentLevel * 0.3),
          },
        })
      );
      i++;
      continue;
    }

    // ── Normal paragraph ──
    children.push(
      new Paragraph({
        children: parseInline(trimmed),
        spacing: { before: 60, after: 60, line: 360 },
        alignment: AlignmentType.JUSTIFIED,
      })
    );
    i++;
  }

  return children;
}

// ── Build and save the document ──
async function main() {
  console.log("Đang chuyển đổi markdown sang Word...");

  const docChildren = buildDocument();

  const doc = new Document({
    creator: "Đồ Án Tốt Nghiệp",
    title:
      "Thiết Kế Kiến Trúc Hệ Thống Sơ Bộ v1 - Hệ Thống Giám Sát Giao Thông Thông Minh",
    description: "System Architecture v1 - Smart Traffic Monitoring System",
    styles: {
      default: {
        document: {
          run: {
            font: FONT,
            size: 24,
          },
          paragraph: {
            spacing: { line: 360 },
          },
        },
        heading1: {
          run: {
            font: FONT,
            size: 36,
            bold: true,
            color: COLOR_HEADING1,
          },
          paragraph: {
            spacing: { before: 360, after: 200 },
          },
        },
        heading2: {
          run: {
            font: FONT,
            size: 30,
            bold: true,
            color: COLOR_HEADING2,
          },
          paragraph: {
            spacing: { before: 300, after: 160 },
          },
        },
        heading3: {
          run: {
            font: FONT,
            size: 26,
            bold: true,
            color: COLOR_HEADING3,
          },
          paragraph: {
            spacing: { before: 240, after: 120 },
          },
        },
      },
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1.2),
              right: convertInchesToTwip(1),
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                children: [
                  textRun(
                    "Đồ Án Tốt Nghiệp — Hệ Thống Giám Sát Giao Thông Thông Minh",
                    { size: 16, italics: true, color: "999999" }
                  ),
                ],
                alignment: AlignmentType.CENTER,
                border: {
                  bottom: {
                    style: BorderStyle.SINGLE,
                    size: 4,
                    color: "CCCCCC",
                  },
                },
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                children: [
                  textRun("Thiết kế kiến trúc hệ thống v1 — ", {
                    size: 16,
                    color: "999999",
                  }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    font: FONT,
                    size: 16,
                    color: "999999",
                  }),
                  textRun(" / ", { size: 16, color: "999999" }),
                  new TextRun({
                    children: [PageNumber.TOTAL_PAGES],
                    font: FONT,
                    size: 16,
                    color: "999999",
                  }),
                ],
                alignment: AlignmentType.CENTER,
              }),
            ],
          }),
        },
        children: docChildren,
      },
    ],
  });

  const outputPath = path.resolve(
    __dirname,
    "..",
    "04_system_architecture_v1.docx"
  );
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);

  console.log(`✅ Đã tạo file Word thành công: ${outputPath}`);
  console.log(`   Kích thước: ${(buffer.length / 1024).toFixed(1)} KB`);
}

main().catch(console.error);
