import { cp, mkdir, readdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, posix, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { slug } from 'github-slugger';

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(here, '..');
const source = resolve(siteRoot, '..', 'docs');
const destination = resolve(siteRoot, 'src', 'content', 'docs');

const sourceBase = 'https://github.com/cri5Castro/JAutomata/blob/master/';

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function removeDuplicatePageHeading(text) {
  const frontmatter = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!frontmatter) return text;

  const title = frontmatter[1].match(/^title:\s*(?:"([^"]+)"|'([^']+)'|(.+))\s*$/m);
  const value = title?.[1] ?? title?.[2] ?? title?.[3]?.trim();
  if (!value) return text;

  const content = text.slice(frontmatter[0].length);
  const leadingHeading = new RegExp(`^\\n*#\\s+${escapeRegExp(value)}\\s*\\n`);
  if (!leadingHeading.test(content)) return text;
  return `${frontmatter[0]}<span id="${slug(value)}" aria-hidden="true"></span>\n${content.replace(leadingHeading, '')}`;
}

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
    text = removeDuplicatePageHeading(text);
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

async function stageCanonicalDocs() {
  try {
    await stat(source);
  } catch {
    throw new Error(`Canonical documentation directory is missing: ${source}`);
  }

  await rm(destination, { recursive: true, force: true });
  await mkdir(dirname(destination), { recursive: true });
  await cp(source, destination, { recursive: true });
  await normalizeMarkdown(destination);
  console.log(`Staged canonical docs: ${source} -> ${destination}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await stageCanonicalDocs();
}
