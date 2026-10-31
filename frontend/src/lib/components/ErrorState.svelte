<script>
	import { CircleAlert } from '@lucide/svelte';
	import * as Alert from './ui/alert/index.js';
	import { Button } from './ui/button/index.js';
	/** @type {{message?: string, onRetry?: () => void}} */
	let { message = 'We could not load this information. Please try again.', onRetry } = $props();
</script>

<Alert.Root variant="destructive" role="alert"
	><CircleAlert aria-hidden="true" /><Alert.Title>Unable to load data</Alert.Title
	><Alert.Description
		>{message}{#if onRetry}<div class="mt-3">
				<Button variant="outline" onclick={onRetry}>Try again</Button>
			</div>{/if}</Alert.Description
	></Alert.Root
>
