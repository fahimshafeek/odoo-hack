import { delay, http, HttpResponse } from 'msw';
import { createPreviewStore, previewSession } from './store.js';

const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
let store = createPreviewStore();
let scenario = 'normal';

const userOf = (/** @type {Request} */ request) => {
	const authHeader = request.headers.get('Authorization') ?? '';
	const token = authHeader.replace(/^Bearer\s+/i, '').trim();
	return store.getSessionUser(token);
};
const roleOf = (/** @type {Request} */ request) => {
	const user = userOf(request);
	if (user?.role) return user.role;
	const authHeader = request.headers.get('Authorization') ?? '';
	return authHeader.includes('customer')
		? 'customer'
		: authHeader.includes('staff')
			? 'staff'
			: 'admin';
};
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
		return respond(() => store.loginUser(body.email, body.password));
	}),
	http.get(`${base}/auth/me`, ({ request }) => {
		const user = userOf(request) ?? previewSession(roleOf(request)).user;
		return json(user);
	}),
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
		'billing/runs',
		'discounts',
		'staff'
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

	...[
		'products',
		'plans',
		'payment-terms',
		'quotation-templates',
		'customers',
		'staff',
		'taxes',
		'discounts'
	].flatMap((resource) => [
		...(!['products', 'plans'].includes(resource)
			? [
					http.get(base + '/' + resource + '/:id', ({ params }) =>
						respond(() => store.resourceDetail(resource, String(params.id)))
					)
				]
			: []),
		http.post(base + '/' + resource, async ({ request }) =>
			respond(() => request.json().then((body) => store.saveResource(resource, body)))
		),
		http.patch(base + '/' + resource + '/:id', async ({ params, request }) =>
			respond(() =>
				request.json().then((body) => store.saveResource(resource, body, String(params.id)))
			)
		),
		http.delete(base + '/' + resource + '/:id', ({ params }) =>
			respond(() => store.deactivate(resource, String(params.id)))
		)
	]),
	http.post(base + '/plans/:id/close', ({ params }) =>
		respond(() => store.deactivate('plans', String(params.id)))
	),
	http.post(base + '/products/:id/attributes', async ({ params, request }) =>
		respond(() => request.json().then((body) => store.attribute(String(params.id), body)))
	),
	http.patch(base + '/products/:id/attributes/:attribute', async ({ params, request }) =>
		respond(() =>
			request
				.json()
				.then((body) => store.attribute(String(params.id), body, String(params.attribute)))
		)
	),
	http.delete(base + '/products/:id/attributes/:attribute', ({ params }) =>
		respond(() => store.attribute(String(params.id), {}, String(params.attribute), true))
	),
	http.get(base + '/me/profile', () => respond(() => store.profile())),
	http.patch(base + '/me/profile', async ({ request }) =>
		respond(() => request.json().then((body) => store.saveProfile(body)))
	),
	http.post(base + '/auth/signup', async ({ request }) => {
		const body = /** @type {any} */ (await request.json());
		return respond(() => store.signupUser(body));
	}),
	http.post(base + '/auth/forgot-password', () =>
		json({ message: 'If an account exists, a reset link will be sent.' })
	),
	http.post(base + '/auth/reset-password', () => json({ message: 'Password updated.' })),
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

	http.get(base + '/reports/summary', () =>
		respond(() => {
			if (scenario === 'error') throw new Error('Preview report unavailable.');
			const invoices = scenario === 'empty' ? [] : store.list('invoices', { page_size: 100 }).items;
			const subscriptions =
				scenario === 'empty' ? [] : store.list('subscriptions', { page_size: 100 }).items;
			const sum = (/** @type {any[]} */ rows, /** @type {string} */ key) =>
				rows.reduce((total, row) => total + Math.round(Number(row[key] || 0) * 100), 0) / 100;
			const overdue = invoices.filter((row) => row.is_overdue);
			return {
				as_of: new Date().toISOString().slice(0, 10),
				active_subscriptions: subscriptions.filter((row) => row.status === 'active').length,
				mrr: sum(
					subscriptions.filter((row) => row.status === 'active'),
					'estimated_total'
				).toFixed(2),
				revenue_collected: sum(invoices, 'amount_paid').toFixed(2),
				invoiced_total: sum(
					invoices.filter((row) => ['confirmed', 'paid'].includes(row.status)),
					'total'
				).toFixed(2),
				outstanding_total: sum(
					invoices.filter((row) => row.status === 'confirmed'),
					'balance'
				).toFixed(2),
				overdue_count: overdue.length,
				overdue_total: sum(overdue, 'balance').toFixed(2),
				upcoming_renewals_count: 0
			};
		})
	),
	http.get(base + '/reports/revenue-by-month', ({ request }) =>
		respond(() => {
			if (scenario === 'error') throw new Error('Preview report unavailable.');
			if (scenario === 'empty') return [];
			const count = Math.min(
				36,
				Math.max(1, Number(new URL(request.url).searchParams.get('months') || 6))
			);
			return Array.from({ length: count }, (_, index) => {
				const month = new Date();
				month.setUTCDate(1);
				month.setUTCMonth(month.getUTCMonth() - count + index + 1);
				return {
					month: month.toISOString().slice(0, 7),
					invoiced: (18000 + index * 3400 + (index % 3) * 2100).toFixed(2),
					collected: (15000 + index * 3100 + (index % 2) * 1700).toFixed(2)
				};
			});
		})
	),
	http.get(base + '/reports/overdue-invoices', () =>
		respond(() => {
			if (scenario === 'error') throw new Error('Preview report unavailable.');
			const rows =
				scenario === 'empty'
					? []
					: store.list('invoices', { payment_filter: 'overdue', page_size: 100 }).items;
			return {
				items: rows.slice(0, 5).map((row) => ({
					invoice_id: row.id,
					number: row.number,
					customer_id: row.customer.id,
					customer_name: row.customer.name,
					phone: row.customer.phone,
					due_date: row.due_date,
					days_overdue: row.days_overdue,
					total: row.total,
					balance: row.balance
				})),
				total: rows.length,
				page: 1,
				page_size: 5
			};
		})
	),
	http.get(base + '/reports/upcoming-renewals', () =>
		respond(() => {
			if (scenario === 'error') throw new Error('Preview report unavailable.');
			const rows =
				scenario === 'empty'
					? []
					: store.list('subscriptions', { page_size: 100 }).items;
			return {
				items: rows.slice(0, 5).map((row) => ({
					subscription_id: row.id,
					number: row.number,
					customer_name: row.customer?.name ?? 'Customer',
					plan_name: row.plan?.name ?? 'Standard Plan',
					expiry_date: row.expiry_date || new Date().toISOString().slice(0, 10),
					days_left: 15,
					allow_renew: true
				})),
				total: rows.length,
				page: 1,
				page_size: 5
			};
		})
	),
	http.get(base + '/reports/export.csv', ({ request }) => {
		const type = new URL(request.url).searchParams.get('report') || 'overdue';
		const csv = `"Report","${type}"\n"Sample","Data"`;
		return new Response(csv, {
			headers: {
				'Content-Type': 'text/csv',
				'Content-Disposition': `attachment; filename=brightloop_${type}_report.csv`
			}
		});
	}),
	http.post(`${base}/me/invoices/:id/razorpay/order`, ({ params }) =>
		respond(() => ({
			order_id: `order_mock_${String(params.id).slice(0, 8)}`,
			amount: 50000,
			currency: 'INR',
			key_id: 'rzp_test_mock',
			invoice_id: params.id,
			invoice_number: 'INV-MOCK',
			balance: '500.00'
		}))
	),
	http.post(`${base}/invoices/:id/razorpay/order`, ({ params }) =>
		respond(() => ({
			order_id: `order_mock_${String(params.id).slice(0, 8)}`,
			amount: 50000,
			currency: 'INR',
			key_id: 'rzp_test_mock',
			invoice_id: params.id,
			invoice_number: 'INV-MOCK',
			balance: '500.00'
		}))
	),
	http.post(`${base}/me/invoices/:id/razorpay/link`, ({ params }) =>
		respond(() => ({
			payment_link_id: `plink_mock_${String(params.id).slice(0, 8)}`,
			short_url: `https://rzp.io/i/mock_${String(params.id).slice(0, 6)}`,
			amount: 50000,
			invoice_id: params.id,
			invoice_number: 'INV-MOCK'
		}))
	),
	http.post(`${base}/invoices/:id/razorpay/link`, ({ params }) =>
		respond(() => ({
			payment_link_id: `plink_mock_${String(params.id).slice(0, 8)}`,
			short_url: `https://rzp.io/i/mock_${String(params.id).slice(0, 6)}`,
			amount: 50000,
			invoice_id: params.id,
			invoice_number: 'INV-MOCK'
		}))
	),
	http.post(`${base}/me/invoices/:id/razorpay/verify`, ({ params }) =>
		respond(() => ({
			status: 'captured',
			payment_id: 'pay_mock_verified',
			invoice_status: 'paid',
			amount_paid: '500.00'
		}))
	),
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
