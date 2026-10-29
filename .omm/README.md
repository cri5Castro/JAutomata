# Canonical teaching diagrams

Each shared figure has one Mermaid source in this repository-local [Oh My Mermaid](https://github.com/oh-my-mermaid/oh-my-mermaid) catalog. Lessons publish generated, accessible SVG images. The site needs no Mermaid browser runtime, and its `/JAutomata/` base path is unchanged.

The catalog contains 25 shared figures with 42 placements across 35 canonical
lessons. The manifest's `inventory` records all 27 replaced conceptual text blocks,
additional placements, legacy-asset dispositions, and preserved text. Every nested
source and generated SVG belongs to the manifest; an unlisted source or generated
asset is an error.

## Install and preview

Use the Node version in `site/.node-version`, the existing Python/uv setup, and the committed npm lockfile. From the repository root:

```sh
cd site
PUPPETEER_SKIP_DOWNLOAD=true npm ci
npm exec playwright install chromium
npm run generate-diagrams
npm run dev
```

On Linux, use `npm exec playwright install --with-deps chromium` when Chromium's system libraries are absent. Mermaid CLI uses the same pinned Playwright Chromium as the existing browser tests. `PUPPETEER_SKIP_DOWNLOAD=true` avoids downloading a second browser. If you set `PLAYWRIGHT_BROWSERS_PATH` during installation, use that same value for all diagram/site/test commands. `DIAGRAM_CHROMIUM_EXECUTABLE=/absolute/path/to/chromium` is an explicit local diagnostic override; the pinned Playwright browser is the release default.

Open the generated SVG directly, or preview its lesson in the dev server. Static generation and preview use installed local dependencies and embedded fonts. The existing `npm run build` and `npm run check` include diagram freshness checks.

OMM is installed locally; no global installation, `omm setup`, login, cloud sync, or separate project is required. Run it from the repository root so it finds this `.omm` directory:

```sh
./site/node_modules/.bin/omm list
./site/node_modules/.bin/omm tree theory
./site/node_modules/.bin/omm read theory/literal diagram
./site/node_modules/.bin/omm view --port 3001
```

Alternatively `npm --prefix site run omm -- ...` runs from the root via the configured script. OMM discovers nested folders without generated metadata or a `config.yaml`. Its optional viewer exposes those folders through its local API, but version 0.2.0 loads CDN scripts and web fonts. Use the generated SVG/site preview for offline and publication-accurate rendering. Do not commit OMM history/timestamp metadata merely to render a figure.

## Add or edit a figure

Create `.omm/<scope>/<id>/diagram.mmd` and an adjacent `description.md`. Suggested scopes are `theory`, `tutorials`, `labs`, `architecture`, and `learn`. Reuse the same source across multiple lessons instead of copying it. The source starts with `flowchart LR` (or another explicit direction), `graph LR`, or `sequenceDiagram`. Do not add Mermaid frontmatter or init directives; shared rendering settings live in `renderer.json`.

Use a short reading direction, one teaching goal, short labels, and shapes/text in addition to color. Keep long explanations beside the figure. `description.md` contains plain accessible prose describing the relevant states, edges, or timing. This file is the single canonical SVG description, not Markdown markup or a copy of program output. `title` comes from the manifest. The renderer supplies the SVG title, description, stable IDs, and ARIA relationship; source-level accessibility declarations are unnecessary.

Add an explicit entry to `manifest.json`:

```json
{
  "version": 1,
  "figures": [
    {
      "id": "literal",
      "source": ".omm/theory/literal/diagram.mmd",
      "description": ".omm/theory/literal/description.md",
      "asset": "site/public/diagrams/literal.svg",
      "title": "A literal fragment",
      "provenance": [
        {
          "path": "python/src/jautomata/thompson.py",
          "note": "Name the actual source symbol or cited legacy example and the semantics verified against it."
        }
      ],
      "placements": [
        { "path": "docs/theory/literal.md", "alt": "Start state 0 reaches accepting state 1 on a." }
      ]
    }
  ]
}
```

The example illustrates the schema; verify the actual provenance path/symbol before adding it. IDs are unique lowercase hyphenated names beginning with a letter. Asset names are unique and directly under `site/public/diagrams/`. Source and description paths are repository-relative; the description must be adjacent to `diagram.mmd`. Each provenance entry needs an existing repository `path` and a `note` explaining the evidence and any limits. Each placement needs a unique canonical `docs/*.md` path and meaningful `alt` text. Additional provenance fields may record a specific symbol or expression. The whole entry participates in freshness hashing.

Place the asset in every listed canonical lesson with double-quoted attributes:

```html
<img class="diagram" src="/JAutomata/diagrams/literal.svg" alt="Start state 0 reaches accepting state 1 on a." />
```

Escape `&`, `"`, `<`, and `>` in HTML attributes; store the unescaped text in JSON. Preserve the adjacent reading cue and text explanation. Edit `docs/`, not staged `site/src/content/docs/`. The generator checks every listed image's URL, `diagram` class, and exact alternative. It recursively enumerates all `.mmd` files and requires each to occur exactly once in the manifest: an unlisted nested source cannot quietly escape validation. Provenance verification and complete lesson-placement coverage remain review responsibilities.

For diagrams that would shrink labels on a phone, use this keyboard-scrollable white panel and a full-size link. Set `--diagram-width` close to the generated SVG's `viewBox` width in pixels so labels stay near their authored size (the default is `46rem`). This panel keeps the page narrow in both themes; it does not invert diagram colors. Keep the link outside the scrolling region so it remains easy to reach without JavaScript.

```html
<div class="diagram-scroll" tabindex="0" role="region" aria-label="Literal fragment, scrollable diagram" style="--diagram-width: 560px">
  <img class="diagram" src="/JAutomata/diagrams/literal.svg" alt="Start state 0 reaches accepting state 1 on a." />
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/literal.svg">Open full-size diagram</a></p>
```

Small figures can keep the plain image. Review actual label size, scrolling, focus visibility, contrast, and the full-size link at narrow viewport sizes when migrating a lesson.

## Regenerate and verify

From `site/`:

```sh
npm run generate-diagrams
npm run check-diagrams
npm run check-diagrams -- --exact
npm run test:diagrams
npm run check
npm run build
npm run test:links
```

Generation validates the entire catalog and renders all figures before atomically replacing each asset. It never edits lessons or deletes legacy assets. Commit sources, descriptions, manifest/config changes, and regenerated SVGs together. Removing a generated figure requires removing its asset and lesson placements too.

OMM 0.2.0 is a lightweight flowchart checker. Its warnings include architecture conventions that do not fit every teaching graph; its errors are enforced for flowcharts. Sequence diagrams bypass that flowchart-only check. **Every figure is also parsed and rendered by the real pinned Mermaid CLI**, including sequences and in `--check` mode. The tests use temporary fixtures outside the canonical catalog and exercise invalid syntax, nested enumeration, accessibility, repeated rendering, and stale output detection.

SVG metadata fingerprints the figure entry, source, description, shared renderer config, npm lockfile, generator, `.omm/math-font.css`, and the pinned math font's actual WOFF2 bytes and license. A separate payload checksum catches manual asset edits. The check then renders again and compares the normalized SVG. IDs and references are normalized in traversal order; packaged fonts and their licenses are embedded and sorted consistently. Open Sans remains first for existing glyphs; the locally bundled Noto Sans Math 5.3.0 face covers mathematical symbols such as `∅` and `→`, avoiding platform-font fallback. Its wrapper supplies the correct symbol range; the package's default CSS advertises only Latin despite the full font containing these glyphs. The renderer explicitly embeds this fallback because Mermaid CLI 12 embeds only the first family of a stack. No CDN or runtime font fetch is needed. Mermaid's duplicate editor-only `data-points` coordinates are removed; actual SVG path geometry is retained and checked. No timestamps or machine paths are recorded.

`--exact` demands identical bytes and is useful for repeated renders on the same platform. The default check allows at most **0.75 SVG units** of coordinate drift (including viewport/size attributes). This bound follows a complete macOS/Linux comparison with the same Chromium version: the largest observed text-bound drift unrelated to missing glyphs was 0.643 units. Missing-symbol fallback is corrected by the bundled math font, rather than covered by a larger allowance.

Labels, IDs, elements, path commands, embedded font data, and authored styles remain exact. The sole additional geometry field is Mermaid neo's generated solid-edge marker trim: the `LENGTH` in the complete uncustomized inline style `stroke-dasharray: 0 0 LENGTH 4; stroke-dashoffset: 0;;`. This value comes from the rendered path's `getTotalLength()`. It shares the coordinate bound only on a marked neo flowchart edge with the solid-edge class and no animation/dotted/dashed class. Leading zeros, the trailing gap, offset, other styles, and authored dash patterns stay exact. Nothing is removed from the emitted SVG.

Geometry changes beyond the bound fail. Identical bytes across macOS/Linux are not assumed: inspect the complete report and rendered figures when upgrading Node, the browser, Mermaid, or fonts. Keep the lockfile pinned and regenerate all catalog assets after an intentional toolchain/config change.

Freshness checks report every figure before returning a failure, so one platform
difference cannot hide later differences. Coordinate diagnostics identify the
element, ID, opening-tag offset in the committed SVG payload, attribute, numeric component, and committed/rendered
values for the five largest changes. Text and style differences still fail exactly.
For a complete JSON report and SVG pairs for failed comparisons, choose a temporary
directory outside both the repository and any supplied fixture root:

```sh
diagram_diagnostics="$(mktemp -d)"
DIAGRAM_DIAGNOSTICS_DIR="$diagram_diagnostics" npm run check-diagrams
```

`$diagram_diagnostics/report.json` records every result, tolerance, OS/architecture, Node, and Chromium
versions. Diagnostics never enter the site output. The existing Pages workflow
uploads a `diagram-diagnostics` artifact only if its check/build step fails. Keep
the threshold unchanged until the complete comparison set explains a platform
difference; do not regenerate or relax checks merely to hide a failed comparison.

The existing single Pages workflow installs Chromium once, runs these focused tests and freshness checks, then retains the established site, browser, links, and deployment steps. [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) remains build-time tooling only.
