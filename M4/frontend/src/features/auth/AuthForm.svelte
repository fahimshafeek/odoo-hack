<script>
	import { untrack } from 'svelte';
	import { SvelteURL } from 'svelte/reactivity';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { auth } from '#lib/auth/session.js';
	import { request } from '#src/api/resources.js';
	import { createForm } from '#lib/forms/form.js';
	import { passwordChecks } from '#lib/validators.js';
	import { Form, TextField } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import { authSchema, authDestination } from './schemas.js';
	import { cn } from '#lib/utils.js';
	/** @type {{mode:string}} */ let { mode } = $props();
	const token = untrack(() => page.url.searchParams.get('token') ?? '');
	const titles = {
		login: 'Sign in',
		signup: 'Create an account',
		forgot: 'Reset your password',
		reset: 'Choose a new password'
	};
	const title = $derived(titles[/** @type {keyof typeof titles} */ (mode)] ?? 'Sign in');
	const form = untrack(() =>
		createForm({
			schema: authSchema(mode),
			initialValues:
				mode === 'signup'
					? {
							role: 'customer',
							full_name: '',
							email: '',
							password: '',
							confirm_password: '',
							company_name: '',
							phone: ''
						}
					: mode === 'forgot'
						? { email: '' }
						: mode === 'reset'
							? { token, new_password: '', confirm_password: '' }
							: { email: '', password: '' }
		})
	);
	let complete = $state(false);
	let showPassword = $state(false);
	const checks = $derived(
		passwordChecks(String($form.values.password ?? $form.values.new_password ?? ''))
	);
	const checkLabels = {
		length: '9–128 characters',
		uppercase: 'An uppercase letter',
		lowercase: 'A lowercase letter',
		special: 'A special character'
	};
	async function enter(/** @type {string} */ role) {
		const next = authDestination(role, page.url.searchParams.get('next'));
		const destination = new SvelteURL(resolve('/[...path]', { path: next.path }), page.url.href);
		destination.search = next.search;
		// The pathname is resolved above; the validated local return URL preserves its filters.
		// eslint-disable-next-line svelte/no-navigation-without-resolve
		await goto(destination, {
			replaceState: true
		});
	}
	async function submit(/** @type {any} */ values) {
		if (mode === 'login') {
			await auth.login(values.email, values.password);
			if (!auth.user) throw new Error('Sign in failed. Please try again.');
			await enter(auth.user.role);
			return;
		}
		if (mode === 'signup') {
			const body = {
				role: $form.values.role || 'customer',
				email: values.email,
				password: values.password,
				full_name: values.full_name,
				company_name: values.company_name,
				phone: values.phone
			};
			const session = await request('POST', '/auth/signup', { body });
			auth.setSession(session);
			await enter(session.user.role);
			return;
		}
		await request('POST', mode === 'forgot' ? '/auth/forgot-password' : '/auth/reset-password', {
			body: mode === 'forgot' ? values : { token: values.token, new_password: values.new_password }
		});
		complete = true;
	}
</script>

<svelte:head><title>{title} · Brightloop</title></svelte:head>
<main
	id="main-content"
	class="mx-auto flex min-h-svh w-full max-w-sm flex-col justify-center gap-6 px-4 py-10"
>
	<a href={resolve('/')} class="w-fit text-lg font-semibold tracking-tight">Brightloop</a>
	<Card.Root
		><Card.Header
			><Card.Title class="text-xl">{title}</Card.Title><Card.Description
				>{mode === 'login'
					? 'Enter your account details.'
					: mode === 'signup'
						? 'Choose your account type and register.'
						: mode === 'forgot'
							? 'Enter your email to receive a reset link.'
							: 'Use a unique password for your account.'}</Card.Description
			></Card.Header
		><Card.Content>
			{#if complete}<div class="flex flex-col gap-4" role="status">
					<p class="text-sm">
						{mode === 'forgot'
							? 'If this email is registered, a reset link has been sent. The link expires in 5 minutes.'
							: 'Your password has been updated.'}
					</p>
					<Button variant="outline" href={resolve('/[...path]', { path: 'login' })}
						>Back to sign in</Button
					>
				</div>{:else if mode === 'reset' && !token}<div class="flex flex-col gap-4">
					<p class="text-sm text-muted-foreground">
						This reset link is missing its token. Request a new link to continue.
					</p>
					<Button variant="outline" href={resolve('/[...path]', { path: 'forgot-password' })}
						>Request reset link</Button
					>
				</div>{:else}
				{#if mode === 'login'}
					<div class="mb-4 rounded-lg border border-border/80 bg-muted/40 p-3 text-xs">
						<div class="flex items-center justify-between mb-2">
							<span class="font-medium text-foreground">Quick Demo Sign-In</span>
							<span class="text-[10px] text-muted-foreground">Click to fill</span>
						</div>
						<div class="grid grid-cols-3 gap-1.5">
							<button
								type="button"
								class="rounded-md border border-border bg-background p-2 text-center font-medium hover:bg-accent transition-colors shadow-xs"
								onclick={() => {
									form.setValue('email', 'admin@brightloop.io');
									form.setValue('password', 'BrightloopAdmin@123');
								}}
							>
								<span class="block text-primary font-semibold text-xs">Admin</span>
								<span class="block text-[10px] text-muted-foreground truncate">Dashboard</span>
							</button>
							<button
								type="button"
								class="rounded-md border border-border bg-background p-2 text-center font-medium hover:bg-accent transition-colors shadow-xs"
								onclick={() => {
									form.setValue('email', 'staff@brightloop.io');
									form.setValue('password', 'BrightloopStaff@123');
								}}
							>
								<span class="block text-primary font-semibold text-xs">Staff</span>
								<span class="block text-[10px] text-muted-foreground truncate">Workspace</span>
							</button>
							<button
								type="button"
								class="rounded-md border border-border bg-background p-2 text-center font-medium hover:bg-accent transition-colors shadow-xs"
								onclick={() => {
									form.setValue('email', 'customer@brightloop.io');
									form.setValue('password', 'BrightloopCust@123');
								}}
							>
								<span class="block text-primary font-semibold text-xs">Customer</span>
								<span class="block text-[10px] text-muted-foreground truncate">Portal</span>
							</button>
						</div>
					</div>
				{/if}
				<Form {form} onSubmit={submit}>
					{#if mode === 'signup'}
						<div class="flex flex-col gap-1.5">
							<span class="text-xs font-medium text-foreground">Select account type</span>
							<div class="grid grid-cols-3 gap-1.5">
								{#each [
									{ id: 'customer', label: 'Customer', desc: 'Portal' },
									{ id: 'staff', label: 'Staff', desc: 'Operations' },
									{ id: 'admin', label: 'Admin', desc: 'Full access' }
								] as item (item.id)}
									<button
										type="button"
										class={cn(
											'flex flex-col items-center justify-center rounded-md border p-2 text-center transition-colors',
											($form.values.role || 'customer') === item.id
												? 'border-primary bg-primary/10 text-primary font-medium ring-1 ring-primary'
												: 'border-border bg-background hover:bg-accent text-muted-foreground'
										)}
										onclick={() => form.setValue('role', item.id)}
									>
										<span class="text-xs font-semibold">{item.label}</span>
										<span class="text-[10px] opacity-80">{item.desc}</span>
									</button>
								{/each}
							</div>
						</div>
						<TextField
							name="full_name"
							label="Full name"
							autocomplete="name"
							required
						/>{/if}
					{#if mode !== 'reset'}<TextField
							name="email"
							type="email"
							label="Email"
							autocomplete="email"
							required
						/>{/if}
					{#if mode !== 'forgot'}<div class="flex flex-col gap-2">
							<TextField
								name={mode === 'reset' ? 'new_password' : 'password'}
								label={mode === 'reset' ? 'New password' : 'Password'}
								type={showPassword ? 'text' : 'password'}
								autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
								required
							/>
							<div class="flex justify-between gap-2">
								<Button
									variant="ghost"
									size="sm"
									onclick={() => (showPassword = !showPassword)}
									aria-pressed={showPassword}
									>{showPassword ? 'Hide password' : 'Show password'}</Button
								>{#if mode === 'login'}<Button
										variant="link"
										size="sm"
										href={resolve('/[...path]', { path: 'forgot-password' })}
										>Forgot password?</Button
									>{/if}
							</div>
						</div>{/if}
					{#if mode === 'signup' || mode === 'reset'}<ul
							class="grid grid-cols-2 gap-2 text-xs text-muted-foreground"
							aria-label="Password requirements"
						>
							{#each Object.entries(checkLabels) as [key, label] (key)}<li
									class={checks[/** @type {keyof typeof checks} */ (key)] ? 'text-foreground' : ''}
								>
									<span aria-hidden="true"
										>{checks[/** @type {keyof typeof checks} */ (key)] ? '✓' : '○'}</span
									>
									{label}<span class="sr-only"
										>{checks[/** @type {keyof typeof checks} */ (key)] ? ' met' : ' not met'}</span
									>
								</li>{/each}
						</ul>
						<TextField
							name="confirm_password"
							label="Confirm password"
							type={showPassword ? 'text' : 'password'}
							autocomplete="new-password"
							required
						/>{/if}
					{#if mode === 'signup'}<TextField
							name="company_name"
							label={$form.values.role === 'customer' ? 'Company (optional)' : 'Department / Team (optional)'}
							autocomplete="organization"
						/><TextField name="phone" label="Phone (optional)" type="tel" autocomplete="tel" />{/if}
					<Button
						type="submit"
						class="w-full"
						disabled={!$form.isValid || $form.isSubmitting}
						aria-busy={$form.isSubmitting}
						>{$form.isSubmitting
							? 'Please wait…'
							: mode === 'login'
								? 'Sign in'
								: mode === 'signup'
									? `Create ${$form.values.role || 'customer'} account`
									: mode === 'forgot'
										? 'Send reset link'
										: 'Update password'}</Button
					>
				</Form>{/if}
		</Card.Content></Card.Root
	>
	{#if mode === 'login'}<p class="text-center text-sm text-muted-foreground">
			Need an account? <a
				href={resolve('/[...path]', { path: 'signup' })}
				class="text-foreground underline underline-offset-4">Sign up</a
			>
		</p>{:else if mode === 'signup'}<p class="text-center text-sm text-muted-foreground">
			Already have an account? <a
				href={resolve('/[...path]', { path: 'login' })}
				class="text-foreground underline underline-offset-4">Sign in</a
			>
		</p>{:else if !complete}<a
			href={resolve('/[...path]', { path: 'login' })}
			class="text-center text-sm text-muted-foreground underline underline-offset-4"
			>Back to sign in</a
		>{/if}
</main>
