export interface paths {
	'/auth/me': {
		parameters: {
			query?: never;
			header?: never;
			path?: never;
			cookie?: never;
		};
		get: {
			parameters: {
				query?: never;
				header?: never;
				path?: never;
				cookie?: never;
			};
			requestBody?: never;
			responses: {
				/** @description Success */
				200: {
					headers: {
						[name: string]: unknown;
					};
					content: {
						'application/json': components['schemas']['User'];
					};
				};
			};
		};
		put?: never;
		post?: never;
		delete?: never;
		options?: never;
		head?: never;
		patch?: never;
		trace?: never;
	};
	'/auth/login': {
		parameters: {
			query?: never;
			header?: never;
			path?: never;
			cookie?: never;
		};
		get?: never;
		put?: never;
		post: {
			parameters: {
				query?: never;
				header?: never;
				path?: never;
				cookie?: never;
			};
			requestBody: {
				content: {
					'application/json': {
						email: string;
						password: string;
					};
				};
			};
			responses: {
				/** @description Success */
				200: {
					headers: {
						[name: string]: unknown;
					};
					content: {
						'application/json': components['schemas']['AuthSession'];
					};
				};
			};
		};
		delete?: never;
		options?: never;
		head?: never;
		patch?: never;
		trace?: never;
	};
}
export type webhooks = Record<string, never>;
export interface components {
	schemas: {
		User: {
			/** Format: uuid */
			id: string;
			email: string;
			full_name: string;
			/** @enum {string} */
			role: 'admin' | 'staff' | 'customer';
			customer_id: string | null;
		};
		AuthSession: {
			access_token: string;
			/** @enum {string} */
			token_type: 'bearer';
			user: components['schemas']['User'];
		};
	};
	responses: never;
	parameters: never;
	requestBodies: never;
	headers: never;
	pathItems: never;
}
export type $defs = Record<string, never>;
export type operations = Record<string, never>;
