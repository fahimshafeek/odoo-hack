import { api } from '#lib/auth/session.js';
import { notify } from '#lib/notify.js';

/**
 * Downloads a CSV report from the backend with formula injection protection.
 * @param {'overdue' | 'upcoming_renewals' | 'subscriptions'} reportType
 */
export async function downloadReportCsv(reportType) {
	try {
		const binaryClient = /** @type {import('openapi-fetch').Client<Record<string, any>>} */ (api);
		const { data, response } = await binaryClient.GET(`/reports/export.csv?report=${reportType}`, {
			parseAs: 'blob'
		});
		if (!(data instanceof Blob) && response?.status !== 200) {
			throw new Error('Failed to generate CSV export.');
		}
		const blob = data instanceof Blob ? data : new Blob([String(data ?? '')], { type: 'text/csv;charset=utf-8;' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `brightloop_${reportType}_report.csv`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		setTimeout(() => URL.revokeObjectURL(url), 60000);
		notify.success(`Exported ${reportType.replaceAll('_', ' ')} report to CSV.`);
	} catch (error) {
		notify.error(error);
	}
}
