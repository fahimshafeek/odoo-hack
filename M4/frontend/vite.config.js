// Load native tool plugins through Node instead of bundling their binary bindings.
const packages = ['@tailwindcss/vite', '@sveltejs/kit/vite', '@sveltejs/adapter-node'];
const [tailwind, kit, node] = await Promise.all(packages.map((name) => import(name)));

export default {
	plugins: [tailwind.default(), kit.sveltekit({ adapter: node.default() })],
	test: { environment: 'node', pool: 'threads', include: ['src/**/*.test.js'] }
};
