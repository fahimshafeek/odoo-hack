<script>
	import { Command as CommandPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ref = $bindable(null), ...restProps } = $props();
</script>

<CommandPrimitive.Loading bind:ref {...restProps} />
