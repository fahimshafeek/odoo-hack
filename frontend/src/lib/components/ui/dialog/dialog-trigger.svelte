<script>
	import { Dialog as DialogPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ref = $bindable(null), type = 'button', ...restProps } = $props();
</script>

<DialogPrimitive.Trigger bind:ref data-slot="dialog-trigger" {type} {...restProps} />
