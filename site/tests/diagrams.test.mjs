import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile, rm, copyFile, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { listNodes, readNodeField, validateDiagram } from 'oh-my-mermaid';
import puppeteer from 'puppeteer';
import { chromium } from '@playwright/test';
import { checkedSvg, compareSvg, generateDiagrams, loadCatalog, repository } from '../scripts/diagrams.mjs';

const hash = (text) => createHash('sha256').update(text).digest('hex');
const sample = '<svg id="literal" viewBox="0 0 100 50"><path d="M0,10L30,40" stroke="red"/><text x="5">state 10</text></svg>\n';

test('geometry tolerance preserves labels, styles, IDs, edge commands, and large movement', () => {
  const drift = compareSvg(sample, sample.replace('M0,10', 'M0.1,10.2'));
  assert(drift.equal);
  assert.deepEqual(drift.largestChanges[0], {
    element: 'path', id: null, tagOffset: sample.indexOf('<path'), attribute: 'd', component: 1,
    committed: 10, rendered: 10.2, delta: Math.abs(10 - 10.2),
  });
  for (const changed of [
    sample.replace('state 10', 'state 11'),
    sample.replace('red', 'blue'),
    sample.replace('literal', 'different'),
    sample.replace('M0,10L30,40', 'M0,10M30,40'),
    sample.replace('M0,10', 'M1,10'),
    sample.replace('<path', '<circle'),
  ]) assert.equal(compareSvg(sample, changed).equal, false);
  assert.equal(compareSvg(sample, sample.replace('M0,10', 'M0.1,10'), 0).equal, false);
});

test('fingerprint rejects source/config drift and generated payload edits', () => {
  const input = hash('source and config');
  const file = `<!-- jautomata-diagram input:${input} svg:${hash(sample)} -->\n${sample}`;
  assert.equal(checkedSvg(file, input), sample);
  assert.throws(() => checkedSvg(file, hash('new source')), /changed/);
  assert.throws(() => checkedSvg(file.replace('state 10', 'state 11'), input), /was edited/);
  assert.throws(() => checkedSvg(sample, input), /metadata is missing/);
});

test('coordinate tolerance never applies to similarly named attributes or style properties', () => {
  const svg = '<svg width="100" height="50" style="max-width: 100px; stroke-width: 1; --max-width: 100px" data-width="100" data-style="max-width: 100px"><path stroke-width="1"/><text>state 10</text></svg>';
  for (const [before, after] of [
    ['width="100"', 'width="100.1"'],
    ['height="50"', 'height="50.1"'],
    ['style="max-width: 100px', 'style="max-width: 100.1px'],
  ]) assert(compareSvg(svg, svg.replace(before, after)).equal, before);
  for (const [before, after] of [
    ['stroke-width="1"', 'stroke-width="1.2"'],
    ['stroke-width: 1', 'stroke-width: 1.2'],
    ['data-width="100"', 'data-width="100.1"'],
    ['data-style="max-width: 100px"', 'data-style="max-width: 100.1px"'],
    ['--max-width: 100px', '--max-width: 100.1px'],
    ['state 10', 'state 10.1'],
  ]) assert.equal(compareSvg(svg, svg.replace(before, after)).equal, false, before);
  for (const exact of [
    '<svg><text> width="1" </text></svg>',
    '<svg><style>.node { stroke-width: 1; }</style></svg>',
    '<svg data-label=\' width="1" \'/>',
    '<svg aria-label=" width=&quot;1&quot; "/>',
    '<svg><text><![CDATA[<node width="1">]]></text></svg>',
    '<svg><!-- <node width="1"> --></svg>',
  ]) assert.equal(compareSvg(exact, exact.replace('1', '1.2')).equal, false, exact);
});

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'jautomata-diagrams-'));
  const put = async (path, text) => { await mkdir(dirname(join(root, path)), { recursive: true }); await writeFile(join(root, path), text); };
  await mkdir(join(root, 'site/public/diagrams'), { recursive: true });
  await mkdir(join(root, '.omm'), { recursive: true });
  for (const path of ['.omm/renderer.json', 'site/package-lock.json']) {
    await mkdir(dirname(join(root, path)), { recursive: true });
    await copyFile(join(repository, path), join(root, path));
  }
  const figures = ['flow', 'sequence'].map((id) => ({
    id, source: `.omm/theory/${id}/diagram.mmd`, description: `.omm/theory/${id}/description.md`,
    asset: `site/public/diagrams/${id}.svg`, title: `${id} fixture`,
    provenance: [{ path: 'docs/fixture.md', note: 'Synthetic renderer regression fixture; not a lesson.' }],
    placements: [{ path: 'docs/fixture.md', alt: `${id} alternative` }],
  }));
  await put('.omm/manifest.json', JSON.stringify({ version: 1, figures }));
  await put('docs/fixture.md', figures.map((f) => `<img class="diagram" src="/JAutomata/diagrams/${f.id}.svg" alt="${f.id} alternative">`).join('\n'));
  await put(figures[0].source, 'flowchart LR\n  A((Start)) -->|ε| B(((Accept)))\n');
  await put(figures[1].source, 'sequenceDiagram\n  participant A as Evaluator\n  participant B as Worker\n  A->>B: Start\n  B-->>A: Result\n');
  for (const figure of figures) await put(figure.description, `${figure.title}: a static accessible test figure.`);
  return { root, figures, put, cleanup: () => rm(root, { recursive: true, force: true }) };
}

test('only generated neo solid-edge trim length shares the measured geometry bound', () => {
  const edge = '<svg><path class="edge-pattern-solid flowchart-link" data-edge="true" data-et="edge" data-look="neo" d="M0,0L104,0" style="stroke-dasharray: 0 0 100 4; stroke-dashoffset: 0;;"/><text>a</text></svg>';
  const shifted = edge.replace('0 0 100 4', '0 0 100.643 4');
  const result = compareSvg(edge, shifted);
  assert(result.equal);
  assert.equal(result.largestChanges[0].attribute, 'style:generated-solid-trim-length');
  assert.equal(compareSvg(edge, shifted, 0).equal, false);
  assert.equal(compareSvg(edge, edge.replace('0 0 100 4', '0 0 100.751 4')).equal, false);
  for (const [before, after] of [
    ['0 0 100 4', '0.1 0 100 4'], ['0 0 100 4', '0 0.1 100 4'],
    ['0 0 100 4', '0 0 100 4.1'], ['stroke-dashoffset: 0', 'stroke-dashoffset: 0.1'],
    ['<text>a', '<text>b'],
  ]) assert.equal(compareSvg(edge, edge.replace(before, after)).equal, false, before);
  for (const altered of [
    edge.replace('data-edge="true"', 'data-edge="false"'),
    edge.replace('data-et="edge"', 'data-et="node"'),
    edge.replace('data-look="neo"', 'data-look="classic"'),
    edge.replace('edge-pattern-solid', 'edge-pattern-dotted'),
    edge.replace('flowchart-link', 'custom-link'),
    edge.replace('flowchart-link', 'flowchart-link edge-animation-fast'),
    edge.replace('0;;', '0; stroke:red;'),
    edge.replace('stroke-dasharray: 0 0 100 4;', 'stroke-dasharray: 100 4;'),
  ]) assert.equal(compareSvg(altered, altered.replace('100 4', '100.1 4')).equal, false, altered);
});

test('embedded symbol glyphs use the bundled math font while covered glyphs retain Open Sans', { timeout: 120000 }, async () => {
  const { root, figures, put, cleanup } = await fixture();
  let browser;
  try {
    await put(figures[0].source, 'flowchart LR\n  A["∅ →"] -->|ε| B["A"]\n');
    await generateDiagrams({ root, log: () => {} });
    const svg = await readFile(join(root, figures[0].asset), 'utf8');
    assert.match(svg, /Noto Sans Math/);
    browser = await puppeteer.launch({ executablePath: chromium.executablePath(), headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', (request) => request.url().startsWith('data:') ? request.continue() : request.abort());
    await page.setContent(svg);
    await page.evaluate(async () => {
      const family = getComputedStyle(document.querySelector('svg text')).fontFamily;
      for (const glyph of ['∅', '→', 'ε', 'A']) {
        const probe = document.createElement('span');
        probe.className = 'font-probe';
        probe.style.cssText = `font-family: ${family}; font-size: 18px; font-weight: 400; display: block`;
        probe.textContent = glyph;
        document.body.append(probe);
      }
      await Promise.all([...document.fonts].map((font) => font.load()));
      await document.fonts.ready;
    });
    const client = await page.createCDPSession();
    await client.send('DOM.enable');
    await client.send('CSS.enable');
    const { root: documentNode } = await client.send('DOM.getDocument');
    const { nodeIds } = await client.send('DOM.querySelectorAll', { nodeId: documentNode.nodeId, selector: '.font-probe' });
    assert.equal(nodeIds.length, 4);
    for (const [index, nodeId] of nodeIds.entries()) {
      const { fonts } = await client.send('CSS.getPlatformFontsForNode', { nodeId });
      assert(fonts.length > 0);
      assert(fonts.every((font) => font.isCustomFont && font.familyName === (index < 2 ? 'Noto Sans Math' : 'Open Sans')), JSON.stringify(fonts));
    }
  } finally {
    await browser?.close();
    await cleanup();
  }
});

test('catalog enumerates nested OMM nodes and rejects omissions, duplicates, and incorrect placements', async () => {
  const { root, figures, put, cleanup } = await fixture();
  try {
    assert.equal((await loadCatalog(root)).figures.length, 2);
    assert.deepEqual(listNodes('theory', [], root), ['flow', 'sequence']);
    assert.match(readNodeField('theory', ['flow'], 'diagram', root), /flowchart LR/);
    await put('.omm/manifest.json', JSON.stringify({ version: 1, figures: [figures[0]] }));
    await assert.rejects(loadCatalog(root), /Every nested/);
    await put('.omm/manifest.json', JSON.stringify({ version: 1, figures: [figures[0], figures[0]] }));
    await assert.rejects(loadCatalog(root), /duplicate figure id/);
    await put('.omm/manifest.json', JSON.stringify({ version: 1, figures }));
    await put('docs/fixture.md', '<img src="/diagrams/flow.svg" alt="wrong">');
    await assert.rejects(loadCatalog(root), /missing img.diagram/);
  } finally { await cleanup(); }
});

test('real renderer produces repeatable accessible flowchart and sequence SVGs, then catches drift and invalid Mermaid', { timeout: 120000 }, async () => {
  const { root, figures, put, cleanup } = await fixture();
  const options = { root, log: () => {} };
  try {
    await generateDiagrams(options);
    const originals = await Promise.all(figures.map((figure) => readFile(join(root, figure.asset), 'utf8')));
    const first = await readFile(join(root, figures[0].asset), 'utf8');
    assert.match(first, /aria-labelledby="flow-title flow-description"/);
    assert.match(first, /<title id="flow-title">flow fixture<\/title>/);
    assert.match(first, /<desc id="flow-description">/);
    assert.match(first, /data:font\/woff2;base64,/);
    assert.doesNotMatch(first, /data-points=/);
    await generateDiagrams({ ...options, check: true, exact: true });
    // A clean checkout has no OMM history/cache or pre-existing output to reuse.
    for (const figure of figures) await rm(join(root, figure.asset));
    await generateDiagrams(options);
    for (const [index, figure] of figures.entries()) {
      const regenerated = await readFile(join(root, figure.asset), 'utf8');
      assert.equal(regenerated, originals[index], `${figure.id}: clean output regeneration must preserve bytes and IDs`);
      assert.match(regenerated, new RegExp(`aria-labelledby="${figure.id}-title ${figure.id}-description"`));
      assert.doesNotMatch(regenerated, /<(?:script|foreignObject)\b/);
    }
    await put(figures[0].source, 'flowchart LR\n  A((Changed)) -->|ε| B(((Accept)))\n');
    await assert.rejects(generateDiagrams({ ...options, check: true }), /changed; regenerate/);
    // OMM intentionally cannot validate sequence syntax. The actual renderer must reject it.
    await put(figures[1].source, 'sequenceDiagram\n  invalid ???\n');
    assert.equal((await loadCatalog(root)).figures.length, 2);
    await assert.rejects(generateDiagrams(options), /Parse error|Syntax error|Lexical error/);
    assert.equal(hash(await readFile(join(root, figures[0].asset), 'utf8')), hash(first), 'failed generation must not replace earlier assets');
    // Balanced brackets alone do not establish valid Mermaid grammar either.
    const invalidFlow = 'flowchart LR\n  A[Start] --> B[End]\n  invalid ???\n';
    assert.equal(validateDiagram(invalidFlow).valid, true);
    await put('.omm/manifest.json', JSON.stringify({ version: 1, figures: [figures[0]] }));
    await rm(join(root, '.omm/theory/sequence'), { recursive: true });
    await rm(join(root, figures[1].asset));
    await put(figures[0].source, invalidFlow);
    await assert.rejects(generateDiagrams(options), /Parse error|Syntax error|Lexical error/);
  } finally { await cleanup(); }
});

test('freshness checks collect all failures and write opt-in diagnostics outside the source tree', { timeout: 120000 }, async () => {
  const { root, figures, put, cleanup } = await fixture();
  const diagnosticsDirectory = await mkdtemp(join(tmpdir(), 'jautomata-diagram-diagnostics-'));
  const options = { root, log: () => {} };
  try {
    await assert.rejects(generateDiagrams({ ...options, check: true, diagnosticsDirectory: join(root, 'site/dist') }), /outside the repository/);
    await generateDiagrams(options);
    const originals = await Promise.all(figures.map((figure) => readFile(join(root, figure.asset), 'utf8')));
    const edits = originals.map((contents, index) => {
      const boundary = contents.indexOf('\n');
      const payload = contents.slice(boundary + 1);
      const changed = index === 0
        ? payload.replace(/viewBox="([^"]+)"/, (_, value) => {
          const coordinates = value.split(' ').map(Number);
          coordinates[0] += 2;
          return `viewBox="${coordinates.join(' ')}"`;
        })
        : payload.replace('Result', 'Changed result');
      assert.notEqual(changed, payload);
      return contents.slice(0, boundary).replace(/svg:[a-f0-9]{64}/, `svg:${hash(changed)}`) + '\n' + changed;
    });
    for (const [index, figure] of figures.entries()) await put(figure.asset, edits[index]);
    await assert.rejects(generateDiagrams({ ...options, check: true, diagnosticsDirectory }), /2\/2 diagram checks failed/);
    const report = JSON.parse(await readFile(join(diagnosticsDirectory, 'report.json'), 'utf8'));
    assert.equal(report.checked, 2);
    assert.equal(report.failed, 2);
    assert.equal(report.tolerance, 0.75);
    assert.equal(report.platform, process.platform);
    assert.match(report.browser, /Chrome|Chromium/);
    assert.deepEqual(report.results.map(({ id, kind }) => [id, kind]), [['flow', 'geometry'], ['sequence', 'structure']]);
    assert.equal(report.results[0].delta, 2);
    for (const [index, figure] of figures.entries()) {
      assert.equal(await readFile(join(root, figure.asset), 'utf8'), edits[index], 'checks must preserve canonical assets');
      assert.equal(await readFile(join(diagnosticsDirectory, `${figure.id}.committed.svg`), 'utf8'), edits[index]);
      assert.equal(await readFile(join(diagnosticsDirectory, `${figure.id}.rendered.svg`), 'utf8'), originals[index].slice(originals[index].indexOf('\n') + 1));
      await put(figure.asset, originals[index]);
    }
    await rm(diagnosticsDirectory, { recursive: true });
    await generateDiagrams({ ...options, check: true, exact: true, diagnosticsDirectory });
    assert.deepEqual(await readdir(diagnosticsDirectory), ['report.json'], 'passing figures do not create failure SVG pairs');
    assert.equal(JSON.parse(await readFile(join(diagnosticsDirectory, 'report.json'), 'utf8')).failed, 0);
  } finally {
    await cleanup();
    await rm(diagnosticsDirectory, { recursive: true, force: true });
  }
});
