import openapiTS, { astToString } from 'openapi-typescript';
import { readFile, writeFile } from 'node:fs/promises';

const snapshot = new URL('../openapi.snapshot.json', import.meta.url);
let schema;
try {
	const base = process.env.VITE_API_URL || 'http://localhost:8000';
	const response = await fetch(`${base.replace(/\/$/, '')}/openapi.json`, {
		signal: AbortSignal.timeout(5000)
	});
	if (!response.ok) throw new Error(`OpenAPI returned ${response.status}`);
	schema = await response.json();
	if (!schema.openapi || !schema.paths) throw new Error('Invalid OpenAPI document');
	await openapiTS(schema);
	await writeFile(snapshot, `${JSON.stringify(schema, null, 2)}\n`);
	console.log('Using live backend OpenAPI contract.');
} catch {
	schema = JSON.parse(await readFile(snapshot, 'utf8'));
	console.log('Backend unavailable: using committed contract snapshot.');
}
const output = astToString(await openapiTS(schema));
await writeFile(new URL('../src/api/schema.d.ts', import.meta.url), output);
