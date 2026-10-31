<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
	bind:this={ref}
	data-slot="field-group"
	class={cn(
		'group/field-group @container/field-group flex w-full flex-col gap-5 data-[slot=checkbox-group]:gap-3 *:data-[slot=field-group]:gap-4',
		className
	)}
	{...restProps}
>
	{@render children?.()}
</div>
