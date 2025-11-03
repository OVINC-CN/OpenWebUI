<script lang="ts">
	import DOMPurify from 'dompurify';
	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import { marked, type Token } from 'marked';
	import { unescapeHtml } from '$lib/utils';

	import { WEBUI_BASE_URL } from '$lib/constants';

	import CodeBlock from '$lib/components/chat/Messages/CodeBlock.svelte';
	import MarkdownInlineTokens from '$lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte';
	import KatexRenderer from './KatexRenderer.svelte';
	import AlertRenderer, { alertComponent } from './AlertRenderer.svelte';
	import Collapsible from '$lib/components/common/Collapsible.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Download from '$lib/components/icons/Download.svelte';

	import Source from './Source.svelte';
	import { settings } from '$lib/stores';
	import HtmlToken from './HTMLToken.svelte';

	export let id: string;
	export let tokens: Token[];
	export let top = true;
	export let attributes = {};

	export let done = true;

	export let save = false;
	export let preview = false;

	export let editCodeBlock = true;
	export let topPadding = false;

	export let onSave: Function = () => {};
	export let onUpdate: Function = () => {};
	export let onPreview: Function = () => {};

	export let onTaskClick: Function = () => {};
	export let onSourceClick: Function = () => {};

	const headerComponent = (depth: number) => {
		return 'h' + depth;
	};

	const exportTableToCSVHandler = (token, tokenIdx = 0) => {
		console.log('Exporting table to CSV');

		// Extract header row text and escape for CSV.
		const header = token.header.map((headerCell) => `"${headerCell.text.replace(/"/g, '""')}"`);

		// Create an array for rows that will hold the mapped cell text.
		const rows = token.rows.map((row) =>
			row.map((cell) => {
				// Map tokens into a single text
				const cellContent = cell.tokens.map((token) => token.text).join('');
				// Escape double quotes and wrap the content in double quotes
				return `"${cellContent.replace(/"/g, '""')}"`;
			})
		);

		// Combine header and rows
		const csvData = [header, ...rows];

		// Join the rows using commas (,) as the separator and rows using newline (\n).
		const csvContent = csvData.map((row) => row.join(',')).join('\n');

		// Log rows and CSV content to ensure everything is correct.
		console.log(csvData);
		console.log(csvContent);

		// To handle Unicode characters, you need to prefix the data with a BOM:
		const bom = '\uFEFF'; // BOM for UTF-8

		// Create a new Blob prefixed with the BOM to ensure proper Unicode encoding.
		const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=UTF-8' });

		// Use FileSaver.js's saveAs function to save the generated CSV file.
		saveAs(blob, `table-${id}-${tokenIdx}.csv`);
	};
</script>

<!-- {JSON.stringify(tokens)} -->
{#each tokens as token, tokenIdx (tokenIdx)}
	{#if token.type === 'hr'}
		<hr class="my-6 border-gray-100 dark:border-gray-850" />
	{:else if token.type === 'heading'}
		<svelte:element this={headerComponent(token.depth)} dir="auto" class="font-semibold leading-tight">
			<MarkdownInlineTokens
				id={`${id}-${tokenIdx}-h`}
				tokens={token.tokens}
				{done}
				{onSourceClick}
			/>
		</svelte:element>
	{:else if token.type === 'code'}
		{#if token.raw.includes('```')}
			<CodeBlock
				id={`${id}-${tokenIdx}`}
				collapsed={$settings?.collapseCodeBlocks ?? false}
				{token}
				lang={token?.lang ?? ''}
				code={token?.text ?? ''}
				{attributes}
				{save}
				{preview}
				edit={editCodeBlock}
				stickyButtonsClassName={topPadding ? 'top-7' : 'top-0'}
				onSave={(value) => {
					onSave({
						raw: token.raw,
						oldContent: token.text,
						newContent: value
					});
				}}
				{onUpdate}
				{onPreview}
			/>
		{:else}
			{token.text}
		{/if}
	{:else if token.type === 'table'}
		<div class="relative w-full group mb-3">
			<div class="scrollbar-hidden relative overflow-x-auto max-w-full">
				<table class="w-full text-[13px] text-gray-700 dark:text-gray-300 border-collapse">
					<thead>
						<tr>
							{#each token.header as header, headerIdx}
								<th
									scope="col"
									class="px-3 py-2 text-left font-semibold text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 text-[14px]"
								>
									<MarkdownInlineTokens
										id={`${id}-${tokenIdx}-header-${headerIdx}`}
										tokens={header.tokens}
										{done}
										{onSourceClick}
									/>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each token.rows as row, rowIdx}
							<tr>
								{#each row ?? [] as cell, cellIdx}
									<td
										class="px-3 py-2 text-left text-gray-700 dark:text-gray-300 {token.rows.length - 1 === rowIdx
											? ''
											: 'border-b border-gray-100 dark:border-gray-800'}"
									>
										<MarkdownInlineTokens
											id={`${id}-${tokenIdx}-row-${rowIdx}-${cellIdx}`}
											tokens={cell.tokens}
											{done}
											{onSourceClick}
										/>
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<div class=" absolute top-1 right-1.5 z-20 invisible group-hover:visible">
				<Tooltip content={$i18n.t('Export to CSV')}>
					<button
						class="p-1 rounded-lg bg-transparent transition"
						on:click={(e) => {
							e.stopPropagation();
							exportTableToCSVHandler(token, tokenIdx);
						}}
					>
						<Download className=" size-3.5" strokeWidth="1.5" />
					</button>
				</Tooltip>
			</div>
		</div>
	{:else if token.type === 'blockquote'}
		{@const alert = alertComponent(token)}
		{#if alert}
			<AlertRenderer {token} {alert} />
		{:else}
			<blockquote dir="auto" class="border-l-[3px] border-gray-300 dark:border-gray-700 pl-4 py-1 text-gray-600 dark:text-gray-400 bg-gray-50/30 dark:bg-gray-800/20 rounded-r">
				<svelte:self
					id={`${id}-${tokenIdx}`}
					tokens={token.tokens}
					{done}
					{editCodeBlock}
					{onTaskClick}
					{onSourceClick}
				/>
			</blockquote>
		{/if}
	{:else if token.type === 'list'}
		{#if token.ordered}
			<ol start={token.start || 1} dir="auto" class="space-y-2">
				{#each token.items as item, itemIdx}
					<li class="text-start leading-7">
						{#if item?.task}
							<input
								class="translate-y-[1px] -translate-x-1"
								type="checkbox"
								checked={item.checked}
								on:change={(e) => {
									onTaskClick({
										id: id,
										token: token,
										tokenIdx: tokenIdx,
										item: item,
										itemIdx: itemIdx,
										checked: e.target.checked
									});
								}}
							/>
						{/if}

						<svelte:self
							id={`${id}-${tokenIdx}-${itemIdx}`}
							tokens={item.tokens}
							top={token.loose}
							{done}
							{editCodeBlock}
							{onTaskClick}
							{onSourceClick}
						/>
					</li>
				{/each}
			</ol>
		{:else}
			<ul dir="auto" class="space-y-2">
				{#each token.items as item, itemIdx}
					<li class="text-start leading-7 {item?.task ? 'flex -translate-x-6.5 gap-3 ' : ''}">
						{#if item?.task}
							<input
								class=""
								type="checkbox"
								checked={item.checked}
								on:change={(e) => {
									onTaskClick({
										id: id,
										token: token,
										tokenIdx: tokenIdx,
										item: item,
										itemIdx: itemIdx,
										checked: e.target.checked
									});
								}}
							/>

							<div>
								<svelte:self
									id={`${id}-${tokenIdx}-${itemIdx}`}
									tokens={item.tokens}
									top={token.loose}
									{done}
									{editCodeBlock}
									{onTaskClick}
									{onSourceClick}
								/>
							</div>
						{:else}
							<svelte:self
								id={`${id}-${tokenIdx}-${itemIdx}`}
								tokens={item.tokens}
								top={token.loose}
								{done}
								{editCodeBlock}
								{onTaskClick}
								{onSourceClick}
							/>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	{:else if token.type === 'details'}
		<Collapsible
			title={token.summary}
			open={$settings?.expandDetails ?? false}
			attributes={token?.attributes}
			className="w-full space-y-1"
			dir="auto"
		>
			<div class=" mb-1.5" slot="content">
				<svelte:self
					id={`${id}-${tokenIdx}-d`}
					tokens={marked.lexer(token.text)}
					attributes={token?.attributes}
					{done}
					{editCodeBlock}
					{onTaskClick}
					{onSourceClick}
				/>
			</div>
		</Collapsible>
	{:else if token.type === 'html'}
		<HtmlToken {id} {token} {onSourceClick} />
	{:else if token.type === 'iframe'}
		<iframe
			src="{WEBUI_BASE_URL}/api/v1/files/{token.fileId}/content"
			title={token.fileId}
			width="100%"
			frameborder="0"
			onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"
		></iframe>
	{:else if token.type === 'paragraph'}
		<p dir="auto" class="leading-7">
			<MarkdownInlineTokens
				id={`${id}-${tokenIdx}-p`}
				tokens={token.tokens ?? []}
				{done}
				{onSourceClick}
			/>
		</p>
	{:else if token.type === 'text'}
		{#if top}
			<p>
				{#if token.tokens}
					<MarkdownInlineTokens
						id={`${id}-${tokenIdx}-t`}
						tokens={token.tokens}
						{done}
						{onSourceClick}
					/>
				{:else}
					{unescapeHtml(token.text)}
				{/if}
			</p>
		{:else if token.tokens}
			<MarkdownInlineTokens
				id={`${id}-${tokenIdx}-p`}
				tokens={token.tokens ?? []}
				{done}
				{onSourceClick}
			/>
		{:else}
			{unescapeHtml(token.text)}
		{/if}
	{:else if token.type === 'inlineKatex'}
		{#if token.text}
			<KatexRenderer content={token.text} displayMode={token?.displayMode ?? false} />
		{/if}
	{:else if token.type === 'blockKatex'}
		{#if token.text}
			<KatexRenderer content={token.text} displayMode={token?.displayMode ?? false} />
		{/if}
	{:else if token.type === 'space'}
		<div class="my-3" />
	{:else}
		{console.log('Unknown token', token)}
	{/if}
{/each}
