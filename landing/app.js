/* Agentic OS Control Plane - Portal Logic. Author: Nicholas Hidalgo */

document.addEventListener('DOMContentLoaded', () => {
  initFolderExplorer();
  initTerminalSimulator();
  initPdfExport();
  initInteractiveDiagrams();
});

/* =========================================
   1. Folder Explorer Interaction
   ========================================= */
function initFolderExplorer() {
  const folders = document.querySelectorAll('.tree-folder');
  
  folders.forEach(folder => {
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

/* =========================================
   2. PDF Export
   ========================================= */
function initPdfExport() {
  const pdfBtn = document.getElementById('btn-export-pdf');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', () => {
      window.print();
    });
  }
}

/* =========================================
   3. Interactive Diagrams Highlights
   ========================================= */
function initInteractiveDiagrams() {
  const nodes = document.querySelectorAll('.svg-node');
  
  nodes.forEach(node => {
    node.addEventListener('mouseenter', () => {
      // Find connected flows and highlight them
      const nodeId = node.id;
      if (nodeId) {
        highlightConnectedFlows(nodeId, true);
      }
    });
    
    node.addEventListener('mouseleave', () => {
      const nodeId = node.id;
      if (nodeId) {
        highlightConnectedFlows(nodeId, false);
      }
    });
  });
}

function highlightConnectedFlows(nodeId, highlight) {
  // Simple check for node names to highlight specific paths
  const flows = document.querySelectorAll('.svg-connection-flow');
  flows.forEach(flow => {
    if (highlight) {
      flow.style.strokeWidth = '4px';
      flow.style.filter = 'drop-shadow(0 0 8px var(--accent-purple))';
    } else {
      flow.style.strokeWidth = '';
      flow.style.filter = '';
    }
  });
}

/* =========================================
   4. Live Terminal execution Simulator
   ========================================= */
const SIMULATION_TIMELINE = [
  // 1. Run a morning brief (Standard Allowed Action)
  {
    cmd: "python control_plane/run_skill.py --skill morning_brief",
    steps: [
      { type: 'output', text: "[INIT]  Initializing Governed Runtime..." },
      { type: 'output', text: "[INFO]  Locating skill 'morning_brief' in registry..." },
      { type: 'output', text: "[LOAD]  Skill loaded: skills/morning_brief/ (Version 0.2)" },
      { type: 'output', text: "[GATE]  Checking action: FILE_READ -> vault/daily/" },
      { type: 'success', text: "[ALLOW] POLICY ALLOW: Action permitted." },
      { type: 'output', text: "[EXEC]  Executing: skills/morning_brief/run.py..." },
      { type: 'output', text: "[WRITE] Writing output: vault/daily/brief_2026-05-20.md" },
      { type: 'output', text: "[GATE]  Validating output path: vault/daily/brief_2026-05-20.md" },
      { type: 'success', text: "[ALLOW] POLICY ALLOW: Path falls inside permitted write prefixes." },
      { type: 'output', text: "[AUDIT] Writing append-only audit record..." },
      { type: 'success', text: "[AUDIT] AUDIT LOGGED: RUN-20260520-123456 -> Success." }
    ]
  },
  
  // 2. Trigger Policy Gate & Human Approval Workflow
  {
    cmd: "python control_plane/run_skill.py --skill vault_cleanup --input out-of-bounds/restricted.md",
    steps: [
      { type: 'output', text: "[INIT]  Initializing Governed Runtime..." },
      { type: 'output', text: "[INFO]  Locating skill 'vault_cleanup' in registry..." },
      { type: 'output', text: "[LOAD]  Skill loaded: skills/vault_cleanup/ (Version 0.1)" },
      { type: 'output', text: "[GATE]  Checking action: FILE_WRITE -> out-of-bounds/restricted.md" },
      { type: 'alert', text: "[WARN]  POLICY GATE TRIGGERED: REQUIRE_APPROVAL\n   approval_id: APR-20260520-8c2e1f\n   reason:      Target write path is outside allowed prefixes.\n   action:      FILE_WRITE -> out-of-bounds/restricted.md\n\n[INFO]  Awaiting Human Operator approval..." },
      { type: 'pause', duration: 4000 },
      { type: 'cmd_instant', text: "python control_plane/run_skill.py --approvals approve APR-20260520-8c2e1f" },
      { type: 'success', text: "[OK]    APPROVAL GRANTED: Operator approved approval_id 'APR-20260520-8c2e1f'." },
      { type: 'output', text: "[EXEC]  Resuming execution of 'vault_cleanup'..." },
      { type: 'output', text: "[WRITE] Writing output: out-of-bounds/restricted.md" },
      { type: 'output', text: "[GATE]  Validating output path: out-of-bounds/restricted.md" },
      { type: 'success', text: "[ALLOW] POLICY ALLOW: Path bypass approved by human override." },
      { type: 'output', text: "[AUDIT] Writing append-only audit record..." },
      { type: 'success', text: "[AUDIT] AUDIT LOGGED: RUN-20260520-123457 -> Success (Approved Bypass)." }
    ]
  },
  
  // 3. Denied Action outright
  {
    cmd: "python control_plane/run_skill.py --skill morning_brief --input control_plane/policy.py",
    steps: [
      { type: 'output', text: "[INIT]  Initializing Governed Runtime..." },
      { type: 'output', text: "[INFO]  Locating skill 'morning_brief' in registry..." },
      { type: 'output', text: "[LOAD]  Skill loaded: skills/morning_brief/ (Version 0.2)" },
      { type: 'output', text: "[GATE]  Checking action: FILE_WRITE -> control_plane/policy.py" },
      { type: 'error', text: "[DENY]  POLICY VIOLATION DENIED: FILE_WRITE -> control_plane/policy.py\n   reason: Modifying core control plane runtime modules is strictly prohibited." },
      { type: 'output', text: "[AUDIT] Writing append-only audit record..." },
      { type: 'error', text: "[AUDIT] AUDIT LOGGED: RUN-20260520-123458 -> FAILED (Policy Deny)." }
    ]
  }
];

async function initTerminalSimulator() {
  const terminal = document.getElementById('terminal-mount');
  if (!terminal) return;
  
  while (true) { // Loop infinitely
    for (let scene of SIMULATION_TIMELINE) {
      terminal.innerHTML = ''; // Clear terminal
      
      // Render prompt and start typing command
      const line = document.createElement('div');
      line.className = 'terminal-row';
      line.innerHTML = `<span class="terminal-prompt">nick@hidalgo-os %</span><span class="terminal-cmd"></span><span class="terminal-cursor"></span>`;
      terminal.appendChild(line);
      
      const cmdSpan = line.querySelector('.terminal-cmd');
      const cursor = line.querySelector('.terminal-cursor');
      
      await typeCommand(cmdSpan, scene.cmd);
      cursor.style.display = 'none'; // Hide active typing cursor
      
      // Execute command steps
      for (let step of scene.steps) {
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
      
      await sleep(5000); // Hold final output before next command
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
    }, 50); // Typing speed
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
