(function() {
	'use strict';
	const MARKDOWN_IT_CDN = '/static/markdown-it.min.js';
	const HIGHLIGHT_JS_CDN = '/static/highlight.min.js';
	const HIGHLIGHT_LANG_GO_CDN = '/static/go.min.js';
	const HIGHLIGHT_LANG_RUST_CDN = '/static/rust.min.js';
	const HIGHLIGHT_LANG_TS_CDN = '/static/typescript.min.js';
	const HIGHLIGHT_LANG_PYTHON_CDN = '/static/python.min.js';
	const EDITOR_BUTTON_ID = 'custom-markdown-edit-btn';
	const MODAL_ID = 'markdown-editor-modal';
	const CHAT_INPUT_SELECTOR = '#chat-input';
	const VOICE_BUTTON_SELECTOR = '#voice-input-button';
	let md;
	let hljs;
	let editorModal = null;
	let editorInput = null;
	let markdownPreview = null;
	let mainChatInput = null;
	let mouseDownTarget = null;

	function loadScript(src) {
		return new Promise((resolve, reject) => {
			if (document.querySelector(`script[src="${src}"]`)) {
				resolve();
				return;
			}
			const script = document.createElement('script');
			script.src = src;
			script.onload = resolve;
			script.onerror = reject;
			document.head.appendChild(script);
		});
	}

	async function ensureDependencies() {
		try {
			if (typeof window.markdownit === 'undefined') {
				await loadScript(MARKDOWN_IT_CDN);
			}
			if (typeof window.hljs === 'undefined') {
				await loadScript(HIGHLIGHT_JS_CDN);
				await Promise.all([
					loadScript(HIGHLIGHT_LANG_GO_CDN),
					loadScript(HIGHLIGHT_LANG_RUST_CDN),
					loadScript(HIGHLIGHT_LANG_TS_CDN),
					loadScript(HIGHLIGHT_LANG_PYTHON_CDN)
				]).catch((e) =>
					console.warn('Could not load optional highlight.js languages:', e)
				);
			}
			md = window.markdownit({
				html: true,
				linkify: true,
				typographer: true,
				highlight: function(str, lang) {
					if (window.hljs) {
						hljs = window.hljs;
						if (lang && hljs.getLanguage(lang)) {
							try {
								return (
									'<pre class="hljs"><code>' +
									hljs.highlight(str, { language: lang, ignoreIllegals: true })
										.value +
									'</code></pre>'
								);
							} catch (__) {
							}
						}
						try {
							return (
								'<pre class="hljs"><code>' +
								hljs.highlightAuto(str).value +
								'</code></pre>'
							);
						} catch (__) {
						}
					}
					return (
						'<pre class="hljs"><code>' +
						md.utils.escapeHtml(str) +
						'</code></pre>'
					);
				}
			});
			hljs = window.hljs;
			console.log('Markdown Editor Dependencies loaded.');
		} catch (error) {
			console.error('Failed to load Markdown editor dependencies:', error);
		}
	}

	function createModal() {
		if (document.getElementById(MODAL_ID)) {
			return document.getElementById(MODAL_ID);
		}
		const modalHTML = `<div class="editor-container"><div class="editor-header"><div class="editor-title">Markdown编辑器</div><button class="close-btn"title="关闭 (Esc)">&times;</button></div><div class="editor-body"><textarea class="editor-input"placeholder="在这里输入 Markdown 内容..."></textarea><div class="preview-pane"><div class="markdown-preview"></div></div></div><div class="editor-footer"><button class="apply-btn"title="应用更改 (Ctrl+Enter)">应用</button></div></div>`;
		const modalDiv = document.createElement('div');
		modalDiv.id = MODAL_ID;
		modalDiv.innerHTML = modalHTML;
		document.body.appendChild(modalDiv);
		editorModal = modalDiv;
		editorInput = modalDiv.querySelector('.editor-input');
		markdownPreview = modalDiv.querySelector('.markdown-preview');
		const closeBtn = modalDiv.querySelector('.close-btn');
		const applyBtn = modalDiv.querySelector('.apply-btn');
		closeBtn.addEventListener('click', closeModal);
		applyBtn.addEventListener('click', applyChanges);
		editorInput.addEventListener('input', updatePreview);
		modalDiv.addEventListener('mousedown', (e) => {
			if (e.target === modalDiv) {
				mouseDownTarget = e.target;
			} else {
				mouseDownTarget = null;
			}
		});
		modalDiv.addEventListener('mouseup', (e) => {
			if (e.target === modalDiv && mouseDownTarget === modalDiv) {
				closeModal();
			}
			mouseDownTarget = null;
		});
		return modalDiv;
	}

	function openModal() {
		if (!md || !hljs) {
			console.error('Markdown editor dependencies not ready.');
			alert('编辑器依赖未能加载，请检查网络连接或控制台错误。');
			return;
		}
		if (!mainChatInput) {
			mainChatInput = document.querySelector(CHAT_INPUT_SELECTOR);
			if (!mainChatInput) {
				console.error('Chat input element not found when opening modal.');
				return;
			}
		}
		editorModal = createModal();
		const currentText = (mainChatInput.innerText || '').trim();
		editorInput.value = currentText;
		updatePreview();
		editorModal.classList.add('active');
		editorInput.focus();
	}

	function closeModal() {
		if (editorModal) {
			editorModal.classList.remove('active');
		}
	}

	function updatePreview() {
		if (!md || !editorInput || !markdownPreview) return;
		const content = editorInput.value;
		markdownPreview.innerHTML = md.render(content);
	}

	function applyChanges() {
		if (!mainChatInput || !editorInput) return;
		const newText = editorInput.value;
		mainChatInput.innerText = newText;
		const placeholderP = mainChatInput.querySelector('p.is-empty');
		if (newText.trim() === '') {
			if (!placeholderP) {
			}
		} else {
			if (placeholderP) {
			}
			mainChatInput.classList.remove('is-editor-empty');
			const parentPlaceholder = mainChatInput.querySelector('p.is-empty');
			if (parentPlaceholder) parentPlaceholder.classList.remove('is-empty');
		}
		mainChatInput.dispatchEvent(
			new Event('input', { bubbles: true, cancelable: true })
		);
		closeModal();
		mainChatInput.focus();
	}

	function injectEditorButton() {
		if (document.getElementById(EDITOR_BUTTON_ID)) {
			return;
		}
		mainChatInput = document.querySelector(CHAT_INPUT_SELECTOR);
		const voiceButton = document.querySelector(VOICE_BUTTON_SELECTOR);
		if (!mainChatInput || !voiceButton) {
			return;
		}
		const voiceButtonContainer = voiceButton.closest('.flex');
		if (!voiceButtonContainer || !voiceButtonContainer.parentElement) {
			console.warn('Could not find suitable container for Markdown button.');
			return;
		}
		const editButton = document.createElement('button');
		editButton.id = EDITOR_BUTTON_ID;
		editButton.className = 'markdown-edit-btn';
		editButton.type = 'button';
		editButton.title = 'Markdown 编辑 (打开/关闭)';
		editButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg"width="20"height="20"viewBox="0 0 24 24"fill="none"stroke="currentColor"stroke-width="2"stroke-linecap="round"stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>`;
		editButton.addEventListener('click', (e) => {
			e.preventDefault();
			if (editorModal && editorModal.classList.contains('active')) {
				closeModal();
			} else {
				openModal();
			}
		});
		voiceButtonContainer.parentElement.insertBefore(
			editButton,
			voiceButtonContainer
		);
		console.log('Markdown Editor button injected.');
	}

	function handleKeyDown(e) {
		if (editorModal && editorModal.classList.contains('active')) {
			if (e.key === 'Escape') {
				e.preventDefault();
				closeModal();
			}
			if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
				e.preventDefault();
				applyChanges();
			}
		}
	}

	ensureDependencies()
		.then(() => {
			injectEditorButton();
			const observer = new MutationObserver((mutationsList, observer) => {
				if (
					document.querySelector(CHAT_INPUT_SELECTOR) &&
					!document.getElementById(EDITOR_BUTTON_ID)
				) {
					injectEditorButton();
				}
			});
			observer.observe(document.body, { childList: true, subtree: true });
			document.addEventListener('keydown', handleKeyDown);
			console.log('Markdown Editor script initialized and observing DOM.');
		})
		.catch((error) => {
			console.error('Initialization failed:', error);
		});
})();
