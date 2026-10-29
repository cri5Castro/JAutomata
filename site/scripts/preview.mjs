import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';

const dist = resolve('dist');
const base = '/JAutomata/';
const args = process.argv.slice(2);
const port = Number(args[args.indexOf('--port') + 1] ?? process.env.PORT ?? 4321);
const host = process.env.HOST ?? '127.0.0.1';
const types = { '.css': 'text/css', '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.wasm': 'application/wasm' };

const server = createServer(async (request, response) => {
  const pathname = new URL(request.url ?? '/', `http://${request.headers.host}`).pathname;
  if (!pathname.startsWith(base)) {
    response.writeHead(404).end('Not found');
    return;
  }
  const relativePath = decodeURIComponent(pathname.slice(base.length));
  const candidate = resolve(dist, normalize(relativePath));
  if (!candidate.startsWith(`${dist}/`) && candidate !== dist) {
    response.writeHead(400).end('Invalid path');
    return;
  }
  try {
    const info = await stat(candidate);
    const file = info.isDirectory() ? join(candidate, 'index.html') : candidate;
    response.writeHead(200, { 'content-type': types[extname(file)] ?? 'application/octet-stream' });
    createReadStream(file).pipe(response);
  } catch {
    response.writeHead(404).end('Not found');
  }
});

server.listen(port, host, () => console.log(`Serving ${dist} at http://${host}:${port}${base}`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => server.close(() => process.exit(0)));
