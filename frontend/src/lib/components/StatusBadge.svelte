<script>
	import { Check, Circle, Clock3, Pause, X } from '@lucide/svelte';
	import { Badge } from './ui/badge/index.js';
	import { statusPresentation } from '#lib/status.js';
	/** @type {{kind: keyof typeof import('#lib/status.js').statuses, value: string | boolean}} */
	let { kind, value } = $props();
	const status = $derived(statusPresentation(kind, value));
	const Icon = $derived(
		value === 'paused'
			? Pause
			: status.tone === 'active'
				? Check
				: status.tone === 'danger'
					? X
					: status.tone === 'warning'
						? Clock3
						: Circle
	);
</script>

{#if status.label}<Badge variant={status.tone}><Icon aria-hidden="true" />{status.label}</Badge
	>{/if}
