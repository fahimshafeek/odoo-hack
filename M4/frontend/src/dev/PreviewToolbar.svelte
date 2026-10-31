<script>
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { auth } from '#lib/auth/session.js';
	import { request } from '#src/api/resources.js';
	import { notify } from '#lib/notify.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	const queryClient = useQueryClient();
	let scenario = $state('normal');
	async function changeRole(/** @type {Event} */ event) {
		const role = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		const session = await request('POST', '/auth/login', {
			body: { email: `${role}@preview.brightloop.test`, password: 'Preview@123' }
		});
		auth.setSession(session);
		queryClient.clear();
		await goto(
			resolve('/[...path]', {
				path: role === 'customer' ? 'portal/subscriptions' : 'app/subscriptions'
			})
		);
	}
	async function changeScenario(/** @type {Event} */ event) {
		scenario = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		await request('POST', '/__preview/scenario', { body: { scenario } });
		await queryClient.invalidateQueries();
	}
	async function reset() {
		await request('POST', '/__preview/reset');
		scenario = 'normal';
		await queryClient.invalidateQueries();
		notify.success('Preview data reset.');
	}
</script>

<aside aria-label="Frontend preview controls" class="preview-toolbar">
	<div class="flex items-center gap-2">
		<strong>Frontend preview</strong><span class="hidden sm:inline">Sample data only</span>
	</div>
	<div class="flex flex-wrap items-center gap-2">
		<NativeSelect.Root
			aria-label="Preview role"
			value={$auth.user?.role ?? 'admin'}
			onchange={changeRole}
			><NativeSelect.Option value="admin">Admin</NativeSelect.Option><NativeSelect.Option
				value="staff">Staff</NativeSelect.Option
			><NativeSelect.Option value="customer">Customer</NativeSelect.Option></NativeSelect.Root
		>
		<NativeSelect.Root aria-label="Preview scenario" value={scenario} onchange={changeScenario}
			><NativeSelect.Option value="normal">Normal</NativeSelect.Option><NativeSelect.Option
				value="slow">Loading</NativeSelect.Option
			><NativeSelect.Option value="empty">Empty</NativeSelect.Option><NativeSelect.Option
				value="error">Error</NativeSelect.Option
			></NativeSelect.Root
		>
		<Button
			size="sm"
			variant="outline"
			href={resolve('/[...path]', {
				path: $auth.user?.role === 'customer' ? 'portal/subscriptions' : 'app/subscriptions'
			})}>Open workspace</Button
		><Button size="sm" variant="ghost" onclick={reset}>Reset</Button>
	</div>
</aside>
