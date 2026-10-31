import { fileURLToPath } from 'node:url';

// Load native tool plugins through Node instead of bundling their binary bindings.
const packages = ['@tailwindcss/vite', '@sveltejs/kit/vite', '@sveltejs/adapter-node'];
const [tailwind, kit, node] = await Promise.all(packages.map((name) => import(name)));
const testing = process.env.VITEST
	? (await import('@testing-library/svelte/vite')).svelteTesting()
	: [];

export default {
	// This CSS-only package has no JavaScript export for Vite's SSR resolver.
	resolve: {
		alias: {
			'tw-animate-css': fileURLToPath(
				new URL('./node_modules/tw-animate-css/dist/tw-animate.css', import.meta.url)
			)
		}
	},
	plugins: [tailwind.default(), kit.sveltekit({ adapter: node.default() }), testing],
	test: {
		environment: 'jsdom',
		setupFiles: ['./vitest-setup.js'],
		pool: 'threads',
		include: ['src/**/*.test.js']
	}
};
