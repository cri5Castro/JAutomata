import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir, mkdir, rename, writeFile } from 'node:fs/promises';
import { dirname, join, resolve, relative, posix, sep, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateDiagram } from 'oh-my-mermaid';
import { renderMermaid } from '@mermaid-js/mermaid-cli';
import puppeteer from 'puppeteer';
import { chromium } from '@playwright/test';

const script = fileURLToPath(import.meta.url);
const mathFontCss = new URL('../../.omm/math-font.css', import.meta.url);
const mathFontFile = new URL(import.meta.resolve('@fontsource/noto-sans-math/files/noto-sans-math-latin-400-normal.woff2'));
export const repository = resolve(dirname(script), '../..');
const digest = (value) => createHash('sha256').update(value).digest('hex');
const text = (value) => typeof value === 'string' && value.trim().length > 0;
const read = (root, path) => readFile(join(root, path), 'utf8');

function checkedPath(path, prefix, suffix = '') {
  assert(text(path) && path.startsWith(prefix) && path.endsWith(suffix)
    && path === posix.normalize(path) && !path.includes('\\') && !path.includes('..'), `Invalid catalog path: ${path}`);
  return path;
}

async function sourcesBelow(root, directory = '.omm') {
  const paths = [];
  for (const item of await readdir(join(root, directory), { withFileTypes: true })) {
    const path = `${directory}/${item.name}`;
    assert(!item.isSymbolicLink(), `Catalog symlinks are not supported: ${path}`);
    if (item.isDirectory()) paths.push(...await sourcesBelow(root, path));
    else if (item.name.endsWith('.mmd')) paths.push(path);
  }
  return paths.sort();
}

/** The manifest is exhaustive even though OMM's default validate command is not recursive. */
export async function loadCatalog(root = repository) {
  const manifest = JSON.parse(await read(root, '.omm/manifest.json'));
  const config = JSON.parse(await read(root, '.omm/renderer.json'));
  assert.equal(manifest.version, 1, 'Unsupported diagram manifest version');
  assert(Array.isArray(manifest.figures), 'figures must be an array');
  assert(config.geometryTolerance >= 0 && config.geometryTolerance <= 0.75, 'Geometry tolerance must be 0–0.75 SVG units');
  const ids = new Set();
  const assets = new Set();
  const figures = [];
  for (const entry of manifest.figures) {
    assert(text(entry.id) && /^[a-z][a-z0-9-]*$/.test(entry.id) && !ids.has(entry.id), `Invalid or duplicate figure id: ${entry.id}`);
    ids.add(entry.id);
    checkedPath(entry.source, '.omm/', '/diagram.mmd');
    assert.equal(entry.description, `${posix.dirname(entry.source)}/description.md`, `${entry.id}: description must be adjacent to source`);
    checkedPath(entry.asset, 'site/public/diagrams/', '.svg');
    assert.equal(posix.dirname(entry.asset), 'site/public/diagrams', 'Assets must be directly inside site/public/diagrams');
    assert(!assets.has(entry.asset), `Duplicate asset: ${entry.asset}`);
    assets.add(entry.asset);
    assert(text(entry.title) && !entry.title.includes('\n'), `${entry.id}: provide a one-line title`);
    assert(Array.isArray(entry.provenance) && entry.provenance.length, `${entry.id}: provenance is required`);
    for (const origin of entry.provenance) {
      checkedPath(origin.path, '');
      assert(!origin.path.startsWith('/') && text(origin.note), `${entry.id}: provenance needs a repository path and note`);
      await read(root, origin.path);
    }
    assert(Array.isArray(entry.placements) && entry.placements.length, `${entry.id}: placements are required`);
    const placementPaths = new Set();
    for (const placement of entry.placements) {
      checkedPath(placement.path, 'docs/', '.md');
      assert(text(placement.alt) && !placementPaths.has(placement.path), `${entry.id}: each placement needs unique path and alt`);
      placementPaths.add(placement.path);
      const content = await read(root, placement.path);
      const url = `/JAutomata/diagrams/${posix.basename(entry.asset)}`;
      const images = content.match(/<img\b[^>]*>/g) ?? [];
      assert(images.some((image) => image.includes(`src="${url}"`)
        && image.includes(`alt="${escapeAttribute(placement.alt)}"`)
        && /class="[^"]*\bdiagram\b[^"]*"/.test(image)), `${entry.id}: missing img.diagram with catalog URL and alt in ${placement.path}`);
    }
    const source = await read(root, entry.source);
    const description = (await read(root, entry.description)).trim();
    assert(text(description), `${entry.id}: empty accessible description`);
    // Configuration lives in renderer.json; per-figure directives can silently change layout or security.
    assert(!/^\s*---/m.test(source) && !/%%\s*\{/.test(source), `${entry.id}: frontmatter/init directives are not supported`);
    const declaration = source.split('\n').map((line) => line.trim()).find((line) => line && !line.startsWith('%%'));
    assert(/^(flowchart|graph)\s+(LR|RL|TD|TB|BT)$|^sequenceDiagram$/.test(declaration), `${entry.id}: use flowchart, graph, or sequenceDiagram`);
    if (declaration !== 'sequenceDiagram') {
      const result = validateDiagram(source);
      assert(result.valid, `${entry.id}: OMM validation failed: ${JSON.stringify(result.issues.filter((issue) => issue.level === 'error'))}`);
    }
    figures.push({ entry, source, description });
  }
  assert.deepEqual(figures.map(({ entry }) => entry.source).sort(), await sourcesBelow(root), 'Every nested .mmd source must appear exactly once in manifest.json');
  // Retired generated assets cannot silently remain published. Legacy hand-authored SVGs are migrated separately.
  for (const file of await readdir(join(root, 'site/public/diagrams'))) {
    if (file.endsWith('.svg') && (await read(root, `site/public/diagrams/${file}`)).startsWith('<!-- jautomata-diagram ')) {
      assert(assets.has(`site/public/diagrams/${file}`), `Orphan generated diagram: ${file}`);
    }
  }
  return { figures, config };
}

function escapeAttribute(value) {
  return value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

/** Canonicalize SVG IDs/references and add accessible metadata without timestamps or host paths. */
async function normalizeSvg(browser, raw, entry, description, embeddedMathCss) {
  const page = await browser.newPage();
  try {
    return await page.evaluate(({ raw, entry, description, embeddedMathCss }) => {
      const doc = new DOMParser().parseFromString(raw, 'image/svg+xml');
      if (doc.querySelector('parsererror')) throw new Error('Renderer returned invalid XML');
      const svg = doc.documentElement;
      if (svg.localName !== 'svg') throw new Error('Renderer did not return SVG');
      if (svg.querySelector('script, foreignObject')) throw new Error('Only static SVG elements are supported');
      // CLI 12 embeds only the first family in a stack. Preserve the fallback
      // actually used during layout as a self-contained, licensed SVG font.
      const mathStyle = doc.createElementNS('http://www.w3.org/2000/svg', 'style');
      mathStyle.textContent = embeddedMathCss;
      svg.appendChild(mathStyle);
      svg.querySelectorAll(':scope > title, :scope > desc, :scope > metadata').forEach((node) => node.remove());
      const mapping = new Map();
      [svg, ...svg.querySelectorAll('[id]')].forEach((node, index) => {
        const old = node.getAttribute('id');
        const id = index === 0 ? entry.id : `${entry.id}-${index}`;
        if (old) mapping.set(old, id);
        node.setAttribute('id', id);
      });
      const replaceReferences = (value) => value.replace(/#([\w-]+)/g, (match, id) => mapping.has(id) ? `#${mapping.get(id)}` : match);
      for (const element of [svg, ...svg.querySelectorAll('*')]) {
        // Mermaid's editor stores duplicate base64 coordinates; static SVG uses the actual path.
        element.removeAttribute('data-points');
        for (const attribute of [...element.attributes]) {
          if (attribute.name.startsWith('on')) throw new Error('SVG event handlers are not supported');
          if (attribute.name !== 'id') element.setAttribute(attribute.name, replaceReferences(attribute.value));
          if (['href', 'xlink:href'].includes(attribute.name) && !attribute.value.startsWith('#') && !attribute.value.startsWith('data:')) throw new Error('SVG has an external resource');
        }
        if (element.localName === 'style') {
          let css = replaceReferences(element.textContent);
          // CLI font fetches finish concurrently; the order of disjoint font-face rules varies.
          const faces = (css.match(/@font-face\s*\{[^}]*\}/g) ?? []).sort();
          let index = 0;
          css = css.replace(/@font-face\s*\{[^}]*\}/g, () => faces[index++]);
          element.textContent = css;
        }
      }
      const fontStyles = [...svg.querySelectorAll('style')].filter((node) => node.textContent.includes('@font-face'));
      const fontBlocks = fontStyles.map((node) => node.textContent).sort();
      fontStyles.forEach((node, index) => { node.textContent = fontBlocks[index]; });
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-labelledby', `${entry.id}-title ${entry.id}-description`);
      svg.removeAttribute('aria-describedby');
      for (const [tag, id, value] of [['desc', `${entry.id}-description`, description], ['title', `${entry.id}-title`, entry.title]]) {
        const node = doc.createElementNS('http://www.w3.org/2000/svg', tag);
        node.setAttribute('id', id);
        node.textContent = value;
        svg.insertBefore(node, svg.firstChild);
      }
      // Attributes have no order semantics; sorting makes serialization independent of insertion order.
      for (const element of [svg, ...svg.querySelectorAll('*')]) {
        const attributes = [...element.attributes].map(({ name, value }) => [name, value]).sort(([a], [b]) => a.localeCompare(b, 'en'));
        for (const [name] of attributes) element.removeAttribute(name);
        for (const [name, value] of attributes) element.setAttribute(name, value);
      }
      return new XMLSerializer().serializeToString(svg).trim() + '\n';
    }, { raw, entry, description, embeddedMathCss });
  } finally {
    await page.close();
  }
}

const numberPattern = /[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:e[-+]?\d+)?/gi;

/** Bound coordinates/generated solid trims; keep labels, authored styles, and path commands exact. */
export function compareSvg(actual, expected, tolerance = 0.75) {
  const geometry = (svg) => {
    const values = [];
    const numbers = (value, location) => {
      let component = 0;
      return value.replace(numberPattern, (number) => { values.push({ ...location, component: component++, value: Number(number) }); return '~'; });
    };
    const skeleton = svg.replace(/<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<[A-Za-z](?:"[^"]*"|'[^']*'|[^'">])*>/g,
      (tag, tagOffset) => {
        if (tag.startsWith('<!')) return tag;
        const element = tag.match(/^<([\w:-]+)/)[1];
        const attributes = Object.fromEntries([...tag.matchAll(/\s([\w:-]+)=("([^"]*)"|'([^']*)')/g)].map((match) => [match[1], match[3] ?? match[4]]));
        const classes = (attributes.class ?? '').split(/\s+/);
        // Mermaid neo computes this marker trim from getTotalLength(). Only
        // its uncustomized solid-edge form is geometry; authored styles stay exact.
        const generatedTrim = element === 'path' && attributes['data-edge'] === 'true'
          && attributes['data-et'] === 'edge' && attributes['data-look'] === 'neo'
          && classes.includes('flowchart-link') && classes.includes('edge-pattern-solid')
          && !classes.some((name) => /edge-pattern-(dotted|dashed)|edge-animation/.test(name))
          && /^stroke-dasharray: 0 0 \d+(?:\.\d+)? 4; stroke-dashoffset: 0;;$/.test(attributes.style ?? '');
        return tag.replace(/(\s)([\w:-]+)=("([^"]*)"|'([^']*)')/g, (_, space, key, quoted, doubleValue, singleValue) => {
          const value = doubleValue ?? singleValue;
          const location = { element, id: attributes.id ?? null, tagOffset, attribute: key };
          let normalized = value;
          if (/^(d|points|transform|viewBox|x|y|x1|x2|y1|y2|cx|cy|rx|ry|r|width|height|textLength)$/.test(key)) normalized = numbers(value, location);
          else if (key === 'style') normalized = value.replace(/(^|;)(\s*max-width:\s*)([\d.]+)px(?=\s*(?:;|$))/g,
            (_, separator, property, size) => `${separator}${property}${numbers(size, { ...location, attribute: 'style:max-width' })}px`);
          if (key === 'style' && generatedTrim) normalized = normalized.replace(/^(stroke-dasharray: 0 0 )(\d+(?:\.\d+)?)( 4;)/,
            (_, prefix, length, suffix) => `${prefix}${numbers(length, { ...location, attribute: 'style:generated-solid-trim-length' })}${suffix}`);
          return `${space}${key}=${quoted[0]}${normalized}${quoted[0]}`;
        });
      });
    return { skeleton, values };
  };
  const a = geometry(actual);
  const b = geometry(expected);
  if (a.skeleton !== b.skeleton || a.values.length !== b.values.length) {
    let index = 0;
    while (index < a.skeleton.length && a.skeleton[index] === b.skeleton[index]) index++;
    return { equal: false, kind: 'structure', reason: `SVG structure, labels, IDs, or styles differ at ${index}: ${JSON.stringify(a.skeleton.slice(index, index + 80))} / ${JSON.stringify(b.skeleton.slice(index, index + 80))}` };
  }
  const changes = a.values.map(({ value, ...location }, index) => ({
    ...location, committed: value, rendered: b.values[index].value, delta: Math.abs(value - b.values[index].value),
  })).filter(({ delta }) => delta > 0).sort((left, right) => right.delta - left.delta);
  const delta = changes[0]?.delta ?? 0;
  return { equal: delta <= tolerance, kind: 'geometry', delta, largestChanges: changes.slice(0, 5), reason: `maximum geometry difference ${delta.toFixed(4)} (allowed ${tolerance})` };
}

function wrapSvg(svg, inputHash) {
  return `<!-- jautomata-diagram input:${inputHash} svg:${digest(svg)} -->\n${svg}`;
}

export function checkedSvg(contents, inputHash) {
  const match = contents.match(/^<!-- jautomata-diagram input:([a-f0-9]{64}) svg:([a-f0-9]{64}) -->\n([\s\S]*)$/);
  assert(match, 'Generated SVG metadata is missing; regenerate diagrams');
  assert.equal(match[1], inputHash, 'Diagram source, manifest, renderer, or lockfile changed; regenerate diagrams');
  assert.equal(match[2], digest(match[3]), 'Generated SVG was edited; regenerate diagrams');
  return match[3];
}

async function atomicWrite(path, contents) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.tmp`;
  await writeFile(temporary, contents);
  await rename(temporary, path);
}

export async function generateDiagrams({ root = repository, check = false, exact = false, diagnosticsDirectory = process.env.DIAGRAM_DIAGNOSTICS_DIR, log = console.log } = {}) {
  if (diagnosticsDirectory) {
    diagnosticsDirectory = resolve(diagnosticsDirectory);
    for (const base of [root, repository]) {
      const path = relative(resolve(base), diagnosticsDirectory);
      assert(path === '..' || path.startsWith(`..${sep}`) || isAbsolute(path), 'Diagram diagnostics must be outside the repository and input root');
    }
  }
  const { figures, config } = await loadCatalog(root);
  if (!figures.length) { log('Diagram catalog: 0 figures (migration has not populated it yet).'); return; }
  const commonInput = await Promise.all(['.omm/renderer.json', 'site/package-lock.json'].map((path) => read(root, path)));
  commonInput.push(await readFile(script, 'utf8'));
  const fontCss = await readFile(mathFontCss, 'utf8');
  const fontBytes = await readFile(mathFontFile);
  const fontLicense = await readFile(new URL('../LICENSE', mathFontFile), 'utf8');
  commonInput.push(fontCss, digest(fontBytes), fontLicense);
  const embeddedMathCss = `/* ${fontLicense.replaceAll('*/', '* /')} */\n${fontCss.replace(/url\('[^']+'\)/, `url('data:font/woff2;base64,${fontBytes.toString('base64')}')`)}`;
  const browser = await puppeteer.launch({
    executablePath: process.env.DIAGRAM_CHROMIUM_EXECUTABLE || chromium.executablePath(),
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none'],
  });
  const outputs = [];
  const results = [];
  const browserVersion = await browser.version();
  try {
    for (const { entry, source, description } of figures) {
      try {
        const inputHash = digest(JSON.stringify([...commonInput, entry, source, description]));
        const rendered = await renderMermaid(browser, source, 'svg', {
          svgId: entry.id,
          mermaidConfig: { ...config.mermaid, deterministicIDSeed: entry.id },
          viewport: { width: 1600, height: 1200, deviceScaleFactor: 1 },
          fontEmbed: true,
          customFontCSS: [{ cssUrl: mathFontCss, allowParentDirectoryLevel: 1 }],
        });
        const svg = await normalizeSvg(browser, Buffer.from(rendered.data).toString('utf8'), entry, description, embeddedMathCss);
        if (check) {
          const contents = await read(root, entry.asset);
          let result;
          try {
            const committed = checkedSvg(contents, inputHash);
            result = compareSvg(committed, svg, exact ? 0 : config.geometryTolerance);
            if (exact && committed !== svg && result.equal) Object.assign(result, { equal: false, reason: 'exact SVG bytes differ' });
          } catch (error) {
            result = { equal: false, kind: 'validation', reason: error.message };
          }
          if (diagnosticsDirectory && !result.equal) {
            await atomicWrite(join(diagnosticsDirectory, `${entry.id}.committed.svg`), contents);
            await atomicWrite(join(diagnosticsDirectory, `${entry.id}.rendered.svg`), svg);
          }
          results.push({ id: entry.id, ...result });
          log(`${result.equal ? 'Verified' : 'FAILED'} ${entry.id}: ${result.reason}`);
          if (result.largestChanges?.length) log(`  Largest coordinate changes: ${JSON.stringify(result.largestChanges)}`);
        } else outputs.push({ path: join(root, entry.asset), contents: wrapSvg(svg, inputHash) });
      } catch (error) {
        if (!check) throw error;
        results.push({ id: entry.id, equal: false, kind: 'validation-or-render', reason: error.message });
        log(`FAILED ${entry.id}: ${error.message}`);
      }
    }
  } finally {
    await browser.close();
  }
  if (check) {
    const failed = results.filter(({ equal }) => !equal);
    if (diagnosticsDirectory) {
      await atomicWrite(join(diagnosticsDirectory, 'report.json'), JSON.stringify({
        platform: process.platform, arch: process.arch, node: process.version, browser: browserVersion,
        tolerance: exact ? 0 : config.geometryTolerance, checked: results.length, failed: failed.length, results,
      }, null, 2) + '\n');
    }
    assert.equal(failed.length, 0, `${failed.length}/${results.length} diagram checks failed: ${failed.map(({ id, reason }) => `${id}: ${reason}`).join('; ')}; inspect diagnostics or run npm run generate-diagrams after reviewing the differences`);
  }
  // Finish all validation/rendering before replacing any assets.
  for (const output of outputs) { await atomicWrite(output.path, output.contents); log(`Generated ${relative(root, output.path)}`); }
}

if (process.argv[1] && resolve(process.argv[1]) === script) {
  const args = process.argv.slice(2);
  assert(args.every((arg) => ['--check', '--exact'].includes(arg)), 'Usage: node scripts/diagrams.mjs [--check] [--exact]');
  await generateDiagrams({ check: args.includes('--check'), exact: args.includes('--exact') });
}
