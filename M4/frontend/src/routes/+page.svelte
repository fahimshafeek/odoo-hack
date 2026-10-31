<script>
	import { resolve } from '$app/paths';
	import { ArrowRight, Repeat2, ReceiptText, Wallet, Play, ChevronRight } from '@lucide/svelte';
	import { auth } from '#lib/auth/session.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
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

{#snippet workspaceLink(path = '', label = '', description = '', Icon = Repeat2)}
	<Button
		href={resolve('/[...path]', { path })}
		variant="ghost"
		class="h-auto justify-start gap-3 px-3 py-4"
	>
		<Icon data-icon="inline-start" />
		<span class="flex min-w-0 flex-col items-start gap-1 text-left whitespace-normal">
			<span>{label}</span>
			<span class="text-xs font-normal text-muted-foreground">{description}</span>
		</span>
		<ChevronRight data-icon="inline-end" class="ml-auto" />
	</Button>
{/snippet}

<div class="flex min-h-svh flex-col" {@attach reveal}>
	<header class="border-b">
		<div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
			<a class="brand" href={resolve('/')} aria-label="Brightloop home">
				<span class="brand-symbol"><Repeat2 aria-hidden="true" /></span>Brightloop
			</a>
			<Button
				href={resolve('/[...path]', { path: $auth.user ? subscriptionsPath : 'login' })}
				variant="ghost"
				size="sm"
			>
				{$auth.user ? 'Workspace' : 'Sign in'}<ArrowRight data-icon="inline-end" />
			</Button>
		</div>
	</header>
	<main
		id="main-content"
		class="mx-auto grid w-full max-w-6xl flex-1 items-center gap-12 px-5 py-14 sm:px-8 sm:py-20 lg:grid-cols-2 lg:gap-16 lg:py-24"
	>
		<section class="flex flex-col items-start gap-6">
			<p data-reveal class="text-sm font-medium text-muted-foreground">Subscription management</p>
			<h1 data-reveal class="hero-title">From plans<br />to payments.</h1>
			<p data-reveal class="max-w-md text-base leading-7 text-muted-foreground">
				Manage plans, recurring billing, and payments in one workspace.
			</p>
			<div data-reveal class="flex flex-wrap gap-3 pt-1">
				<Button
					size="lg"
					href={resolve('/[...path]', { path: $auth.user ? subscriptionsPath : 'login' })}
					>Open workspace<ArrowRight data-icon="inline-end" /></Button
				>
				<Button
					size="lg"
					variant="outline"
					href={resolve('/[...path]', { path: $auth.user ? invoicesPath : 'signup' })}
					>{$auth.user ? 'View invoices' : 'Create an account'}</Button
				>
			</div>
			<div
				data-reveal
				class="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground"
				aria-label="Workflow: subscription to invoice to payment"
			>
				<span>Subscription</span><ArrowRight class="size-3" aria-hidden="true" /><span>Invoice</span
				><ArrowRight class="size-3" aria-hidden="true" /><span>Payment</span><Repeat2
					class="ml-1 size-3.5"
					aria-hidden="true"
				/>
			</div>
		</section>
		<section data-reveal class="workspace-preview" aria-label="Open a workspace page">
			<svg class="cycle-outline" viewBox="0 0 480 480" fill="none" aria-hidden="true">
				<circle cx="240" cy="240" r="222" stroke="currentColor" />
				<path
					d="M240 18a222 222 0 0 1 222 222M240 462A222 222 0 0 1 18 240"
					stroke="var(--muted-foreground)"
					stroke-dasharray="4 8"
				/>
			</svg>
			<Card.Root class="relative">
				<Card.Header>
					<Card.Title>Workspace</Card.Title>
					<Card.Description>Select a page to continue.</Card.Description>
					<Card.Action
						><Badge variant="outline" class="capitalize">{$auth.user?.role ?? 'Quick access'}</Badge
						></Card.Action
					>
				</Card.Header>
				<Card.Content>
					<nav aria-label="Workspace pages" class="flex flex-col divide-y">
						{@render workspaceLink(
							subscriptionsPath,
							'Subscriptions',
							'Plans, status, and renewal dates',
							Repeat2
						)}
						{@render workspaceLink(
							invoicesPath,
							'Invoices',
							'Invoices, balances, and due dates',
							ReceiptText
						)}
						{@render workspaceLink(
							customer ? 'portal/payments' : 'app/payments',
							'Payments',
							'Payment records and history',
							Wallet
						)}
						{#if !customer}{@render workspaceLink(
								'app/billing-runs',
								'Billing runs',
								'Run and review recurring billing',
								Play
							)}{/if}
					</nav>
				</Card.Content>
				<Card.Footer class="border-t py-3">
					<p class="text-xs text-muted-foreground">
						{#if $auth.user}Signed in as {$auth.user.full_name}{:else}Sign in to access your
							workspace.{/if}
					</p>
				</Card.Footer>
			</Card.Root>
		</section>
	</main>
	<footer class="border-t">
		<div
			class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-5 text-xs text-muted-foreground sm:px-8"
		>
			<span>Brightloop</span><span>Subscriptions · Invoices · Payments</span>
		</div>
	</footer>
</div>

<style>
	.hero-title {
		font-size: clamp(2.8rem, 5.6vw, 4.75rem);
		font-weight: 600;
		line-height: 1.06;
		letter-spacing: -0.055em;
	}
	.workspace-preview {
		position: relative;
		isolation: isolate;
	}
	.cycle-outline {
		position: absolute;
		inset: -2rem;
		z-index: -1;
		width: calc(100% + 4rem);
		height: calc(100% + 4rem);
		color: var(--border);
		pointer-events: none;
	}
	@media (max-width: 63.999rem) {
		.cycle-outline {
			display: none;
		}
	}
</style>
