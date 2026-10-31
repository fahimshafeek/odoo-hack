<script>
	import AuthForm from './AuthForm.svelte';
	/** @type {{mode?:string}} */ let { mode = 'login' } = $props();
</script>

{#key mode}<AuthForm {mode} />{/key}
