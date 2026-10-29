import { cp, mkdir, readdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, posix, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(here, '..');
const source = resolve(siteRoot, '..', 'docs');
const destination = resolve(siteRoot, 'src', 'content', 'docs');

try {
  await stat(source);
} catch {
  throw new Error(`Canonical documentation directory is missing: ${source}`);
}

await rm(destination, { recursive: true, force: true });
await mkdir(dirname(destination), { recursive: true });
await cp(source, destination, { recursive: true });

const sourceBase = 'https://github.com/cri5Castro/JAutomata/blob/master/';

async function normalizeMarkdown(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await normalizeMarkdown(path);
    if (!entry.isFile() || !entry.name.endsWith('.md')) continue;

    let text = await readFile(path, 'utf8');
    if (!text.startsWith('---\n')) {
      const heading = text.match(/^#\s+(.+)$/m)?.[1] ?? entry.name.replace(/\.md$/, '').replaceAll('-', ' ');
      text = `---\ntitle: ${JSON.stringify(heading)}\n---\n\n${text}`;
    }
    text = text.replace(/\]\((?:\.\.\/)+((?:src|python)\/[^)#]+)(#[^)]+)?\)/g, (_match, path, hash = '') => `](${sourceBase}${path}${hash})`);
    const currentDirectory = relative(destination, dirname(path)).replaceAll('\\', '/');
    text = text.replace(/\]\((?!https?:|#)([^)]+?\.md)(#[^)]+)?\)/g, (_match, markdownPath, hash = '') => {
      const route = posix.normalize(posix.join('/', currentDirectory, markdownPath)).replace(/\.md$/, '/');
      const starlightRoute = route === '/index/' ? '/' : route;
      return `](/JAutomata${starlightRoute}${hash})`;
    });
    await writeFile(path, text);
    if (text.includes("import TracePlayer from")) await rename(path, path.replace(/\.md$/, '.mdx'));
  }
}

await normalizeMarkdown(destination);
console.log(`Staged canonical docs: ${source} -> ${destination}`);
