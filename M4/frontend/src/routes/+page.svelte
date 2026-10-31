<script>
	import { resolve } from '$app/paths';
	import { ArrowRight, Repeat2, ReceiptText, Wallet, Play } from '@lucide/svelte';
	import { auth } from '#lib/auth/session.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import { reveal } from '#lib/motion/reveal.js';
	const customer = $derived($auth.user?.role === 'customer');
	const subscriptionsPath = $derived(customer ? 'portal/subscriptions' : 'app/subscriptions');
	const invoicesPath = $derived(customer ? 'portal/invoices' : 'app/invoices');
</script>

<svelte:head>
	<title>Brightloop · Subscription management</title>
	<meta name="description" content="Manage subscriptions, invoices, and payments in Brightloop." />
</svelte:head>

<div class="flex min-h-svh flex-col" {@attach reveal}>
	<header class="border-b">
		<div class="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
			<a class="brand" href={resolve('/')} aria-label="Brightloop home">
				<span class="brand-symbol"><Repeat2 aria-hidden="true" /></span>Brightloop
			</a>
			{#if !$auth.user}<Button
					href={resolve('/[...path]', { path: 'login' })}
					variant="ghost"
					size="sm">Sign in</Button
				>{/if}
		</div>
	</header>
	<main
		id="main-content"
		class="mx-auto flex w-full max-w-xl flex-1 flex-col gap-6 px-4 py-12 sm:px-6 sm:py-20"
	>
		<div data-reveal class="flex flex-col gap-2">
			<h1 class="text-2xl font-semibold tracking-tight">Subscription management</h1>
			<p class="text-sm text-muted-foreground">Manage subscriptions, invoices, and payments.</p>
		</div>
		<div data-reveal>
			<Card.Root>
				<Card.Header
					><Card.Title>Workspace</Card.Title><Card.Description
						>Select a page to continue.</Card.Description
					></Card.Header
				>
				<Card.Content>
					<nav aria-label="Workspace pages" class="flex flex-col gap-1">
						<Button
							href={resolve('/[...path]', { path: subscriptionsPath })}
							variant="ghost"
							class="justify-start"
							><Repeat2 data-icon="inline-start" />Subscriptions<ArrowRight
								data-icon="inline-end"
								class="ml-auto"
							/></Button
						>
						<Button
							href={resolve('/[...path]', { path: invoicesPath })}
							variant="ghost"
							class="justify-start"
							><ReceiptText data-icon="inline-start" />Invoices<ArrowRight
								data-icon="inline-end"
								class="ml-auto"
							/></Button
						>
						<Button
							href={resolve('/[...path]', { path: customer ? 'portal/payments' : 'app/payments' })}
							variant="ghost"
							class="justify-start"
							><Wallet data-icon="inline-start" />Payments<ArrowRight
								data-icon="inline-end"
								class="ml-auto"
							/></Button
						>
						{#if !customer}<Button
								href={resolve('/[...path]', { path: 'app/billing-runs' })}
								variant="ghost"
								class="justify-start"
								><Play data-icon="inline-start" />Billing runs<ArrowRight
									data-icon="inline-end"
									class="ml-auto"
								/></Button
							>{/if}
					</nav>
				</Card.Content>
				<Card.Footer class="flex flex-wrap gap-2">
					<Button href={resolve('/[...path]', { path: $auth.user ? subscriptionsPath : 'login' })}
						>Open your workspace<ArrowRight data-icon="inline-end" /></Button
					>
					{#if !$auth.user}<Button
							href={resolve('/[...path]', { path: 'signup' })}
							variant="outline">Create an account</Button
						>{/if}
				</Card.Footer>
			</Card.Root>
		</div>
	</main>
</div>
