/** Get the record segment from a canonical list/detail/edit URL. @param {string} pathname */
export function recordId(pathname) {
	const segments = pathname.split('/').filter(Boolean);
	const value = segments.at(-1) === 'edit' ? segments.at(-2) : segments.at(-1);
	return decodeURIComponent(value ?? '');
}

/** Client date controls use the same timezone as the backend clock (D13). */
export function todayISO() {
	const parts = new Intl.DateTimeFormat('en-CA', {
		timeZone: 'Asia/Kolkata',
		year: 'numeric',
		month: '2-digit',
		day: '2-digit'
	}).formatToParts(new Date());
	const get = (/** @type {string} */ type) => parts.find((part) => part.type === type)?.value;
	return `${get('year')}-${get('month')}-${get('day')}`;
}
