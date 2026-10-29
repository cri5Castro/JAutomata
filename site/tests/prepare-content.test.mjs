import assert from 'node:assert/strict';
import test from 'node:test';
import { removeDuplicatePageHeading } from '../scripts/prepare-content.mjs';

test('staging replaces an exact title H1 with its compatible anchor', () => {
  const source = '---\ntitle: "Tutorial: check errors"\n---\n\n# Tutorial: check errors\n\nLesson text.\n';
  const staged = removeDuplicatePageHeading(source);

  assert.match(staged, /<span id="tutorial-check-errors" aria-hidden="true"><\/span>/);
  assert.doesNotMatch(staged, /# Tutorial: check errors/);
  assert.match(staged, /Lesson text/);
});

test('staging preserves a leading H1 when it does not match frontmatter', () => {
  const source = '---\ntitle: "Course overview"\n---\n\n# Start with a small automaton\n';

  assert.equal(removeDuplicatePageHeading(source), source);
});
