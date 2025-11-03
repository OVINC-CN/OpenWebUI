<script lang="ts">
	import DOMPurify from 'dompurify';

	import { onMount, getContext, createEventDispatcher, onDestroy, tick } from 'svelte';
	import * as FocusTrap from 'focus-trap';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { fade } from 'svelte/transition';
	import { flyAndScale } from '$lib/utils/transitions';
	import { marked } from 'marked';

	export let title = '';
	export let message = '';

	export let cancelLabel = $i18n.t('Cancel');
	export let confirmLabel = $i18n.t('Confirm');

	export let onConfirm = () => {};

	export let input = false;
	export let inputPlaceholder = '';
	export let inputValue = '';

	export let show = false;

	$: if (show) {
		init();
	}

	let modalElement = null;
	let mounted = false;

	let focusTrap: FocusTrap.FocusTrap | null = null;

	const init = () => {
		inputValue = '';
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			console.log('Escape');
			show = false;
		}

		if (event.key === 'Enter') {
			console.log('Enter');
			confirmHandler();
		}
	};

	const confirmHandler = async () => {
		show = false;
		await tick();
		await onConfirm();
		dispatch('confirm', inputValue);
	};

	onMount(() => {
		mounted = true;
	});

	$: if (mounted) {
		if (show && modalElement) {
			document.body.appendChild(modalElement);
			focusTrap = FocusTrap.createFocusTrap(modalElement);
			focusTrap.activate();

			window.addEventListener('keydown', handleKeyDown);
			document.body.style.overflow = 'hidden';
		} else if (modalElement) {
			focusTrap.deactivate();

			window.removeEventListener('keydown', handleKeyDown);
			document.body.removeChild(modalElement);

			document.body.style.overflow = 'unset';
		}
	}

	onDestroy(() => {
		show = false;
		if (focusTrap) {
			focusTrap.deactivate();
		}
		if (modalElement) {
			document.body.removeChild(modalElement);
		}
	});
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		bind:this={modalElement}
		class=" fixed top-0 right-0 left-0 bottom-0 bg-black/60 w-full h-screen max-h-[100dvh] flex justify-center z-99999999 overflow-hidden overscroll-contain"
		in:fade={{ duration: 10 }}
		on:mousedown={() => {
			show = false;
		}}
	>
		<div
			class=" m-auto max-w-full w-[32rem] mx-2 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-xl max-h-[100dvh] shadow-3xl border border-white dark:border-gray-850"
			in:flyAndScale
			on:mousedown={(e) => {
				e.stopPropagation();
			}}
		>
		<div class="px-4 pt-3.5 pb-1.5 flex items-center justify-between">
			<div class="text-sm font-medium text-gray-900 dark:text-gray-100">
				{#if title !== ''}
					{title}
				{:else}
					{$i18n.t('Confirm your action')}
				{/if}
			</div>
			<button
				class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
				on:click={() => {
					show = false;
					dispatch('cancel');
				}}
				type="button"
			>
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
		<div class="px-4 pb-3.5 flex flex-col">
				<slot>
					<div class="text-xs text-gray-600 dark:text-gray-400 flex-1 mt-3">
						{#if message !== ''}
							{@const html = DOMPurify.sanitize(marked.parse(message))}
							{@html html}
						{:else}
							{$i18n.t('This action cannot be undone. Do you wish to continue?')}
						{/if}

						{#if input}
							<textarea
								bind:value={inputValue}
								placeholder={inputPlaceholder ? inputPlaceholder : $i18n.t('Enter your message')}
								class="w-full mt-2 rounded-lg px-3 py-2 text-xs text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 outline-none focus:ring-1 focus:ring-gray-900 dark:focus:ring-gray-100 resize-none transition"
								rows="3"
								required
							/>
						{/if}
					</div>
				</slot>

			<div class="mt-3 flex justify-end gap-1.5">
				<button
					class="text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white font-medium px-3 py-1.5 rounded-full transition"
					on:click={() => {
						show = false;
						dispatch('cancel');
					}}
					type="button"
				>
					{cancelLabel}
				</button>
				<button
					class="text-xs bg-gray-900 hover:bg-gray-850 text-gray-100 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-800 font-medium px-3 py-1.5 rounded-full transition"
					on:click={() => {
						confirmHandler();
					}}
					type="button"
				>
					{confirmLabel}
				</button>
			</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
