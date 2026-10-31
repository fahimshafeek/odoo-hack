<script>
	import * as Card from './ui/card/index.js';
	/** @type {{title: string, value: string | number, hint?: string, icon?: import('svelte').Component<any>}} */
	let { title, value, hint, icon: Icon } = $props();
</script>

<Card.Root
	><Card.Header
		><Card.Description>{title}</Card.Description>{#if Icon}<Card.Action
				><Icon aria-hidden="true" /></Card.Action
			>{/if}</Card.Header
	><Card.Content
		><p class="text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
		{#if hint}<p class="mt-2 text-xs text-muted-foreground">{hint}</p>{/if}</Card.Content
	></Card.Root
>
