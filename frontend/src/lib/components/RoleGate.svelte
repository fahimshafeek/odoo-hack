<script>
	import { auth } from '#lib/auth/session.js';
	/** @type {{roles: string[], children: import('svelte').Snippet}} */
	let { roles, children } = $props();
</script>

{#if $auth.user && roles.includes($auth.user.role)}{@render children()}{/if}
