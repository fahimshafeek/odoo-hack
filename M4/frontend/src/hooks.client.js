/** Preview fixtures are never enabled by a production build. */
export async function init() {
	if (import.meta.env.DEV && import.meta.env.VITE_USE_MOCKS === 'true') {
		const { startPreview } = await import('#src/api/mocks/browser.js');
		await startPreview();
	}
}
