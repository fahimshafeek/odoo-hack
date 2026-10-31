<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<optgroup
	bind:this={ref}
	data-slot="native-select-optgroup"
	class={cn('bg-[Canvas] text-[CanvasText]', className)}
	{...restProps}
>
	{@render children?.()}
</optgroup>
