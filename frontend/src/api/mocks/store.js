import { todayISO } from '#lib/navigation.js';

const id = (/** @type {string} */ domain, /** @type {number} */ value) =>
	`${domain}0000000-0000-4000-8000-${String(value).padStart(12, '0')}`;
const cents = (/** @type {string | number} */ value) => {
	const [whole, fraction = ''] = String(value).split('.');
	return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
};
const money = (/** @type {bigint} */ value) =>
	`${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
const offsetDate = (/** @type {number} */ days) => {
	const value = new Date(`${todayISO()}T12:00:00Z`);
	value.setUTCDate(value.getUTCDate() + days);
	return value.toISOString().slice(0, 10);
};
const periodStart = () => `${todayISO().slice(0, 7)}-01`;

/** Preview identities are only used by the explicitly enabled development worker. @param {'admin' | 'staff' | 'customer'} role */
export function previewSession(role) {
	return {
		access_token: `preview-${role}`,
		token_type: /** @type {const} */ ('bearer'),
		user: {
			id: id('9', role === 'admin' ? 1 : role === 'staff' ? 2 : 3),
			full_name:
				role === 'customer'
					? 'Northstar Labs'
					: role === 'staff'
						? 'Sales workspace'
						: 'Admin workspace',
			email: `${role}@brightloop.io`,
			role,
			customer_id: role === 'customer' ? id('1', 1) : null
		}
	};
}

/** Deterministic in-memory scenarios for frontend development; never a billing implementation. */
export function createPreviewStore() {
	const customers = [
		{
			id: id('1', 1),
			name: 'Northstar Labs',
			company_name: 'Northstar Labs',
			email: 'hello@northstar.example',
			full_name: 'Northstar team',
			phone: '+91 98765 43210',
			billing_address: 'Bengaluru, India',
			tax_id: 'Preview GST'
		},
		{
			id: id('1', 2),
			name: 'Morrow Studio',
			company_name: 'Morrow Studio',
			email: 'accounts@morrow.example',
			full_name: 'Morrow team',
			phone: '+91 98765 43211',
			billing_address: 'Kochi, India',
			tax_id: null
		},
		{
			id: id('1', 3),
			name: 'Evergreen Works',
			company_name: 'Evergreen Works',
			email: 'billing@evergreen.example',
			full_name: 'Evergreen team',
			phone: '+91 98765 43212',
			billing_address: 'Pune, India',
			tax_id: null
		}
	];
	const taxes = [{ id: id('4', 1), name: 'GST 18%', rate_percent: '18.00', is_active: true }];
	const terms = [
		{ id: id('5', 1), name: 'Net 15', due_days: 15, is_active: true },
		{ id: id('5', 2), name: 'Immediate', due_days: 0, is_active: true }
	];
	const plans = [
		{
			id: id('2', 1),
			name: 'Growth',
			price: '2000.00',
			billing_period: 'monthly',
			min_quantity: 5,
			valid_from: '2020-01-01',
			valid_to: '2035-12-31',
			auto_close: true,
			allow_early_close: true,
			allow_pause: true,
			allow_renew: true,
			is_active: true,
			tax_id: taxes[0].id
		},
		{
			id: id('2', 2),
			name: 'Essential',
			price: '0.00',
			billing_period: 'monthly',
			min_quantity: 1,
			valid_from: '2020-01-01',
			valid_to: '2035-12-31',
			auto_close: true,
			allow_early_close: true,
			allow_pause: false,
			allow_renew: true,
			is_active: true,
			tax_id: null
		}
	];
	const products = [
		{
			id: id('3', 1),
			name: 'Workspace seat',
			type: 'service',
			sales_price: '1000.00',
			cost_price: '400.00',
			notes: 'A shared place for your team.',
			tax_id: taxes[0].id,
			tax: taxes[0],
			is_active: true,
			attributes: [
				{
					id: id('a', 1),
					name: 'Edition',
					values: [
						{ id: id('b', 1), name: 'Standard', extra_price: '0.00' },
						{ id: id('b', 2), name: 'Plus', extra_price: '250.00' }
					]
				}
			]
		},
		{
			id: id('3', 2),
			name: 'Priority support',
			type: 'service',
			sales_price: '1500.00',
			cost_price: '600.00',
			notes: 'Dedicated support for your workspace.',
			tax_id: taxes[0].id,
			tax: taxes[0],
			is_active: true,
			attributes: []
		}
	];
	const templates = [
		{
			id: id('c', 1),
			name: 'Growth workspace',
			plan_id: plans[0].id,
			plan: plans[0],
			validity_days: 30,
			is_active: true,
			lines: [
				{
					product_id: products[0].id,
					product: products[0],
					quantity: 5,
					variant_value_ids: [id('b', 1)],
					tax_id: taxes[0].id
				}
			]
		}
	];
	/** @type {any[]} */ const discounts = [
		{
			id: id('d', 1),
			name: 'Welcome credit',
			type: 'fixed',
			value: '500.00',
			scope: 'subscription',
			min_purchase: null,
			min_quantity: null,
			start_date: offsetDate(-30),
			end_date: offsetDate(60),
			usage_limit: 100,
			used_count: 1,
			is_active: true,
			targets: [],
			editable_fields: ['name', 'end_date', 'is_active', 'usage_limit']
		}
	];
	/** @type {any[]} */ const staff = [
		{ ...previewSession('staff').user, is_active: true, created_at: new Date().toISOString() }
	];
	/** @type {any} */ let profile = { ...customers[0] };
	function collection(/** @type {string} */ resource) {
		return /** @type {any[]} */ (
			/** @type {Record<string, any[]>} */ ({
				customers,
				products,
				plans,
				taxes,
				'payment-terms': terms,
				'quotation-templates': templates,
				discounts,
				staff
			})[resource] ?? []
		);
	}
	function resourceDetail(/** @type {string} */ resource, /** @type {string} */ recordId) {
		return (
			collection(resource).find((row) => row.id === recordId) ?? fail('Record not found.', 404)
		);
	}
	function saveResource(
		/** @type {string} */ resource,
		/** @type {any} */ body,
		/** @type {string} */ recordId = ''
	) {
		const rows = collection(resource);
		const row = recordId
			? resourceDetail(resource, recordId)
			: {
					id: id('f', ++sequence),
					created_at: new Date().toISOString(),
					is_active: true,
					attributes: [],
					used_count: 0
				};
		Object.assign(row, body, { updated_at: new Date().toISOString() });
		if (resource === 'staff') row.role = 'staff';
		if (resource === 'customers') {
			row.user_id ??= id('9', ++sequence);
			row.full_name ??= row.name ?? '';
			row.company_name ??= '';
			row.name = row.company_name || row.full_name;
		}
		if (resource === 'products' && body.tax_id)
			row.tax = taxes.find((tax) => tax.id === body.tax_id);
		if (resource === 'quotation-templates') {
			row.plan = plans.find((plan) => plan.id === row.plan_id);
			row.lines = (row.lines ?? []).map((/** @type {any} */ line) => ({
				...line,
				product: products.find((product) => product.id === line.product_id)
			}));
		}
		if (resource === 'discounts')
			row.editable_fields = row.used_count
				? ['name', 'end_date', 'is_active', 'usage_limit']
				: Object.keys(row);
		if (!recordId) rows.push(row);
		return row;
	}
	function attribute(
		/** @type {string} */ recordId,
		/** @type {any} */ body,
		/** @type {string} */ attributeId = '',
		remove = false
	) {
		const product = resourceDetail('products', recordId);
		if (remove) {
			product.attributes = product.attributes.filter(
				(/** @type {any} */ row) => row.id !== attributeId
			);
			return product;
		}
		const row = attributeId
			? product.attributes.find((/** @type {any} */ item) => item.id === attributeId)
			: { id: id('a', ++sequence) };
		Object.assign(row, body, {
			values: (body.values ?? []).map((/** @type {any} */ value) => ({
				...value,
				id: value.id ?? id('b', ++sequence)
			}))
		});
		if (!attributeId) product.attributes.push(row);
		return product;
	}
	/** @type {any[]} */ const subscriptions = [];
	/** @type {any[]} */ const invoices = [];
	/** @type {any[]} */ const payments = [];
	/** @type {any[]} */ const runs = [];
	/** @type {Record<string, any[]>} */ const histories = {};
	let sequence = 20;
	const fail = (/** @type {string} */ message, status = 409, fields = {}) => {
		throw Object.assign(new Error(message), { status, fields });
	};

	const users = [
		{
			id: id('9', 1),
			email: 'admin@brightloop.io',
			aliases: ['admin@brightloop.test', 'admin@preview.brightloop.test'],
			password: 'BrightloopAdmin@123',
			altPasswords: ['Admin@12345', 'admin123', 'Brightloop123!'],
			role: 'admin',
			full_name: 'Admin workspace',
			customer_id: null
		},
		{
			id: id('9', 2),
			email: 'staff@brightloop.io',
			aliases: ['staff@brightloop.test', 'staff@preview.brightloop.test'],
			password: 'BrightloopStaff@123',
			altPasswords: ['Staff@12345', 'staff123', 'Brightloop123!'],
			role: 'staff',
			full_name: 'Sales workspace',
			customer_id: null
		},
		{
			id: id('9', 3),
			email: 'customer@brightloop.io',
			aliases: [
				'customer@brightloop.test',
				'customer@preview.brightloop.test',
				'hello@northstar.example'
			],
			password: 'BrightloopCust@123',
			altPasswords: ['Customer@12345', 'customer123', 'Brightloop123!'],
			role: 'customer',
			full_name: 'Northstar Labs',
			customer_id: id('1', 1)
		}
	];
	/** @type {Map<string, any>} */
	const activeSessions = new Map();

	function loginUser(/** @type {string} */ email, /** @type {string} */ password) {
		const normEmail = String(email || '').trim().toLowerCase();
		const user = users.find(
			(u) =>
				u.email.toLowerCase() === normEmail ||
				u.aliases?.some((a) => a.toLowerCase() === normEmail)
		);
		if (!user) {
			return fail('Invalid email or password. Please check your credentials or sign up.', 401);
		}
		const validPassword =
			user.password === password ||
			user.altPasswords?.includes(password);
		if (!validPassword) {
			return fail('Invalid email or password. Please check your password.', 401);
		}
		const token = `preview-${user.role}-${user.id}`;
		const userOut = {
			id: user.id,
			full_name: user.full_name,
			email: user.email,
			role: user.role,
			customer_id: user.customer_id
		};
		activeSessions.set(token, userOut);
		return {
			access_token: token,
			token_type: 'bearer',
			user: userOut
		};
	}

	function signupUser(/** @type {any} */ body) {
		const normEmail = String(body.email || '').trim().toLowerCase();
		if (
			users.some(
				(u) =>
					u.email.toLowerCase() === normEmail ||
					u.aliases?.some((a) => a.toLowerCase() === normEmail)
			)
		) {
			return fail('An account with this email already exists.', 409);
		}
		const role = ['customer', 'staff', 'admin'].includes(body.role) ? body.role : 'customer';
		let customerId = null;
		if (role === 'customer') {
			customerId = id('1', ++sequence);
			const newCustomer = {
				id: customerId,
				name: body.company_name || body.full_name,
				company_name: body.company_name || '',
				email: normEmail,
				full_name: body.full_name,
				phone: body.phone || '',
				billing_address: 'Registered Address',
				tax_id: null
			};
			customers.push(newCustomer);
			profile = { ...newCustomer };
		}
		const newUser = {
			id: id('9', ++sequence),
			email: normEmail,
			aliases: [],
			password: body.password,
			altPasswords: [],
			role,
			full_name: body.full_name,
			customer_id: customerId
		};
		users.push(newUser);
		if (role === 'staff') {
			staff.push({
				id: newUser.id,
				full_name: newUser.full_name,
				email: newUser.email,
				role: 'staff',
				is_active: true,
				created_at: new Date().toISOString()
			});
		}
		const token = `preview-${role}-${newUser.id}`;
		const userOut = {
			id: newUser.id,
			full_name: newUser.full_name,
			email: newUser.email,
			role: newUser.role,
			customer_id: newUser.customer_id
		};
		activeSessions.set(token, userOut);
		return {
			access_token: token,
			token_type: 'bearer',
			user: userOut
		};
	}

	function getSessionUser(/** @type {string} */ token) {
		if (!token) return null;
		if (activeSessions.has(token)) return activeSessions.get(token);
		for (const u of users) {
			if (token.includes(u.id)) {
				const userOut = {
					id: u.id,
					full_name: u.full_name,
					email: u.email,
					role: u.role,
					customer_id: u.customer_id
				};
				activeSessions.set(token, userOut);
				return userOut;
			}
		}
		if (token.endsWith('customer')) return users.find((u) => u.role === 'customer') ?? null;
		if (token.endsWith('staff')) return users.find((u) => u.role === 'staff') ?? null;
		if (token.endsWith('admin')) return users.find((u) => u.role === 'admin') ?? null;
		return null;
	}
	const own = (/** @type {any} */ row, /** @type {string} */ role) =>
		role !== 'customer' || row.customer.id === id('1', 1);

	/** Fixture-only arithmetic keeps preview responses coherent when controls change. @param {any} body */
	function price(body) {
		const plan = plans.find((item) => item.id === body.plan_id) ?? plans[0];
		const lines = (body.lines ?? []).map((/** @type {any} */ line, /** @type {number} */ index) => {
			const product = products.find((item) => item.id === line.product_id) ?? products[0];
			const selections = product.attributes.flatMap((attribute) =>
				attribute.values
					.filter((value) => line.variant_value_ids?.includes(value.id))
					.map((value) => ({
						attribute: attribute.name,
						value: value.name,
						extra_price: value.extra_price
					}))
			);
			const unit =
				cents(product.sales_price) +
				selections.reduce((total, value) => total + cents(value.extra_price), 0n);
			const quantity = Number(line.quantity) || 1;
			const gross = unit * BigInt(Math.max(1, Math.trunc(quantity)));
			const tax = line.tax_id === null ? 0n : (gross * 18n + 50n) / 100n;
			return {
				id: id('d', index + 1),
				product_id: product.id,
				product: { id: product.id, name: product.name },
				variant: { selections },
				quantity,
				unit_price: money(unit),
				amount: money(gross),
				tax: line.tax_id === null ? null : taxes[0],
				tax_rate: line.tax_id === null ? '0.00' : '18.00',
				tax_amount: money(tax),
				total: money(gross + tax)
			};
		});
		const fee = cents(plan.price);
		const feeTax = plan.tax_id ? (fee * 18n + 50n) / 100n : 0n;
		const subtotal = lines.reduce(
			(/** @type {bigint} */ sum, /** @type {any} */ line) => sum + cents(line.amount),
			fee
		);
		const taxTotal = lines.reduce(
			(/** @type {bigint} */ sum, /** @type {any} */ line) => sum + cents(line.tax_amount),
			feeTax
		);
		return {
			lines,
			plan_fee:
				fee > 0n
					? {
							amount: plan.price,
							tax_rate: plan.tax_id ? '18.00' : '0.00',
							tax_amount: money(feeTax),
							total: money(fee + feeTax)
						}
					: null,
			totals: {
				subtotal: money(subtotal),
				tax_total: money(taxTotal),
				total: money(subtotal + taxTotal)
			}
		};
	}
	function subView(/** @type {any} */ row, /** @type {string} */ role) {
		const map = /** @type {Record<string, string[]>} */ ({
			draft: ['send_quote'],
			quotation: ['confirm', 'reject'],
			confirmed: ['activate'],
			active: ['pause', 'renew', 'close'],
			paused: ['resume'],
			closed: []
		});
		const actions = (map[row.status] ?? [])
			.filter((action) => action !== 'pause' || row.plan.allow_pause)
			.filter((action) => action !== 'renew' || row.plan.allow_renew)
			.filter((action) => action !== 'close' || row.plan.allow_early_close);
		return {
			...row,
			can_edit: role !== 'customer' && row.status === 'draft',
			allowed_actions:
				role === 'customer'
					? actions.filter((action) => ['pause', 'resume', 'renew', 'close'].includes(action))
					: actions
		};
	}
	function invoiceView(/** @type {any} */ row, /** @type {string} */ role) {
		const balance = cents(row.total) - cents(row.amount_paid);
		const daysOverdue = Math.max(
			0,
			Math.floor((Date.parse(todayISO()) - Date.parse(row.due_date)) / 86400000)
		);
		const overdue = row.status === 'confirmed' && balance > 0n && daysOverdue > 0;
		const actions =
			role === 'customer'
				? ['print', ...(balance > 0n && row.status === 'confirmed' ? ['pay'] : [])]
				: [
						...(row.status === 'draft' ? ['confirm', 'cancel'] : []),
						...(row.status === 'confirmed'
							? [
									'send',
									...(cents(row.amount_paid) === 0n ? ['cancel'] : []),
									...(balance > 0n ? ['record_payment'] : [])
								]
							: []),
						...(row.status === 'paid' ? ['send'] : []),
						...(row.status !== 'cancelled' ? ['print'] : [])
					];
		return {
			...row,
			balance: money(balance),
			is_overdue: overdue,
			days_overdue: overdue ? daysOverdue : 0,
			payment_state: ['draft', 'cancelled'].includes(row.status)
				? 'not_applicable'
				: row.status === 'paid'
					? 'paid'
					: overdue
						? 'overdue'
						: cents(row.amount_paid) > 0n
							? 'partially_paid'
							: 'unpaid',
			payments: payments.filter((payment) => payment.invoice.id === row.id),
			allowed_actions: actions
		};
	}
	function addSubscription(/** @type {any} */ body, status = 'draft', customerIndex = 0) {
		const customer =
			customers.find((item) => item.id === body.customer_id) ?? customers[customerIndex];
		const plan = plans.find((item) => item.id === body.plan_id) ?? plans[0];
		const priced = price({ ...body, plan_id: plan.id });
		const number = ++sequence;
		const row = {
			id: id('6', number),
			number: `SUB-2026-${String(number).padStart(6, '0')}`,
			status,
			customer,
			plan,
			start_date: body.start_date ?? offsetDate(-60),
			expiry_date: body.expiry_date ?? offsetDate(300),
			next_billing_date: periodStart(),
			estimated_total: priced.totals.total,
			payment_term: terms.find((term) => term.id === body.payment_term_id) ?? terms[0],
			quote_valid_until: offsetDate(30),
			template_id: body.template_id ?? null,
			created_at: new Date().toISOString(),
			...priced
		};
		subscriptions.push(row);
		histories[row.id] = [
			{
				id: id('e', number),
				from_status: 'draft',
				to_status: status,
				action: status === 'draft' ? 'create' : 'activate',
				changed_by: { id: previewSession('admin').user.id, name: 'Admin workspace' },
				changed_at: new Date().toISOString(),
				note: 'Frontend preview history'
			}
		];
		return row;
	}
	function addInvoice(/** @type {any} */ subscription, status = 'draft', discounted = false) {
		const number = ++sequence;
		const lines = [
			...(subscription.plan_fee
				? [
						{
							line_type: 'plan_fee',
							description: `Plan: ${subscription.plan.name}`,
							quantity: 1,
							unit_price: subscription.plan_fee.amount,
							amount: subscription.plan_fee.amount,
							tax_rate: subscription.plan_fee.tax_rate,
							tax_amount: subscription.plan_fee.tax_amount,
							total: subscription.plan_fee.total,
							product_id: null
						}
					]
				: []),
			...subscription.lines.map((/** @type {any} */ line) => ({
				...line,
				line_type: 'product',
				description: line.product.name
			}))
		].map((line, index) => ({
			...line,
			id: id('f', number * 10 + index),
			gross_amount: line.amount,
			discount_amount: '0.00',
			discount: null,
			line_total: line.total
		}));
		if (discounted && lines.length > 1) {
			const line = lines[1];
			const discount = 50000n;
			line.discount_amount = money(discount);
			line.discount = { id: id('c', 5), name: 'Welcome credit' };
			const net = cents(line.gross_amount) - discount;
			const tax = (net * 18n + 50n) / 100n;
			line.tax_amount = money(tax);
			line.line_total = money(net + tax);
		}
		const discountTotal = lines.reduce(
			(/** @type {bigint} */ sum, /** @type {any} */ line) => sum + cents(line.discount_amount),
			0n
		);
		const taxTotal = lines.reduce(
			(/** @type {bigint} */ sum, /** @type {any} */ line) => sum + cents(line.tax_amount),
			0n
		);
		const total = lines.reduce(
			(/** @type {bigint} */ sum, /** @type {any} */ line) => sum + cents(line.line_total),
			0n
		);
		const row = {
			id: id('7', number),
			number: `INV-2026-${String(number).padStart(6, '0')}`,
			subscription: { id: subscription.id, number: subscription.number },
			customer: subscription.customer,
			customer_billing: {
				billing_address: subscription.customer.billing_address,
				tax_id: subscription.customer.tax_id,
				phone: subscription.customer.phone
			},
			period_start: periodStart(),
			period_end: todayISO(),
			issue_date: offsetDate(-20),
			due_date: offsetDate(10),
			status,
			subtotal: subscription.totals.subtotal,
			discount_total: money(discountTotal),
			tax_total: money(taxTotal),
			total: money(total),
			amount_paid: status === 'paid' ? money(total) : '0.00',
			confirmed_at: status === 'draft' ? null : new Date().toISOString(),
			sent_at: null,
			lines
		};
		invoices.push(row);
		return row;
	}
	for (const [index, status] of [
		'active',
		'quotation',
		'draft',
		'confirmed',
		'paused',
		'closed',
		'active',
		'active'
	].entries()) {
		addSubscription(
			{
				plan_id: plans[index % 2].id,
				customer_id: customers[index % 3].id,
				lines: [
					{
						product_id: products[0].id,
						quantity: index % 2 ? 2 : 5,
						variant_value_ids: [id('b', 1)],
						tax_id: taxes[0].id
					}
				]
			},
			status,
			index % 3
		);
	}
	const invoice1 = addInvoice(subscriptions[0], 'confirmed', true);
	invoice1.due_date = offsetDate(-8);
	pay(invoice1.id, {
		amount: '1000.00',
		method: 'upi',
		paid_on: offsetDate(-12),
		note: 'Preview partial payment'
	});
	const paidInvoice = addInvoice(subscriptions[3], 'confirmed');
	pay(paidInvoice.id, {
		amount: paidInvoice.total,
		method: 'bank_transfer',
		paid_on: offsetDate(-10),
		note: 'Preview full payment'
	});
	addInvoice(subscriptions[4], 'confirmed');
	addInvoice(subscriptions[1], 'draft');
	addInvoice(subscriptions[5], 'cancelled');

	function subscription(/** @type {string} */ recordId, /** @type {string} */ role) {
		const row = subscriptions.find((item) => item.id === recordId);
		if (!row || !own(row, role) || (role === 'customer' && row.status === 'draft'))
			return fail('Subscription not found.', 404);
		return subView(row, role);
	}
	function invoice(/** @type {string} */ recordId, /** @type {string} */ role) {
		const row = invoices.find((item) => item.id === recordId);
		if (
			!row ||
			!own(row, role) ||
			(role === 'customer' && !['confirmed', 'paid'].includes(row.status))
		)
			return fail('Invoice not found.', 404);
		return invoiceView(row, role);
	}
	function list(
		/** @type {string} */ resource,
		/** @type {Record<string, any>} */ query = {},
		role = 'admin'
	) {
		let items = ['discounts', 'staff'].includes(resource)
			? collection(resource)
			: resource === 'subscriptions'
				? subscriptions
						.filter((row) => own(row, role) && (role !== 'customer' || row.status !== 'draft'))
						.map((row) => subView(row, role))
				: resource === 'invoices'
					? invoices
							.filter(
								(row) =>
									own(row, role) &&
									(role !== 'customer' || ['confirmed', 'paid'].includes(row.status))
							)
							.map((row) => invoiceView(row, role))
					: resource === 'payments'
						? payments.filter((row) => own(row, role))
						: resource === 'billing/runs'
							? runs
							: resource === 'customers'
								? customers
								: resource === 'plans'
									? plans
									: resource === 'products'
										? products
										: resource === 'taxes'
											? taxes
											: resource === 'payment-terms'
												? terms
												: resource === 'quotation-templates'
													? templates
													: [];
		if (query.active !== undefined && query.active !== '')
			items = items.filter((item) => item.is_active === (String(query.active) === 'true'));
		if (query.q)
			items = items.filter((item) =>
				JSON.stringify(item).toLowerCase().includes(String(query.q).toLowerCase())
			);
		for (const key of ['status', 'method', 'customer_id', 'plan_id', 'subscription_id'])
			if (query[key])
				items = items.filter(
					(item) =>
						String(
							key.endsWith('_id') ? (item[key.replace('_id', '')]?.id ?? item[key]) : item[key]
						) === String(query[key])
				);
		if (query.payment_filter === 'paid') items = items.filter((item) => item.status === 'paid');
		if (query.payment_filter === 'outstanding')
			items = items.filter((item) => item.status === 'confirmed' && cents(item.balance) > 0n);
		if (query.payment_filter === 'overdue') items = items.filter((item) => item.is_overdue);
		if (query.date_from)
			items = items.filter((item) => (item.issue_date ?? item.paid_on ?? '') >= query.date_from);
		if (query.date_to)
			items = items.filter((item) => (item.issue_date ?? item.paid_on ?? '') <= query.date_to);
		const sort = String(query.sort ?? '-created_at');
		const key = sort.replace(/^-/, '');
		items = [...items].sort(
			(a, b) =>
				String(a[key] ?? '').localeCompare(String(b[key] ?? '')) * (sort.startsWith('-') ? -1 : 1)
		);
		const page = Math.max(1, Number(query.page) || 1);
		const pageSize = Math.min(100, Math.max(1, Number(query.page_size) || 25));
		return {
			items: items.slice((page - 1) * pageSize, page * pageSize),
			total: items.length,
			page,
			page_size: pageSize
		};
	}
	function subscriptionAction(
		/** @type {string} */ recordId,
		/** @type {string} */ action,
		role = 'admin'
	) {
		const visible = subscription(recordId, role);
		if (!visible.allowed_actions.includes(action)) return fail('This action is unavailable.');
		const row = subscriptions.find((item) => item.id === recordId);
		const old = row.status;
		const next = /** @type {Record<string, string>} */ ({
			send_quote: 'quotation',
			confirm: 'confirmed',
			reject: 'closed',
			activate: 'active',
			pause: 'paused',
			resume: 'active',
			close: 'closed',
			renew: 'active'
		});
		row.status = next[action];
		if (action === 'renew') row.expiry_date = offsetDate(665);
		histories[recordId].push({
			id: id('e', ++sequence),
			from_status: old,
			to_status: row.status,
			action,
			changed_by: { id: previewSession('admin').user.id, name: 'Workspace user' },
			changed_at: new Date().toISOString(),
			note: action === 'renew' ? 'Extended the term.' : null
		});
		return subView(row, role);
	}
	function invoiceAction(
		/** @type {string} */ recordId,
		/** @type {string} */ action,
		role = 'admin'
	) {
		const visible = invoice(recordId, role);
		if (!visible.allowed_actions.includes(action))
			return fail('This invoice action is unavailable.');
		const row = invoices.find((item) => item.id === recordId);
		if (action === 'confirm') {
			row.status = cents(row.total) === 0n ? 'paid' : 'confirmed';
			row.confirmed_at = new Date().toISOString();
		}
		if (action === 'cancel') row.status = 'cancelled';
		if (action === 'send') row.sent_at = new Date().toISOString();
		return invoiceView(row, role);
	}
	function pay(/** @type {string} */ recordId, /** @type {any} */ body, role = 'admin') {
		const visible = invoice(recordId, role);
		if (visible.status !== 'confirmed') return fail('Only confirmed invoices accept payments.');
		const amount = cents(body.amount ?? visible.balance);
		if (amount <= 0n || amount > cents(visible.balance))
			return fail('Enter an amount up to the remaining balance.', 422, {
				amount: 'Amount must be greater than zero and no more than the balance.'
			});
		const row = invoices.find((item) => item.id === recordId);
		row.amount_paid = money(cents(row.amount_paid) + amount);
		if (cents(row.amount_paid) === cents(row.total)) row.status = 'paid';
		const payment = {
			id: id('8', ++sequence),
			invoice: { id: row.id, number: row.number },
			customer: row.customer,
			method: body.method ?? 'online',
			amount: money(amount),
			paid_on: body.paid_on ?? todayISO(),
			note: body.note ?? 'Frontend preview payment',
			recorded_by: { id: previewSession('admin').user.id, name: 'Workspace user' },
			created_at: new Date().toISOString()
		};
		payments.unshift(payment);
		return payment;
	}
	function saveSubscription(/** @type {any} */ body, /** @type {string} */ recordId = '') {
		const plan = plans.find((item) => item.id === body.plan_id) ?? plans[0];
		/** @type {Record<string, string>} */ const fields = {};
		if (body.expiry_date <= body.start_date)
			fields['expiry_date'] = 'Expiry must be after the start date.';
		body.lines?.forEach((/** @type {any} */ line, /** @type {number} */ index) => {
			if (line.quantity < plan.min_quantity)
				fields[`lines.${index}.quantity`] = `Use at least ${plan.min_quantity}.`;
		});
		if (Object.keys(fields).length) return fail('Check the highlighted fields.', 422, fields);
		if (!recordId) return subView(addSubscription(body), 'admin');
		const row = subscriptions.find((item) => item.id === recordId);
		if (!row || row.status !== 'draft') return fail('Only draft subscriptions can be edited.');
		Object.assign(row, body, { plan, ...price({ ...row, ...body }) });
		row.estimated_total = row.totals.total;
		return subView(row, 'admin');
	}
	function startRun() {
		const row = {
			id: id('a', ++sequence),
			run_date: todayISO(),
			status: 'running',
			started_at: new Date().toISOString(),
			finished_at: null,
			total_due: subscriptions.filter((sub) => sub.status === 'active').length,
			processed: 0,
			created: 0,
			skipped: 0,
			failed: 0,
			error: null,
			triggered_by: { id: previewSession('admin').user.id, name: 'Admin workspace' }
		};
		runs.unshift(row);
		return { ...row };
	}
	function run(/** @type {string} */ recordId) {
		const row = runs.find((item) => item.id === recordId);
		if (!row) return fail('Billing run not found.', 404);
		if (row.status === 'running') {
			const due = subscriptions.filter((sub) => sub.status === 'active');
			const sub = due[row.processed];
			if (sub) {
				if (
					invoices.some(
						(item) => item.subscription.id === sub.id && item.period_start === periodStart()
					)
				)
					row.skipped++;
				else {
					addInvoice(sub);
					row.created++;
				}
				row.processed++;
			}
			if (row.processed >= row.total_due) {
				row.status = 'finished';
				row.finished_at = new Date().toISOString();
			}
		}
		return {
			...row,
			created_count: row.created,
			skipped_count: row.skipped,
			failed_count: row.failed
		};
	}
	return {
		resourceDetail,
		saveResource,
		attribute,
		deactivate: (/** @type {string} */ resource, /** @type {string} */ recordId) => {
			const row = resourceDetail(resource, recordId);
			row.is_active = false;
			return row;
		},
		profile: () => profile,
		saveProfile: (/** @type {any} */ body) => {
			profile = { ...profile, ...body };
			Object.assign(customers[0], body);
			return profile;
		},
		list,
		subscription,
		invoice,
		price,
		subscriptionAction,
		invoiceAction,
		pay,
		saveSubscription,
		startRun,
		run,
		history: (/** @type {string} */ recordId) => histories[recordId] ?? [],
		product: (/** @type {string} */ recordId) =>
			products.find((item) => item.id === recordId) ?? fail('Product not found.', 404),
		plan: (/** @type {string} */ recordId) =>
			plans.find((item) => item.id === recordId) ?? fail('Plan not found.', 404),
		fromTemplate: (/** @type {string} */ recordId, /** @type {any} */ body) => {
			const template = templates.find((item) => item.id === recordId);
			if (!template) return fail('Template not found.', 404);
			return subView(
				addSubscription({
					...body,
					plan_id: template.plan_id,
					template_id: recordId,
					lines: template.lines
				}),
				'admin'
			);
		},
		loginUser,
		signupUser,
		getSessionUser,
		users
	};
}
