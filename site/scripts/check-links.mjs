import { access, readdir, readFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const dist = path.resolve('dist');
const basePath = '/JAutomata/';
const htmlFiles = [];
const errors = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) await walk(file);
    else if (entry.name.endsWith('.html')) htmlFiles.push(file);
  }
}

function htmlPathForRoute(route) {
  const cleaned = route.replace(/^\/+/, '');
  if (!cleaned || cleaned.endsWith('/')) return path.join(dist, cleaned, 'index.html');
  if (path.extname(cleaned)) return path.join(dist, cleaned);
  return path.join(dist, cleaned, 'index.html');
}

async function exists(file) {
  try {
    await access(file, constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

function idsFrom(html) {
  return new Set([...html.matchAll(/\sid=(['"])(.*?)\1/g)].map((match) => match[2]));
}

function hrefsFrom(html) {
  return [...html.matchAll(/\s(?:href|src)=(['"])(.*?)\1/g)].map((match) => match[2]);
}

function isExternal(value) {
  return /^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(value) || value.startsWith('mailto:') || value.startsWith('tel:');
}

async function checkReference(sourceFile, reference) {
  if (!reference || isExternal(reference) || reference.startsWith('data:')) return;
  const [withoutQuery, fragment = ''] = reference.split('#', 2);
  const targetRoute = withoutQuery.startsWith('/')
    ? withoutQuery.startsWith(basePath)
      ? withoutQuery.slice(basePath.length)
      : null
    : path.posix.normalize(path.posix.join(path.posix.dirname(path.relative(dist, sourceFile)), withoutQuery || '.'));

  if (targetRoute === null) {
    errors.push(`${path.relative(dist, sourceFile)}: internal reference escapes ${basePath}: ${reference}`);
    return;
  }

  const target = htmlPathForRoute(targetRoute);
  if (!await exists(target)) {
    errors.push(`${path.relative(dist, sourceFile)}: missing ${reference} (${path.relative(dist, target)})`);
    return;
  }
  if (fragment) {
    const targetHtml = await readFile(target, 'utf8');
    if (!idsFrom(targetHtml).has(decodeURIComponent(fragment))) {
      errors.push(`${path.relative(dist, sourceFile)}: missing anchor #${fragment} in ${path.relative(dist, target)}`);
    }
  }
}

await walk(dist);
if (htmlFiles.length === 0) {
  throw new Error('No built HTML found. Run npm run build before npm run test:links.');
}
for (const file of htmlFiles) {
  const html = await readFile(file, 'utf8');
  await Promise.all(hrefsFrom(html).map((reference) => checkReference(file, reference)));
}

for (const required of ['pagefind/pagefind.js', 'pagefind/pagefind-ui.js', 'sitemap-index.xml']) {
  if (!await exists(path.join(dist, required))) errors.push(`missing built asset: ${required}`);
}

if (errors.length) {
  console.error(`Built-site link check failed with ${errors.length} issue(s):\n${errors.map((error) => `- ${error}`).join('\n')}`);
  process.exitCode = 1;
} else {
  console.log(`Built-site link check passed: ${htmlFiles.length} HTML files, /JAutomata/ links, assets, and anchors.`);
}
