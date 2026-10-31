<script>
	import { Inbox } from '@lucide/svelte';
	import * as Empty from './ui/empty/index.js';
	/** @type {{title?: string, description?: string, action?: import('svelte').Snippet}} */
	let {
		title = 'Nothing here yet',
		description = 'New records will appear here when they are ready.',
		action
	} = $props();
</script>

<Empty.Root
	><Empty.Header
		><Empty.Media variant="icon"><Inbox aria-hidden="true" /></Empty.Media><Empty.Title
			>{title}</Empty.Title
		><Empty.Description>{description}</Empty.Description></Empty.Header
	>{#if action}<Empty.Content>{@render action()}</Empty.Content>{/if}</Empty.Root
>
