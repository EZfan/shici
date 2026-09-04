#!/usr/bin/env node
// Preprocess chinese-poetry JSON files into samples.jsonl for the shici CLI.
//
// Output: one JSON object per poem line:
//   { author, title, line, dynasty, source }
//
// Dynasty labels: "唐" for Tang, "宋" for Song ci, "先秦" for Shijing.
//
// Usage:
//   node scripts/preprocess_poetry.js            # default paths
//   node scripts/preprocess_poetry.js --check    # only print stats, no write

'use strict';

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.resolve(__dirname);
const OUT_FILE = path.join(DATA_DIR, 'samples.jsonl');

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// Split a paragraph (couplet) into two lines. Chinese poetry typically
// has lines of 5 or 7 characters, with the two halves of a couplet
// separated by 。 or ， (also 「」, ？！ etc. as full-width punctuation).
// We use a permissive split: any full-width comma/period, or if none
// found, fall back to half-width comma.
function splitCouplet(paragraph) {
  if (typeof paragraph !== 'string' || !paragraph.length) return [];
  // Prefer a single separator; in the dataset a paragraph is one couplet
  // like "秦川雄帝宅，函谷壯皇居。" with a ，
  const m = paragraph.match(/^(.+?)[，。！？；：、]/);
  if (m) {
    const head = m[1].trim();
    const tail = paragraph.slice(m[0].length).replace(/[，。！？；：、「」『』\s]+$/g, '').trim();
    const out = [head];
    if (tail) out.push(tail);
    return out;
  }
  // No separator found — return as a single line
  return [paragraph.trim()];
}

function* emitLines(poem, dynasty, source) {
  const author = (poem.author || '佚名').trim();
  const title = (poem.title || poem.rhythmic || '').trim();
  const paragraphs = Array.isArray(poem.paragraphs) ? poem.paragraphs
                    : Array.isArray(poem.content)    ? poem.content
                    : [];
  for (const p of paragraphs) {
    for (const line of splitCouplet(p)) {
      if (!line) continue;
      yield { author, title, line, dynasty, source };
    }
  }
}

function* emitShijing(poem) {
  const title = (poem.title || '').trim();
  const chapter = (poem.chapter || '').trim();
  const section = (poem.section || '').trim();
  const author = `${chapter}·${section}` || '佚名';
  const paragraphs = Array.isArray(poem.content) ? poem.content : [];
  for (const p of paragraphs) {
    // Shijing paragraphs are often 4-line stanzas, e.g. "关关雎鸠，在河之洲。窈窕淑女，君子好逑。"
    // Split on 。 first, then on ， within each chunk.
    for (const sentence of p.split('。')) {
      const cleaned = sentence.replace(/^[，。、\s]+|[，。、\s]+$/g, '').trim();
      if (!cleaned) continue;
      yield {
        author,
        title: `${chapter}·${section}·${title}`.replace(/^·+/, '').replace(/·+/g, '·'),
        line: cleaned,
        dynasty: '先秦',
        source: 'shijing',
      };
    }
  }
}

function main() {
  const check = process.argv.includes('--check');

  const sources = [
    { file: path.join(DATA_DIR, 'tang', 'poet.tang.0.json'),     dynasty: '唐', tag: 'tang' },
    { file: path.join(DATA_DIR, 'tang', 'poet.tang.1000.json'),  dynasty: '唐', tag: 'tang' },
    { file: path.join(DATA_DIR, 'tang', 'poet.tang.3000.json'),  dynasty: '唐', tag: 'tang' },
    { file: path.join(DATA_DIR, 'song', 'ci.song.0.json'),       dynasty: '宋', tag: 'song' },
    { file: path.join(DATA_DIR, 'song', 'songci-300.json'),      dynasty: '宋', tag: 'song' },
    { file: path.join(DATA_DIR, 'shijing', 'shijing.json'),     dynasty: '先秦', tag: 'shijing' },
  ];

  let totalPoems = 0;
  let totalLines = 0;
  const authors = new Set();
  const perDynasty = { '唐': 0, '宋': 0, '先秦': 0 };
  const perSource = {};

  const out = fs.createWriteStream(OUT_FILE, { encoding: 'utf8' });
  for (const src of sources) {
    if (!fs.existsSync(src.file)) {
      console.warn(`skip (missing): ${src.file}`);
      continue;
    }
    const arr = loadJson(src.file);
    let nPoem = 0, nLine = 0;
    for (const poem of arr) {
      nPoem += 1;
      const gen = src.tag === 'shijing' ? emitShijing(poem) : emitLines(poem, src.dynasty, src.tag);
      for (const rec of gen) {
        authors.add(rec.author);
        perDynasty[rec.dynasty] = (perDynasty[rec.dynasty] || 0) + 1;
        nLine += 1;
        if (!check) out.write(JSON.stringify(rec) + '\n');
      }
    }
    perSource[src.tag] = { poems: nPoem, lines: nLine, file: path.relative(DATA_DIR, src.file) };
    totalPoems += nPoem;
    totalLines += nLine;
    console.log(`  ${src.tag.padEnd(8)} poems=${String(nPoem).padStart(5)} lines=${String(nLine).padStart(6)}  ${path.relative(DATA_DIR, src.file)}`);
  }
  out.end();

  console.log('\nTotals:');
  console.log(`  poems : ${totalPoems}`);
  console.log(`  lines : ${totalLines}`);
  console.log(`  authors: ${authors.size}`);
  console.log(`  per-dynasty: ${JSON.stringify(perDynasty)}`);
  console.log(`\nWrote ${check ? '(dry-run) ' : ''}${OUT_FILE}`);
}

main();
