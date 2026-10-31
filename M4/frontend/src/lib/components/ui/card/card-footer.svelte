<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
	bind:this={ref}
	data-slot="card-footer"
	class={cn('flex items-center rounded-b-xl border-t bg-muted/50 p-(--card-spacing)', className)}
	{...restProps}
>
	{@render children?.()}
</div>
