import { delay, http, HttpResponse } from 'msw';
import { createPreviewStore, previewSession } from './store.js';

const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
let store = createPreviewStore();
let scenario = 'normal';

const roleOf = (/** @type {Request} */ request) =>
	request.headers.get('Authorization')?.endsWith('customer')
		? 'customer'
		: request.headers.get('Authorization')?.endsWith('staff')
			? 'staff'
			: 'admin';
const queryOf = (/** @type {Request} */ request) =>
	Object.fromEntries(new URL(request.url).searchParams);
const json = (/** @type {any} */ data, status = 200) => HttpResponse.json(data, { status });

/** Translate fixture failures into the same readable envelope as the agreed API. @param {() => any | Promise<any>} callback */
async function respond(callback) {
	try {
		if (scenario === 'slow') await delay(1200);
		return json(await callback());
	} catch (reason) {
		const error = /** @type {any} */ (reason);
		return json(
			{
				error: {
					code:
						error.status === 404
							? 'not_found'
							: error.status === 422
								? 'validation_error'
								: 'conflict',
					message: error.message,
					fields: error.fields ?? {}
				}
			},
			error.status ?? 409
		);
	}
}

/** A tiny valid document for reviewing the PDF action without a backend. @param {any} invoice */
function previewPdf(invoice) {
	const text = `BT /F1 18 Tf 64 740 Td (Brightloop - frontend preview) Tj 0 -36 Td /F1 12 Tf (${invoice.number}) Tj 0 -22 Td (Total: INR ${invoice.total}) Tj 0 -22 Td (This is sample data.) Tj ET`;
	const objects = [
		'<< /Type /Catalog /Pages 2 0 R >>',
		'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
		'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
		`<< /Length ${text.length} >>\nstream\n${text}\nendstream`,
		'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
	];
	let pdf = '%PDF-1.4\n';
	const offsets = [0];
	objects.forEach((object, index) => {
		offsets.push(pdf.length);
		pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
	});
	const start = pdf.length;
	pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
	pdf += offsets
		.slice(1)
		.map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`)
		.join('');
	pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`;
	return new HttpResponse(pdf, { headers: { 'Content-Type': 'application/pdf' } });
}

/** Browser-only preview HTTP handlers. No business fixture is imported by a feature. */
export const handlers = [
	http.post(`${base}/auth/login`, async ({ request }) => {
		const body = /** @type {any} */ (await request.json());
		const role = String(body.email).startsWith('customer')
			? 'customer'
			: String(body.email).startsWith('staff')
				? 'staff'
				: 'admin';
		return json(previewSession(role));
	}),
	http.get(`${base}/auth/me`, ({ request }) => json(previewSession(roleOf(request)).user)),
	http.post(`${base}/__preview/reset`, () => {
		store = createPreviewStore();
		scenario = 'normal';
		return json({ ok: true });
	}),
	http.post(`${base}/__preview/scenario`, async ({ request }) => {
		const body = /** @type {any} */ (await request.json());
		scenario = ['normal', 'slow', 'empty', 'error'].includes(body.scenario)
			? body.scenario
			: 'normal';
		return json({ scenario });
	}),
	...[
		'subscriptions',
		'invoices',
		'payments',
		'customers',
		'plans',
		'products',
		'taxes',
		'payment-terms',
		'quotation-templates',
		'billing/runs'
	].flatMap((resource) => [
		http.get(`${base}/${resource}`, ({ request }) =>
			scenario === 'error'
				? json(
						{ error: { code: 'internal_error', message: 'Preview error scenario.', fields: {} } },
						503
					)
				: respond(() =>
						scenario === 'empty'
							? { items: [], total: 0, page: 1, page_size: 25 }
							: store.list(resource, queryOf(request), roleOf(request))
					)
		),
		...(['subscriptions', 'invoices', 'payments'].includes(resource)
			? [
					http.get(`${base}/me/${resource}`, ({ request }) =>
						scenario === 'error'
							? json(
									{
										error: {
											code: 'internal_error',
											message: 'Preview error scenario.',
											fields: {}
										}
									},
									503
								)
							: respond(() =>
									scenario === 'empty'
										? { items: [], total: 0, page: 1, page_size: 25 }
										: store.list(resource, queryOf(request), 'customer')
								)
					)
				]
			: [])
	]),
	http.get(`${base}/products/:id`, ({ params }) => respond(() => store.product(String(params.id)))),
	http.get(`${base}/plans/:id`, ({ params }) => respond(() => store.plan(String(params.id)))),
	http.post(`${base}/subscriptions/price-preview`, async ({ request }) => {
		const body = await request.json();
		return respond(() => store.price(body));
	}),
	http.post(`${base}/subscriptions`, async ({ request }) => {
		const body = await request.json();
		return respond(() => store.saveSubscription(body));
	}),
	http.post(`${base}/subscriptions/from-template/:id`, async ({ params, request }) => {
		const body = await request.json();
		return respond(() => store.fromTemplate(String(params.id), body));
	}),
	http.patch(`${base}/subscriptions/:id`, async ({ params, request }) => {
		const body = await request.json();
		return respond(() => store.saveSubscription(body, String(params.id)));
	}),
	...['', '/me'].flatMap((prefix) => [
		http.get(`${base}${prefix}/subscriptions/:id/history`, ({ params, request }) =>
			respond(() => {
				store.subscription(String(params.id), prefix ? 'customer' : roleOf(request));
				return store.history(String(params.id));
			})
		),
		http.get(`${base}${prefix}/subscriptions/:id`, ({ params, request }) =>
			respond(() => store.subscription(String(params.id), prefix ? 'customer' : roleOf(request)))
		),
		http.post(
			`${base}${prefix}/subscriptions/:id/${prefix ? 'actions' : 'transition'}`,
			async ({ params, request }) => {
				const body = /** @type {any} */ (await request.json());
				return respond(() =>
					store.subscriptionAction(
						String(params.id),
						body.action,
						prefix ? 'customer' : roleOf(request)
					)
				);
			}
		),
		http.get(`${base}${prefix}/invoices/:id/pdf`, ({ params, request }) => {
			try {
				return previewPdf(store.invoice(String(params.id), prefix ? 'customer' : roleOf(request)));
			} catch {
				return json(
					{ error: { code: 'not_found', message: 'Invoice not found.', fields: {} } },
					404
				);
			}
		}),
		http.get(`${base}${prefix}/invoices/:id`, ({ params, request }) =>
			respond(() => store.invoice(String(params.id), prefix ? 'customer' : roleOf(request)))
		)
	]),
	...['confirm', 'cancel', 'send'].map((action) =>
		http.post(`${base}/invoices/:id/${action}`, ({ params, request }) =>
			respond(() => store.invoiceAction(String(params.id), action, roleOf(request)))
		)
	),
	http.post(`${base}/invoices/:id/payments`, async ({ params, request }) => {
		const body = await request.json();
		return respond(() => store.pay(String(params.id), body, roleOf(request)));
	}),
	http.post(`${base}/me/invoices/:id/pay`, async ({ params, request }) => {
		const body = await request.json();
		return respond(() => store.pay(String(params.id), body, 'customer'));
	}),
	http.post(`${base}/billing/run`, () => respond(() => store.startRun())),
	http.get(`${base}/billing/runs/:id`, ({ params }) => respond(() => store.run(String(params.id)))),
	http.all(`${base}/*`, () =>
		json(
			{
				error: {
					code: 'not_found',
					message: 'This endpoint is not part of the frontend preview.',
					fields: {}
				}
			},
			404
		)
	)
];
