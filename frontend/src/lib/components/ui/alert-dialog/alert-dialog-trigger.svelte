<script>
	import { AlertDialog as AlertDialogPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ref = $bindable(null), ...restProps } = $props();
</script>

<AlertDialogPrimitive.Trigger bind:ref data-slot="alert-dialog-trigger" {...restProps} />
