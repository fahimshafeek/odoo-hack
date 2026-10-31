import { createServer } from 'vite';

// Real API backend connection: mocks disabled for live product.
process.env.VITE_USE_MOCKS = process.env.VITE_USE_MOCKS ?? 'false';
const server = await createServer({
	configLoader: 'native',
	server: { host: '127.0.0.1', port: 5173, strictPort: true }
});
await server.listen();
server.printUrls();
