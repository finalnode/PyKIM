"""OSZ-KIM-Theme und Browserverhalten des lokalen Lernstudios."""


def configure_theme(ui) -> None:
    ui.colors(primary="#f36b2b", secondary="#9b9da0", accent="#5f6164")
    ui.add_head_html(r"""
        <style>
            .pykim-skip-link {
                position: fixed; left: 1rem; top: -5rem; z-index: 9999;
                padding: .65rem 1rem; border-radius: .35rem;
                background: #262626; color: white;
            }
            .pykim-skip-link:focus { top: 1rem; }
            :focus-visible {
                outline: 3px solid #1f6feb !important;
                outline-offset: 3px !important;
            }
            .pykim-header {
                display: flex;
                flex-direction: column;
                align-items: stretch;
                padding: 0 !important;
                background: white !important;
                color: #262626 !important;
                box-shadow: 0 2px 7px rgba(38, 38, 38, .14);
            }
            .pykim-header-top {
                min-height: 3.25rem;
                padding: .45rem 1rem;
                margin: 0;
                background: #f36b2b;
                color: white;
            }
            .pykim-main-navigation {
                min-height: 3rem;
                background: white;
                color: #4f5154;
                border-bottom: 1px solid #d7d8d9;
            }
            .pykim-main-navigation .q-tab--active {
                color: #d95316;
                font-weight: 700;
            }
            #pykim-main { scroll-margin-top: 7rem; }
            pre.pykim-copy-ready {
                position: relative;
                padding: 1rem 1.1rem !important;
                background: #f5f5f4 !important;
                border: 1px solid #d7d8d9;
                border-left: 4px solid #f36b2b;
                border-radius: .45rem;
                box-shadow: 0 1px 2px rgba(40, 40, 40, .06);
            }
            pre.pykim-copy-ready.pykim-has-actions {
                padding-right: 12rem !important;
            }
            pre.pykim-copy-ready code {
                background: transparent !important;
            }
            .pykim-copy-button {
                position: absolute; top: .55rem; right: .55rem; z-index: 2;
                border: 0; border-radius: .4rem; padding: .35rem .65rem;
                background: #686a6d; color: white; cursor: pointer;
                font: 500 .8rem system-ui, sans-serif;
            }
            .pykim-copy-button:hover { background: #f36b2b; }
            .pykim-code-run-button {
                position: absolute; top: .55rem; right: 5.7rem; z-index: 2;
                border: 0; border-radius: .4rem; padding: .35rem .65rem;
                background: #f36b2b; color: white; cursor: pointer;
                font: 500 .8rem system-ui, sans-serif;
            }
            .pykim-code-run-button:hover { background: #cf4f18; }
            .pykim-code-run-button:disabled { opacity: .6; cursor: wait; }
            .pykim-code-output {
                margin: -.35rem 0 1rem;
                padding: .65rem .8rem;
                border: 1px solid #d7d8d9;
                border-top: 0;
                border-radius: 0 0 .4rem .4rem;
                background: #272822;
                color: #f5f5f5;
                white-space: pre-wrap;
                font: .85rem/1.45 ui-monospace, SFMono-Regular, Consolas, monospace;
            }
            .pykim-code-options { display: none !important; }
            .pykim-playground textarea {
                width: 100%; min-height: 15rem; padding: 1rem;
                border: 1px solid #cfd0d1; border-left: 4px solid #f36b2b;
                border-radius: .45rem; background: #f5f5f4;
                font: 14px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace;
            }
            .pykim-run-button, .pykim-clear-button {
                border: 0; border-radius: .4rem; padding: .55rem .9rem;
                color: white; cursor: pointer; margin-right: .4rem;
            }
            .pykim-run-button { background: #f36b2b; }
            .pykim-clear-button { background: #686a6d; }
            .pykim-test-result {
                border: 1px solid #d7d8d9;
                border-left-width: 5px;
                border-radius: .45rem;
                box-shadow: none;
            }
            .pykim-test-passed {
                border-left-color: #2e7d32;
                background: #f2f8f3;
            }
            .pykim-test-failed {
                border-left-color: #d14b34;
                background: #fff5f2;
            }
            .pykim-test-hint {
                background: #fff4eb;
                border-left: 3px solid #f36b2b;
                border-radius: .3rem;
                padding: .55rem .75rem;
            }
            .pykim-script-layout {
                display: grid;
                grid-template-columns: 16rem minmax(0, 1fr);
                gap: 1.25rem;
                margin-top: 1rem;
            }
            .pykim-script-menu {
                position: sticky;
                top: 5rem;
                width: 16rem;
                max-height: calc(100vh - 7rem);
                overflow-y: auto;
                border: 1px solid #d7d8d9;
                border-left: 4px solid #f36b2b;
                background: #f8f8f7;
                padding: .8rem;
            }
            .pykim-script-menu-button {
                min-height: 2.4rem;
                padding: .35rem .5rem;
                border-radius: .35rem;
            }
            .pykim-script-menu-button .q-btn__content {
                width: 100%;
                justify-content: flex-start !important;
                text-align: left !important;
                white-space: normal;
                line-height: 1.25;
                font-size: .88rem;
                font-weight: 500;
            }
            .pykim-script-page {
                border: 1px solid #e0e0df;
                border-radius: .5rem;
                padding: 1.5rem;
                background: white;
            }
            .pykim-chapter-markdown {
                color: #262626;
                font-size: 1rem;
                line-height: 1.65;
                max-width: 58rem;
            }
            .pykim-chapter-markdown h1 {
                font-size: 2rem !important;
                line-height: 1.2 !important;
                font-weight: 700 !important;
                margin: 1.25rem 0 1rem !important;
                letter-spacing: -.02em;
            }
            .pykim-chapter-markdown h2 {
                font-size: 1.4rem !important;
                line-height: 1.3 !important;
                font-weight: 700 !important;
                margin: 1.6rem 0 .65rem !important;
            }
            .pykim-chapter-markdown h3 {
                font-size: 1.15rem !important;
                font-weight: 700 !important;
                margin: 1.3rem 0 .5rem !important;
            }
            .pykim-chapter-markdown p {
                margin: .65rem 0;
            }
            .pykim-chapter-markdown table {
                display: block;
                width: max-content;
                max-width: 100%;
                overflow-x: auto;
                margin: 1rem 0;
                border-collapse: collapse;
            }
            .pykim-chapter-markdown th,
            .pykim-chapter-markdown td {
                padding: .5rem .75rem;
                border: 1px solid #d7d8d9;
                text-align: left;
            }
            .pykim-chapter-markdown th { background: #f2f2f1; }
            @media (max-width: 800px) {
                .pykim-course-path { display: none; }
                .pykim-header-top { min-height: 3rem; }
                .pykim-main-navigation .q-tab { min-width: max-content; }
                .pykim-script-layout { grid-template-columns: 1fr; }
                .pykim-script-menu {
                    position: static;
                    width: 100%;
                    max-height: none;
                }
                .pykim-script-page { padding: 1rem; }
                .pykim-chapter-markdown h1 { font-size: 1.65rem !important; }
            }
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    scroll-behavior: auto !important;
                    animation-duration: .01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: .01ms !important;
                }
            }
        </style>
        <script>
            let pyKIMBrowserWorker = null;
            const createPyKIMBrowserWorker = () => {
                const workerSource = `
                    import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.2/full/pyodide.mjs';
                    let runtime = null;
                    self.onmessage = async event => {
                        try {
                            if (!runtime) {
                                self.postMessage({type: 'status', text: 'Python wird im Hintergrund geladen …'});
                                runtime = await loadPyodide();
                                self.postMessage({type: 'status', text: 'Python ist bereit.'});
                            }
                            let output = '';
                            runtime.setStdout({batched: value => output += value + '\\n'});
                            runtime.setStderr({batched: value => output += value + '\\n'});
                            const result = await runtime.runPythonAsync(event.data.code);
                            if (result !== undefined) output += String(result);
                            self.postMessage({type: 'result', text: output || 'Programm ohne Ausgabe beendet.'});
                        } catch (error) {
                            self.postMessage({type: 'error', text: String(error)});
                        }
                    };
                `;
                const url = URL.createObjectURL(new Blob([workerSource], {type: 'text/javascript'}));
                const worker = new Worker(url, {type: 'module'});
                URL.revokeObjectURL(url);
                worker.onmessage = event => {
                    const status = document.getElementById('pyodide-status');
                    const output = document.getElementById('pyodide-output');
                    if (event.data.type === 'status' && status) {
                        status.innerHTML = `<strong>${event.data.text}</strong>`;
                    } else if (event.data.type === 'result' && output) {
                        output.textContent = event.data.text;
                    } else if (event.data.type === 'error' && output) {
                        output.textContent = event.data.text;
                    }
                };
                worker.onerror = event => {
                    const status = document.getElementById('pyodide-status');
                    const output = document.getElementById('pyodide-output');
                    if (status) status.textContent = 'Python im Browser konnte nicht geladen werden.';
                    if (output) output.textContent = event.message || 'Unbekannter Worker-Fehler.';
                    pyKIMBrowserWorker = null;
                };
                return worker;
            };
            window.resetPyKIMBrowserExample = () => {
                const editor = document.getElementById('pyodide-code');
                const output = document.getElementById('pyodide-output');
                if (editor) editor.value = 'for zahl in range(1, 6):\n    print(zahl, zahl * zahl)';
                if (output) output.textContent = 'Bereit.';
            };
            window.runPyKIMPython = async () => {
                const output = document.getElementById('pyodide-output');
                const code = document.getElementById('pyodide-code').value;
                const unsupportedImport = /^\s*(?:from|import)\s+(pykim|pyxel)\b/m.exec(code);
                if (unsupportedImport) {
                    const packageName = unsupportedImport[1] === 'pykim' ? 'PyKIM' : 'Pyxel';
                    output.textContent = `${packageName} läuft nicht in dieser Browser-Spielwiese. `
                        + 'Öffne den Code als Aufgabe oder Projekt und starte ihn mit der lokalen Runtime.';
                    return;
                }
                output.textContent = 'Wird ausgeführt …';
                if (!pyKIMBrowserWorker) pyKIMBrowserWorker = createPyKIMBrowserWorker();
                pyKIMBrowserWorker.postMessage({code});
            };
            window.stopPyKIMBrowserPython = () => {
                if (pyKIMBrowserWorker) {
                    pyKIMBrowserWorker.terminate();
                    pyKIMBrowserWorker = null;
                }
                const status = document.getElementById('pyodide-status');
                const output = document.getElementById('pyodide-output');
                if (status) status.innerHTML = '<strong>Python wird erst beim Ausführen geladen.</strong>';
                if (output) output.textContent = 'Ausführung gestoppt.';
            };
        </script>
        <script>
            (() => {
                const addCopyButtons = root => {
                    root.querySelectorAll('pre:not(.pykim-copy-ready)').forEach(pre => {
                        pre.classList.add('pykim-copy-ready');
                        const pythonCode = pre.querySelector('code');
                        const inScript = Boolean(pre.closest('.pykim-chapter-markdown'));
                        const codeContainer = pre.parentElement?.classList.contains('codehilite')
                            ? pre.parentElement
                            : pre;
                        const markerCandidate = codeContainer.previousElementSibling;
                        const marker = inScript && markerCandidate?.matches(
                            '.pykim-code-options'
                        ) ? markerCandidate : null;
                        const buttons = inScript
                            ? (marker?.dataset.buttons || '').split(',').filter(Boolean)
                            : ['copy'];
                        if (buttons.length) pre.classList.add('pykim-has-actions');

                        if (buttons.includes('copy')) {
                            const button = document.createElement('button');
                            button.className = 'pykim-copy-button';
                            button.type = 'button';
                            button.textContent = 'Kopieren';
                            button.setAttribute('aria-label', 'Code in die Zwischenablage kopieren');
                            button.addEventListener('click', async () => {
                                const text = (pythonCode || pre).innerText;
                                if (navigator.clipboard?.writeText) {
                                    await navigator.clipboard.writeText(text);
                                } else {
                                    const area = document.createElement('textarea');
                                    area.value = text;
                                    area.style.position = 'fixed';
                                    area.style.opacity = '0';
                                    document.body.appendChild(area);
                                    area.select();
                                    document.execCommand('copy');
                                    area.remove();
                                }
                                button.textContent = 'Kopiert ✓';
                                setTimeout(() => button.textContent = 'Kopieren', 1500);
                            });
                            pre.appendChild(button);
                        }

                        if (buttons.includes('run') && pythonCode) {
                            const runButton = document.createElement('button');
                            runButton.className = 'pykim-code-run-button';
                            runButton.type = 'button';
                            runButton.textContent = '▶ Ausführen';
                            runButton.setAttribute('aria-label', 'Python-Code ausführen');
                            runButton.addEventListener('click', async () => {
                                runButton.disabled = true;
                                runButton.textContent = 'Läuft …';
                                let output = pre.nextElementSibling;
                                if (!output?.classList.contains('pykim-code-output')) {
                                    output = document.createElement('div');
                                    output.className = 'pykim-code-output';
                                    pre.insertAdjacentElement('afterend', output);
                                }
                                output.textContent = 'Beispiel wird ausgeführt …';
                                try {
                                    const response = await fetch('/api/script/run', {
                                        method: 'POST',
                                        headers: {'Content-Type': 'application/json'},
                                        body: JSON.stringify({source: pythonCode.innerText}),
                                    });
                                    const started = await response.json();
                                    if (!response.ok) throw new Error(started.detail || 'Ausführung abgelehnt');

                                    let result = null;
                                    while (true) {
                                        const statusResponse = await fetch(
                                            `/api/script/status/${started.job_id}`
                                        );
                                        result = await statusResponse.json();
                                        if (!statusResponse.ok) {
                                            throw new Error(result.detail || 'Status nicht verfügbar');
                                        }
                                        const text = [result.stdout, result.stderr]
                                            .filter(Boolean).join('\n').trim();
                                        output.textContent = text || (
                                            result.running
                                                ? 'Programm läuft …'
                                                : `Programm ohne Ausgabe beendet (Code ${result.returncode}).`
                                        );
                                        output.style.borderLeft = `4px solid ${
                                            result.running ? '#f36b2b' :
                                            result.returncode === 0 ? '#2e7d32' : '#d14b34'
                                        }`;
                                        if (!result.running) break;
                                        await new Promise(resolve => setTimeout(resolve, 150));
                                    }
                                } catch (error) {
                                    output.textContent = `Ausführen fehlgeschlagen: ${error}`;
                                    output.style.borderLeft = '4px solid #d14b34';
                                } finally {
                                    runButton.disabled = false;
                                    runButton.textContent = '▶ Ausführen';
                                }
                            });
                            pre.appendChild(runButton);
                        }
                    });
                };
                document.addEventListener('DOMContentLoaded', () => {
                    addCopyButtons(document);
                    new MutationObserver(() => addCopyButtons(document)).observe(
                        document.body, {childList: true, subtree: true}
                    );
                });
            })();
        </script>
        <script>
            window.pykimHasUnsavedChanges = false;
            window.addEventListener('beforeunload', event => {
                if (window.pykimHasUnsavedChanges) {
                    event.preventDefault();
                    event.returnValue = '';
                }
            });
        </script>
    """)


__all__ = ["configure_theme"]
