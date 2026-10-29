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
          items: ['getting-started', 'learn/foundations', 'learn/regex-syntax'],
        },
        {
          label: 'Learn the pipeline',
          items: ['learn/thompson', 'learn/epsilon-closure', 'learn/subset-construction', 'tutorial'],
        },
        { label: 'Practice', items: ['practice/exercises'] },
        {
          label: 'Reference',
          items: ['reference/glossary', 'python-api', 'algorithms', 'architecture', 'compatibility', 'java-reference'],
        },
      ],
    }),
    mdx(),
  ],
});
