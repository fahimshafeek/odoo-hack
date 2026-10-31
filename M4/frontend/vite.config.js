import { fileURLToPath } from 'node:url';

// Load native tool plugins through Node instead of bundling their binary bindings.
const packages = ['@tailwindcss/vite', '@sveltejs/kit/vite', '@sveltejs/adapter-node'];
const [tailwind, kit, node] = await Promise.all(packages.map((name) => import(name)));

export default {
	// This CSS-only package has no JavaScript export for Vite's SSR resolver.
	resolve: {
		alias: {
			'tw-animate-css': fileURLToPath(
				new URL('./node_modules/tw-animate-css/dist/tw-animate.css', import.meta.url)
			)
		}
	},
	plugins: [tailwind.default(), kit.sveltekit({ adapter: node.default() })],
	test: { environment: 'node', pool: 'threads', include: ['src/**/*.test.js'] }
};
