(function() {
	function checkIsEditPage() {
		return window.location.href.includes('/functions');
	}

	let isCurrentlyEditPage = checkIsEditPage();

	function onRouteChange() {
		isCurrentlyEditPage = checkIsEditPage();
		if (isCurrentlyEditPage) {
			if (mutationObserverActive) {
				mutationObserver.disconnect();
				mutationObserverActive = false;
			}
		} else {
			initializeAllCodeBlocks();
			if (!mutationObserverActive) {
				mutationObserver.observe(document.body, { childList: true, subtree: true });
				mutationObserverActive = true;
			}
		}
	}

	const originalPushState = history.pushState;
	history.pushState = function(state, title, url) {
		originalPushState.apply(history, arguments);
		onRouteChange();
	};
	window.addEventListener('popstate', onRouteChange);
	const observedCodeBlocks = new WeakSet();
	const resizeObserver = new ResizeObserver((entries) => {
		if (isCurrentlyEditPage) return;
		for (const entry of entries) {
			const editorRoot = entry.target;
			if (!editorRoot.classList.contains('cm-editor')) continue;
			updateCodeBlock(editorRoot);
		}
	});

	function updateCodeBlock(editorRoot) {
		if (editorRoot.querySelector('.code-expand-btn')) return;
		const height = editorRoot.scrollHeight;
		if (height > 400) {
			editorRoot.id = 'collapsed';
			const expandBtn = document.createElement('button');
			expandBtn.className = 'code-expand-btn';
			expandBtn.id = 'collapsed';
			editorRoot.appendChild(expandBtn);
			editorRoot.style.height = '400px';
		}
	}

	function initializeCodeBlock(editorRoot) {
		if (observedCodeBlocks.has(editorRoot)) return;
		observedCodeBlocks.add(editorRoot);
		resizeObserver.observe(editorRoot);
		updateCodeBlock(editorRoot);
	}

	function initializeAllCodeBlocks() {
		if (isCurrentlyEditPage) return;
		document.querySelectorAll('.cm-editor').forEach(initializeCodeBlock);
	}

	const mutationObserver = new MutationObserver((mutations) => {
		if (isCurrentlyEditPage) return;
		let hasNewCodeBlocks = false;
		mutations.forEach((mutation) => {
			mutation.addedNodes.forEach((node) => {
				if (node.nodeType !== 1) return;
				if (node.classList?.contains('cm-editor')) {
					initializeCodeBlock(node);
					hasNewCodeBlocks = true;
				} else {
					const matches = node.querySelectorAll?.('.cm-editor') || [];
					matches.forEach((el) => {
						initializeCodeBlock(el);
						hasNewCodeBlocks = true;
					});
				}
			});
		});
		if (hasNewCodeBlocks) requestAnimationFrame(initializeAllCodeBlocks);
	});
	let mutationObserverActive = false;
	document.addEventListener('click', function(evt) {
		if (!evt.target.classList.contains('code-expand-btn')) return;
		const editorRoot = evt.target.closest('.cm-editor');
		if (!editorRoot) return;
		const isCollapsed = editorRoot.id === 'collapsed';
		requestAnimationFrame(() => {
			if (isCollapsed) {
				const scroller = editorRoot.querySelector('.cm-scroller');
				editorRoot.style.height = `${scroller.scrollHeight}px`;
				editorRoot.id = 'expanded';
				evt.target.id = 'expanded';
			} else {
				editorRoot.style.height = '400px';
				editorRoot.id = 'collapsed';
				evt.target.id = 'collapsed';
				const scrollTarget = editorRoot.closest('.relative.my-2')?.parentElement;
				scrollTarget?.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});

	function init() {
		isCurrentlyEditPage = checkIsEditPage();
		if (!isCurrentlyEditPage) initializeAllCodeBlocks();
		mutationObserver.observe(document.body, { childList: true, subtree: true });
		mutationObserverActive = true;
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
	window.addEventListener('error', (error) => {
		console.error('Code block error:', error);
	});
	window.addEventListener('unhandledrejection', (event) => {
		console.error('Unhandled rejection:', event.reason);
	});
})();
