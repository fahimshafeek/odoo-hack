import { get, writable } from 'svelte/store';

/** @param {Record<string, any>} values @param {string} path */
export function getFieldValue(values, path) {
	return path
		.split('.')
		.reduce(
			(value, key) => (value != null && Object.hasOwn(value, key) ? value[key] : undefined),
			values
		);
}

/** Validated form state with nested server errors and duplicate-submit protection (A6).
 * @param {{schema: import('zod').ZodType, initialValues: Record<string, any>}} options */
export function createForm({ schema, initialValues }) {
	const initial = () => structuredClone(initialValues);
	/** @type {import('svelte/store').Writable<{values: Record<string, any>, errors: Record<string, string>, formError: string, isValid: boolean, isSubmitting: boolean, submitted: boolean}>} */
	const state = writable({
		values: initial(),
		errors: {},
		formError: '',
		isValid: schema.safeParse(initialValues).success,
		isSubmitting: false,
		submitted: false
	});
	const touched = new Set();
	/** @type {Record<string, string>} */
	let serverErrors = {};
	/** @param {boolean} [all] */
	function validate(all = false) {
		const current = get(state);
		const result = schema.safeParse(current.values);
		/** @type {Record<string, string>} */
		const errors = {};
		if (!result.success)
			for (const issue of result.error.issues) {
				const path = issue.path.join('.');
				if ((all || touched.has(path)) && !errors[path]) errors[path] = issue.message;
			}
		state.update((value) => ({
			...value,
			errors: { ...errors, ...serverErrors },
			isValid: result.success && !Object.keys(serverErrors).length
		}));
		return result;
	}
	/** @param {string} path @param {any} value */
	function setValue(path, value) {
		if (path.split('.').some((key) => ['__proto__', 'prototype', 'constructor'].includes(key)))
			throw new Error('Invalid field path');
		for (const key of Object.keys(serverErrors)) {
			if (key === path || key.startsWith(`${path}.`) || path.startsWith(`${key}.`))
				delete serverErrors[key];
		}
		state.update((current) => {
			const values = structuredClone(current.values);
			const keys = path.split('.');
			let target = values;
			for (const key of keys.slice(0, -1)) {
				if (!Object.hasOwn(target, key)) throw new Error(`Unknown field: ${path}`);
				target = target[key];
			}
			target[keys.at(-1) ?? path] = value;
			return { ...current, values, formError: '' };
		});
		touched.add(path);
		validate(get(state).submitted);
	}
	const form = {
		subscribe: state.subscribe,
		setValue,
		validate,
		/** @param {(values: any) => any | Promise<any>} onSubmit */
		async submit(onSubmit) {
			if (get(state).isSubmitting) return false;
			state.update((value) => ({ ...value, submitted: true, formError: '' }));
			const result = validate(true);
			if (!result.success || !get(state).isValid) return false;
			state.update((value) => ({ ...value, isSubmitting: true }));
			try {
				await onSubmit(result.data);
				return true;
			} catch (error) {
				applyServerErrors(form, error);
				return false;
			} finally {
				state.update((value) => ({ ...value, isSubmitting: false }));
			}
		},
		/** @param {Record<string, string>} errors @param {string} [formError] */
		setErrors(errors, formError = '') {
			serverErrors = { ...errors };
			state.update((value) => ({
				...value,
				errors,
				formError,
				isValid: schema.safeParse(value.values).success && !Object.keys(errors).length
			}));
		},
		/** @param {Record<string, any>} [values] */
		reset(values = initial()) {
			touched.clear();
			serverErrors = {};
			state.set({
				values: structuredClone(values),
				errors: {},
				formError: '',
				isValid: schema.safeParse(values).success,
				isSubmitting: false,
				submitted: false
			});
		}
	};
	return form;
}

/** Map dotted A3 errors onto known inputs; unknown fields become a form alert.
 * @param {ReturnType<typeof createForm>} form @param {any} error */
export function applyServerErrors(form, error) {
	const values = get(form).values;
	/** @type {Record<string, string>} */
	const fields = {};
	const general = [];
	for (const [path, message] of Object.entries(error?.fields ?? {})) {
		if (getFieldValue(values, path) !== undefined) fields[path] = String(message);
		else general.push(String(message));
	}
	form.setErrors(
		fields,
		general.join(' ') ||
			(Object.keys(fields).length
				? ''
				: error?.message || 'We could not save your changes. Please try again.')
	);
}
