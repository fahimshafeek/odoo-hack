<script lang="ts">
  interface Props {
    status?: string;
    text?: string;
  }
  let { status = 'draft', text = '' }: Props = $props();

  let displayLabel = $derived(text || status.toUpperCase());

  let badgeColor = $derived.by(() => {
    switch (status.toLowerCase()) {
      case 'draft':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'quotation':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'confirmed':
        return 'bg-indigo-100 text-indigo-700 border-indigo-300';
      case 'active':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'paused':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'closed':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  });
</script>

<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border {badgeColor}">
  {displayLabel}
</span>
