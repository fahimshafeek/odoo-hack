const browser = typeof window !== 'undefined';
import { goto } from '$app/navigation';
import { resolve } from '$app/paths';
import { writable, get } from 'svelte/store';
import { createApiClient } from '#src/api/client.js';

const key = 'brightloop.access_token';
/** @typedef {import('../../api/schema').components['schemas']['User']} User */
/** @type {string | null} */
let token = null;
/** @type {Promise<void> | null} */
let initialization = null;
/** @type {import('svelte/store').Writable<{user: User | null, isLoading: boolean, error: string | null}>} */
const state = writable({ user: null, isLoading: true, error: null });

/** Persist AUTH-4 credentials while tolerating blocked browser storage. @param {string | null} value */
function saveToken(value) {
	token = value;
	if (!browser) return;
	try {
		if (value) localStorage.setItem(key, value);
		else localStorage.removeItem(key);
	} catch {
		/* The in-memory session still works when storage is unavailable. */
	}
}

/** Clear cached identity and return to login after expired credentials. */
function expire() {
	saveToken(null);
	state.set({ user: null, isLoading: false, error: null });
	if (browser) void goto(resolve('/[...path]', { path: 'login' }), { replaceState: true });
}

export const api = createApiClient({ getToken: () => token, onUnauthorized: expire });

/** Hydrate the browser session through /auth/me; never trust a stored role. */
async function initialize() {
	if (!browser) return;
	if (initialization) return initialization;
	initialization = (async () => {
		try {
			token = localStorage.getItem(key);
		} catch {
			token = null;
		}
		if (!token) {
			state.set({ user: null, isLoading: false, error: null });
			return;
		}
		try {
			const { data } = await api.GET('/auth/me');
			state.set({ user: data ?? null, isLoading: false, error: null });
		} catch (error) {
			state.set({
				user: null,
				isLoading: false,
				error: error instanceof Error ? error.message : 'Cannot reach the server.'
			});
		}
	})();
	return initialization;
}

/** Accept only the canonical A4 AuthSession, supplied by the API. @param {import('../../api/schema').components['schemas']['AuthSession']} session */
function setSession(session) {
	saveToken(session.access_token);
	state.set({ user: session.user, isLoading: false, error: null });
}

/** Authenticate via M1's endpoint. @param {string} email @param {string} password */
async function login(email, password) {
	const { data } = await api.POST('/auth/login', { body: { email, password } });
	if (data) setSession(data);
}

/** End AUTH-4 session, including the account's query cache. */
function logout() {
	initialization = null;
	expire();
}

export const auth = {
	subscribe: state.subscribe,
	initialize,
	login,
	logout,
	setSession,
	get user() {
		return get(state).user;
	},
	get isLoading() {
		return get(state).isLoading;
	}
};

/** Svelte's AUTH-4 session is a readable store, with the same shared auth methods. */
export function useAuth() {
	return auth;
}
