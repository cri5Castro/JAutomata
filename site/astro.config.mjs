import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://cri5castro.github.io',
  base: '/JAutomata/',
  integrations: [
    starlight({
      title: 'JAutomata',
      description: 'Learn regular expressions, epsilon-NFAs, and complete DFAs one clear step at a time.',
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      components: {
        Head: './src/components/Head.astro',
        PageTitle: './src/components/FocusMode.astro',
      },
      sidebar: [
        { label: 'Home', slug: 'index' },
        {
          label: 'Start here',
          items: ['learning-map', 'getting-started', 'learn/foundations', 'learn/regex-syntax'],
        },
        {
          label: 'Short learning path',
          items: ['learn/thompson', 'learn/epsilon-closure', 'learn/subset-construction', 'tutorial'],
        },
        {
          label: 'Model and parsing',
          collapsed: true,
          items: ['theory/automata', 'tutorials/automata', 'theory/regex', 'tutorials/regex', 'theory/parsing', 'tutorials/parsing'],
        },
        {
          label: 'Thompson fragments',
          collapsed: true,
          items: ['theory/literal', 'tutorials/literal', 'theory/concatenation', 'tutorials/concatenation', 'theory/union', 'tutorials/union', 'theory/kleene-star', 'tutorials/kleene-star', 'theory/positive-closure', 'tutorials/positive-closure'],
        },
        {
          label: 'Recognition and DFAs',
          collapsed: true,
          items: ['theory/epsilon-closure', 'tutorials/epsilon-closure', 'theory/nfa-simulation', 'tutorials/nfa-simulation', 'theory/subset-construction', 'tutorials/subset-construction', 'theory/complete-dfa', 'tutorials/complete-dfa'],
        },
        {
          label: 'Implementation reasoning',
          collapsed: true,
          items: ['theory/identity', 'tutorials/identity', 'theory/pure-execution', 'tutorials/pure-execution', 'theory/validation-complexity', 'tutorials/validation-complexity'],
        },
        {
          label: 'Historical capstones',
          collapsed: true,
          items: ['labs/practica1', 'labs/practica2', 'labs/practica3', 'labs/main'],
        },
        { label: 'Practice', collapsed: true, items: ['practice/exercises'] },
        {
          label: 'Reference',
          collapsed: true,
          items: ['reference/source-curriculum', 'reference/glossary', 'python-api', 'algorithms', 'architecture', 'compatibility', 'java-reference'],
        },
      ],
    }),
    mdx(),
  ],
});
