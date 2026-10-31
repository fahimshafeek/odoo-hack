import ts from 'typescript';
import { readdir, readFile } from 'node:fs/promises';
import { join, relative } from 'node:path';

/** Enforce A0.6: fixtures stay in mocks/tests, never in production feature code. */
async function scan(directory) {
	const failures = [];
	for (const entry of await readdir(directory, { withFileTypes: true })) {
		const path = join(directory, entry.name);
		const name = relative('src', path).replaceAll('\\', '/');
		if (entry.isDirectory()) {
			if (name !== 'api/mocks') failures.push(...(await scan(path)));
			continue;
		}
		if (!/\.(js|svelte)$/.test(name) || /\.(test|spec)\.js$/.test(name)) continue;
		const content = await readFile(path, 'utf8');
		const script = ts.createSourceFile(name, content, ts.ScriptTarget.Latest, true);
		if (
			/\b(?:import|export)\b[^;]*["'][^"']*\.json["']/.test(content) ||
			/\bimport\s*\(\s*["'][^"']*\.json["']/.test(content)
		) {
			failures.push(`${name}: JSON data import`);
		}
		const guardedPreviewBootstrap =
			name === 'hooks.client.js' &&
			/import\.meta\.env\.DEV\s*&&\s*import\.meta\.env\.VITE_USE_MOCKS\s*===\s*['"]true['"]/.test(
				content
			);
		if (
			/(?:from\s*|import\s*\(\s*)["'][^"']*(?:api\/mocks|\.\/mocks)/.test(content) &&
			!guardedPreviewBootstrap
		) {
			failures.push(`${name}: mock import in production source`);
		}
		if (name.startsWith('features/') && !name.endsWith('/routes.js')) {
			const visit = (node) => {
				if (
					ts.isArrayLiteralExpression(node) &&
					node.elements.length >= 3 &&
					node.elements.every(ts.isObjectLiteralExpression) &&
					!node.elements.every((element) => {
						const keys = /** @type {import('typescript').ObjectLiteralExpression} */ (
							element
						).properties.map((property) => property.name?.getText(script));
						return keys.includes('key') && keys.includes('header');
					})
				) {
					failures.push(`${name}: embedded business record array`);
				}
				ts.forEachChild(node, visit);
			};
			visit(script);
		}
	}
	return failures;
}

const failures = await scan('src');
if (failures.length) {
	console.error(failures.join('\n'));
	process.exitCode = 1;
} else console.log('Static-data check passed.');
