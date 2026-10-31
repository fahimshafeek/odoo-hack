import { createServer } from 'vite';

// Isolated browser fixtures: no backend or database required.
process.env.VITE_USE_MOCKS = 'true';
const server = await createServer({
	configLoader: 'native',
	server: { host: '127.0.0.1', port: 5173, strictPort: true }
});
await server.listen();
server.printUrls();
