<script lang="ts">
	import Pagination from '$lib/components/common/Pagination.svelte';
	import { getContext, onMount } from 'svelte';
	import { listAllCreditLog } from '$lib/apis/credit';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import DeleteCreditLogModal from '$lib/components/admin/Users/DeleteCreditLogModal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let page = 1;
	let limit = 30;
	let total = null;

	let query = '';

	let logs = [];
	const doQuery = async () => {
		const data = await listAllCreditLog(localStorage.token, page, limit, query).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (data) {
			total = data?.total ?? 0;
			logs = data?.results ?? [];
		}
	};

	const formatDate = (t: number): string => {
		return new Date(t * 1000).toLocaleString();
	};

	const formatDesc = (log): string => {
		const usage = log?.detail?.usage ?? {};
		if (usage && Object.keys(usage).length > 0) {
			if (usage.total_price !== undefined && usage.total_price !== null) {
				return `-${Math.round(usage.total_price * 1e6) / 1e6}`;
			}
			if (usage.request_unit_price) {
				return `-${usage.request_unit_price / 1e6}`;
			}
			if (usage.prompt_unit_price || usage.completion_unit_price) {
				return `-${Math.round(usage.prompt_tokens * usage.prompt_unit_price + usage.completion_tokens * usage.completion_unit_price) / 1e6}`;
			}
		}
		return log?.detail?.desc;
	};

	let showDeleteLogModal = false;

	$: if (page !== undefined || query !== undefined) {
		doQuery();
	}
</script>

<DeleteCreditLogModal
	bind:show={showDeleteLogModal}
	on:save={async () => {
		page = 1;
		await doQuery();
	}}
/>

<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		<div class="flex-shrink-0">
			{$i18n.t('Credit Log')}
		</div>
	</div>

	<div class="flex gap-1">
		<div class=" flex w-full space-x-2">
			<div class="flex flex-1 w-full">
				<div class=" self-center ml-1 mr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<input
					class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={query}
					placeholder={$i18n.t('Fuzzy Search Username')}
				/>
			</div>
			<div>
				<Tooltip content={$i18n.t('Open Delete Log Modal')}>
					<button
						class=" p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
						on:click={() => {
							showDeleteLogModal = !showDeleteLogModal;
						}}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
							/>
						</svg>
					</button>
				</Tooltip>
			</div>
		</div>
	</div>
</div>
{#if total === null}
	<div class="my-10">
		<Spinner className="size-5" />
	</div>
{:else}
	<div
		class="mt-2 scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm"
	>
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm}"
		>
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
				<tr>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Date')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('User')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Credit')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Model')}
					</th>
					<th scope="col" class="px-3 py-1.5 select-none w-3">
						{$i18n.t('Desc')}
					</th>
				</tr>
			</thead>
			<tbody>
				{#each logs as log}
					<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs group">
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
							<div class=" line-clamp-1">
								{formatDate(log.created_at)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
							<div class=" line-clamp-1">
								{log.username || log.user_id}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
							<div class=" line-clamp-1">
								{parseFloat(log.credit).toFixed(6)}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
							<div class=" line-clamp-1">
								{log.detail?.api_params?.model?.name || log.detail?.api_params?.model?.id || '- -'}
							</div>
						</td>
						<td class="px-3 py-1.5 text-left font-medium text-gray-900 dark:text-white w-fit">
							<div class=" line-clamp-1">
								{formatDesc(log)}
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<Pagination bind:page count={total} perPage={limit} />
{/if}
