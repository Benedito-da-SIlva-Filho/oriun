import { mdsvex } from 'mdsvex';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/kit/vite';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: [vitePreprocess(), mdsvex()],
    kit: {
        adapter: adapter({ fallback: 'index.html' })
    },
    extensions: ['.svelte', '.svx']
};

export default config;
