const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const date = new Intl.DateTimeFormat('en-GB', {
	day: '2-digit',
	month: 'short',
	year: 'numeric',
	timeZone: 'Asia/Kolkata'
});

/** Display server money without performing pricing arithmetic (A6). @param {string | number | null | undefined} value */
export function formatMoney(value) {
	if (value === null || value === undefined || value === '') return '—';
	const number = Number(value);
	return Number.isFinite(number) ? money.format(number) : '—';
}

/** Render dates consistently in the backend's Asia/Kolkata timezone (D13). @param {string | null | undefined} value */
export function formatDate(value) {
	if (!value) return '—';
	const parsed = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00Z` : value);
	return Number.isNaN(parsed.getTime()) ? '—' : date.format(parsed);
}
