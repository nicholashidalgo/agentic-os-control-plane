/* Agentic OS Control Plane - Portal Logic */

document.addEventListener('DOMContentLoaded', () => {
  initFolderExplorer();
  initTerminalSimulator();
  initPdfExport();
  initInteractiveDiagrams();
});

function initFolderExplorer() {
  const folders = document.querySelectorAll('.tree-folder');

  folders.forEach((folder) => {
    folder.addEventListener('click', (e) => {
      e.stopPropagation();
      const subtree = folder.nextElementSibling;
      if (subtree && subtree.classList.contains('tree-subtree')) {
        const isCollapsed = subtree.classList.toggle('collapsed');
        folder.classList.toggle('expanded', !isCollapsed);
      }
    });
  });
}

function initPdfExport() {
  const pdfBtn = document.getElementById('btn-export-pdf');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', () => {
      window.print();
    });
  }
}

function initInteractiveDiagrams() {
  const nodes = document.querySelectorAll('.svg-node');

  nodes.forEach((node) => {
    node.addEventListener('mouseenter', () => {
      const nodeId = node.id;
      if (nodeId) {
        highlightConnectedFlows(true);
      }
    });

    node.addEventListener('mouseleave', () => {
      const nodeId = node.id;
      if (nodeId) {
        highlightConnectedFlows(false);
      }
    });
  });
}

function highlightConnectedFlows(highlight) {
  const flows = document.querySelectorAll('.svg-connection-flow');
  flows.forEach((flow) => {
    if (highlight) {
      flow.style.strokeWidth = '4px';
      flow.style.filter = 'drop-shadow(0 0 8px var(--accent-purple))';
    } else {
      flow.style.strokeWidth = '';
      flow.style.filter = '';
    }
  });
}

const SIMULATION_TIMELINE = [
  {
    cmd: 'agentic-os run morning_brief',
    steps: [
      { type: 'output', text: '[INIT]  Initializing governed runtime...' },
      { type: 'output', text: "[INFO]  Locating skill 'morning_brief' in registry..." },
      { type: 'output', text: '[LOAD]  Skill loaded: skills/morning_brief/' },
      { type: 'output', text: '[GATE]  Checking action: FILE_READ -> vault/daily/' },
      { type: 'success', text: '[ALLOW] Policy allow: action permitted.' },
      { type: 'output', text: '[EXEC]  Executing skill...' },
      { type: 'output', text: '[WRITE] Writing output: vault/daily/brief_2026-05-20.md' },
      { type: 'output', text: '[AUDIT] Appending run record...' },
      { type: 'success', text: '[AUDIT] RUN-20260520-123456 logged as success.' }
    ]
  },
  {
    cmd: 'agentic-os approvals list --status pending',
    steps: [
      { type: 'output', text: '[QUEUE]  Reading approval ledger...' },
      { type: 'alert', text: 'APR-20260520-8c2e1f  pending     skill=vault_cleanup  action=file_write  path=out-of-bounds/restricted.md' },
      { type: 'pause', duration: 2000 },
      { type: 'cmd_instant', text: 'agentic-os approvals approve APR-20260520-8c2e1f' },
      { type: 'success', text: '[OK]    Approval resolved: APR-20260520-8c2e1f -> approved' },
      { type: 'output', text: '[AUDIT] Approval transition appended to approvals.jsonl' }
    ]
  },
  {
    cmd: 'agentic-os run policy_simulator --input vault/raw/sample_action_manifest.json',
    steps: [
      { type: 'output', text: '[INIT]  Initializing governed runtime...' },
      { type: 'output', text: '[INFO]  Loading proposed actions from sample manifest...' },
      { type: 'output', text: '[SIM]   Evaluating policy outcomes without execution...' },
      { type: 'output', text: '[SIM]   ALLOW=file_read -> vault/raw/note.md' },
      { type: 'output', text: '[SIM]   REQUIRE_APPROVAL=git_commit' },
      { type: 'error', text: '[SIM]   DENY=file_write -> protected surface' },
      { type: 'output', text: '[AUDIT] Appending run record...' },
      { type: 'success', text: '[AUDIT] RUN-20260520-123458 logged as success.' }
    ]
  }
];

async function initTerminalSimulator() {
  const terminal = document.getElementById('terminal-mount');
  if (!terminal) return;

  while (true) {
    for (const scene of SIMULATION_TIMELINE) {
      terminal.innerHTML = '';

      const line = document.createElement('div');
      line.className = 'terminal-row';
      line.innerHTML = '<span class="terminal-prompt">operator@control-plane %</span><span class="terminal-cmd"></span><span class="terminal-cursor"></span>';
      terminal.appendChild(line);

      const cmdSpan = line.querySelector('.terminal-cmd');
      const cursor = line.querySelector('.terminal-cursor');

      await typeCommand(cmdSpan, scene.cmd);
      cursor.style.display = 'none';

      for (const step of scene.steps) {
        await sleep(600);

        if (step.type === 'pause') {
          await sleep(step.duration);
          continue;
        }

        if (step.type === 'cmd_instant') {
          const instantLine = document.createElement('div');
          instantLine.className = 'terminal-row';
          instantLine.innerHTML = `<span class="terminal-prompt">operator@control-plane %</span><span class="terminal-cmd">${step.text}</span>`;
          terminal.appendChild(instantLine);
          continue;
        }

        const outputLine = document.createElement('div');
        outputLine.className = 'terminal-row';

        if (step.type === 'output') {
          outputLine.innerHTML = `<span class="terminal-output">${step.text}</span>`;
        } else if (step.type === 'success') {
          outputLine.innerHTML = `<div class="terminal-output-success">${step.text}</div>`;
        } else if (step.type === 'alert') {
          outputLine.innerHTML = `<div class="terminal-output-alert">${step.text}</div>`;
        } else if (step.type === 'error') {
          outputLine.innerHTML = `<div class="terminal-output-alert" style="border-left-color:#ef4444; background-color:rgba(239,68,68,0.08); color:#fca5a5;">${step.text}</div>`;
        }

        terminal.appendChild(outputLine);
        terminal.scrollTop = terminal.scrollHeight;
      }

      await sleep(5000);
    }
  }
}

function typeCommand(element, text) {
  return new Promise((resolve) => {
    let index = 0;
    const interval = setInterval(() => {
      if (index < text.length) {
        element.textContent += text.charAt(index);
        index++;
      } else {
        clearInterval(interval);
        resolve();
      }
    }, 50);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
