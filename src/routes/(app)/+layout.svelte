<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, tick, getContext } from 'svelte';
	import { openDB, deleteDB } from 'idb';
	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;
	import mermaid from 'mermaid';

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade } from 'svelte/transition';

	import { getKnowledgeBases } from '$lib/apis/knowledge';
	import { getFunctions } from '$lib/apis/functions';
	import { getModels, getToolServersData, getVersionUpdates } from '$lib/apis';
	import { getAllTags } from '$lib/apis/chats';
	import { getPrompts } from '$lib/apis/prompts';
	import { getTools } from '$lib/apis/tools';
	import { getBanners } from '$lib/apis/configs';
	import { getUserSettings } from '$lib/apis/users';

	import { WEBUI_VERSION } from '$lib/constants';
	import { compareVersion } from '$lib/utils';

	import {
		config,
		user,
		settings,
		models,
		prompts,
		knowledge,
		tools,
		functions,
		tags,
		banners,
		showSettings,
		showChangelog,
		temporaryChatEnabled,
		toolServers,
		showSearch,
		showPreview,
		previewContent,
		showSidebar
	} from '$lib/stores';

	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import SettingsModal from '$lib/components/chat/SettingsModal.svelte';
	import ChangelogModal from '$lib/components/ChangelogModal.svelte';
	import AccountPending from '$lib/components/layout/Overlay/AccountPending.svelte';
	import UpdateInfoToast from '$lib/components/layout/UpdateInfoToast.svelte';
	import { get } from 'svelte/store';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ResultPreview from '$lib/components/chat/ResultPreview.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let DB = null;
	let localDBChats = [];

	let version;
	let sidebarWidth = '260px';
	let mainFr = 1;
	let previewFr = 1;
	let isResizing = false;

	function startResize(e) {
		isResizing = true;
		document.body.style.cursor = 'col-resize';
		const startX = e.clientX;
		const main = document.querySelector('main');
		const preview = document.querySelector('.preview-panel');
		const mainRect = main.getBoundingClientRect();
		const previewRect = preview.getBoundingClientRect();
		const total = mainRect.width + previewRect.width;
		function onMouseMove(ev) {
			const delta = ev.clientX - startX;
			let newMain = mainRect.width + delta;
			let newPreview = previewRect.width - delta;
			// 限制最小宽度
			if (newMain < 200) newMain = 200;
			if (newPreview < 200) newPreview = 200;
			mainFr = newMain / total;
			previewFr = newPreview / total;
		}
		function onMouseUp() {
			isResizing = false;
			document.body.style.cursor = '';
			window.removeEventListener('mousemove', onMouseMove);
			window.removeEventListener('mouseup', onMouseUp);
		}
		window.addEventListener('mousemove', onMouseMove);
		window.addEventListener('mouseup', onMouseUp);
	}

	$: gridCols = `${$showSidebar ? '260px' : '0'} ${mainFr}fr ${previewFr}fr`;

	onMount(async () => {
		if ($user === undefined || $user === null) {
			await goto('/auth');
		} else if (['user', 'admin'].includes($user?.role)) {
			try {
				// Check if IndexedDB exists
				DB = await openDB('Chats', 1);

				if (DB) {
					const chats = await DB.getAllFromIndex('chats', 'timestamp');
					localDBChats = chats.map((item, idx) => chats[chats.length - 1 - idx]);

					if (localDBChats.length === 0) {
						await deleteDB('Chats');
					}
				}

				console.log(DB);
			} catch (error) {
				// IndexedDB Not Found
			}

			const chatInputKeys = Object.keys(localStorage).filter((key) =>
				key.startsWith('chat-input-')
			);
			if (chatInputKeys.length > 0) {
				chatInputKeys.forEach((key) => {
					localStorage.removeItem(key);
				});
			}

			const userSettings = await getUserSettings(localStorage.token).catch((error) => {
				console.error(error);
				return null;
			});

			if (userSettings) {
				settings.set(userSettings.ui);
			} else {
				let localStorageSettings = {} as Parameters<(typeof settings)['set']>[0];

				try {
					localStorageSettings = JSON.parse(localStorage.getItem('settings') ?? '{}');
				} catch (e: unknown) {
					console.error('Failed to parse settings from localStorage', e);
				}

				settings.set(localStorageSettings);
			}

			models.set(
				await getModels(
					localStorage.token,
					$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
				)
			);

			banners.set(await getBanners(localStorage.token));
			tools.set(await getTools(localStorage.token));
			toolServers.set(await getToolServersData($i18n, $settings?.toolServers ?? []));

			document.addEventListener('keydown', async function (event) {
				const isCtrlPressed = event.ctrlKey || event.metaKey; // metaKey is for Cmd key on Mac
				// Check if the Shift key is pressed
				const isShiftPressed = event.shiftKey;

				// Check if Ctrl  + K is pressed
				if (isCtrlPressed && event.key.toLowerCase() === 'k') {
					event.preventDefault();
					console.log('search');
					showSearch.set(!$showSearch);
				}

				// Check if Ctrl + Shift + O is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'o') {
					event.preventDefault();
					console.log('newChat');
					document.getElementById('sidebar-new-chat-button')?.click();
				}

				// Check if Shift + Esc is pressed
				if (isShiftPressed && event.key === 'Escape') {
					event.preventDefault();
					console.log('focusInput');
					document.getElementById('chat-input')?.focus();
				}

				// Check if Ctrl + Shift + ; is pressed
				if (isCtrlPressed && isShiftPressed && event.key === ';') {
					event.preventDefault();
					console.log('copyLastCodeBlock');
					const button = [...document.getElementsByClassName('copy-code-button')]?.at(-1);
					button?.click();
				}

				// Check if Ctrl + Shift + C is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'c') {
					event.preventDefault();
					console.log('copyLastResponse');
					const button = [...document.getElementsByClassName('copy-response-button')]?.at(-1);
					console.log(button);
					button?.click();
				}

				// Check if Ctrl + Shift + S is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 's') {
					event.preventDefault();
					console.log('toggleSidebar');
					document.getElementById('sidebar-toggle-button')?.click();
				}

				// Check if Ctrl + Shift + Backspace is pressed
				if (
					isCtrlPressed &&
					isShiftPressed &&
					(event.key === 'Backspace' || event.key === 'Delete')
				) {
					event.preventDefault();
					console.log('deleteChat');
					document.getElementById('delete-chat-button')?.click();
				}

				// Check if Ctrl + . is pressed
				if (isCtrlPressed && event.key === '.') {
					event.preventDefault();
					console.log('openSettings');
					showSettings.set(!$showSettings);
				}

				// Check if Ctrl + / is pressed
				if (isCtrlPressed && event.key === '/') {
					event.preventDefault();
					console.log('showShortcuts');
					document.getElementById('show-shortcuts-button')?.click();
				}

				// Check if Ctrl + Shift + ' is pressed
				if (
					isCtrlPressed &&
					isShiftPressed &&
					(event.key.toLowerCase() === `'` || event.key.toLowerCase() === `"`)
				) {
					event.preventDefault();
					console.log('temporaryChat');
					temporaryChatEnabled.set(!$temporaryChatEnabled);
					await goto('/');
					const newChatButton = document.getElementById('new-chat-button');
					setTimeout(() => {
						newChatButton?.click();
					}, 0);
				}
			});

			if ($user?.role === 'admin' && ($settings?.showChangelog ?? true)) {
				showChangelog.set($settings?.version !== $config.version);
			}

			if ($user?.role === 'admin' || ($user?.permissions?.chat?.temporary ?? true)) {
				if ($page.url.searchParams.get('temporary-chat') === 'true') {
					temporaryChatEnabled.set(true);
				}

				if ($user?.permissions?.chat?.temporary_enforced) {
					temporaryChatEnabled.set(true);
				}
			}

			// Check for version updates
			if ($user?.role === 'admin') {
				// Check if the user has dismissed the update toast in the last 24 hours
				if (localStorage.dismissedUpdateToast) {
					const dismissedUpdateToast = new Date(Number(localStorage.dismissedUpdateToast));
					const now = new Date();

					if (now - dismissedUpdateToast > 24 * 60 * 60 * 1000) {
						checkForVersionUpdates();
					}
				} else {
					checkForVersionUpdates();
				}
			}
			await tick();
		}

		loaded = true;
	});

	const checkForVersionUpdates = async () => {
		version = await getVersionUpdates(localStorage.token).catch((error) => {
			return {
				current: WEBUI_VERSION,
				latest: WEBUI_VERSION
			};
		});
	};
</script>

<SettingsModal bind:show={$showSettings} />
<ChangelogModal bind:show={$showChangelog} />

{#if version && compareVersion(version.latest, version.current) && ($settings?.showUpdateToast ?? true)}
	<div class=" absolute bottom-8 right-8 z-50" in:fade={{ duration: 100 }}>
		<UpdateInfoToast
			{version}
			on:close={() => {
				localStorage.setItem('dismissedUpdateToast', Date.now().toString());
				version = null;
			}}
		/>
	</div>
{/if}

{#if $user}
	{#if $showSidebar}
		<div class="main-layout with-sidebar" style="grid-template-columns: {$showSidebar ? '260px' : '0'} 1fr {$showPreview ? '1fr' : ''};">
			<Sidebar />
			<main class="main-content"><slot /></main>
			{#if $showPreview}
				<div class="preview-panel">
					<ResultPreview content={$previewContent} />
				</div>
			{/if}
		</div>
	{:else}
		<div class="main-layout no-sidebar" style="grid-template-columns: 1fr {$showPreview ? '1fr' : ''};">
			<main class="main-content"><slot /></main>
			{#if $showPreview}
				<div class="preview-panel">
					<ResultPreview content={$previewContent} />
				</div>
			{/if}
		</div>
	{/if}
{/if}

<style>
	.loading {
		display: inline-block;
		clip-path: inset(0 1ch 0 0);
		animation: l 1s steps(3) infinite;
		letter-spacing: -0.5px;
	}

	@keyframes l {
		to {
			clip-path: inset(0 -1ch 0 0);
		}
	}

	pre[class*='language-'] {
		position: relative;
		overflow: auto;

		/* make space  */
		margin: 5px 0;
		padding: 1.75rem 0 1.75rem 1rem;
		border-radius: 10px;
	}

	pre[class*='language-'] button {
		position: absolute;
		top: 5px;
		right: 5px;

		font-size: 0.9rem;
		padding: 0.15rem;
		background-color: #828282;

		border: ridge 1px #7b7b7c;
		border-radius: 5px;
		text-shadow: #c4c4c4 0 0 2px;
	}

	pre[class*='language-'] button:hover {
		cursor: pointer;
		background-color: #bcbabb;
	}

	.main-layout.with-sidebar {
		display: grid;
		grid-template-columns: 260px 1fr 1fr;
		height: 100vh;
		width: 100vw;
		background: #fafafa;
	}
	.main-layout.no-sidebar {
		display: grid;
		grid-template-columns: 1fr 1fr;
		height: 100vh;
		width: 100vw;
		background: #fafafa;
	}
	.main-content, .preview-panel {
		min-width: 0;
		overflow: auto;
		height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: stretch;
		width: 100%;
		background: #fff;
		box-sizing: border-box;
	}
	.preview-panel {
		background: #f9f9f9;
		border-left: 1px solid #e5e7eb;
	}
</style>
