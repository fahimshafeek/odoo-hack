import { redirect } from '@sveltejs/kit';
import { auth } from '#lib/auth/session.js';
import { authDestination } from '#src/features/auth/schemas.js';

export async function load({ url }) {
	await auth.initialize();
	if (auth.user) {
		const next = authDestination(auth.user.role, url.searchParams.get('next'));
		redirect(307, '/' + next.path + (next.search || ''));
	}
	return {};
}
