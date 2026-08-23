const API = 'http://127.0.0.1:8787';

function esc(value) {
  return String(value ?? '').replace(/[&<>\"']/g, function (c) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c];
  });
}

function evidence(report, kind) {
  return (report && Array.isArray(report.evidence) ? report.evidence : []).find(function (item) {
    return item.kind === kind;
  });
}

function check(ok, title, meaning, detail) {
  var cls = ok === true ? 'ok' : ok === false ? 'bad' : 'unknown';
  var mark = ok === true ? '✓' : ok === false ? '!' : '–';
  var label = ok === true ? 'Verified' : ok === false ? 'Not verified' : 'Not reached';
  return '<div class="check ' + cls + '"><div class="dot">' + mark + '</div><div><b>' + esc(title) + '</b><p>' + esc(meaning) + '</p>' + (detail ? '<p>' + esc(detail) + '</p>' : '') + '</div><div class="state">' + label + '</div></div>';
}

function render(job) {
  var result = document.getElementById('result');
  if (!result) return;
  result.classList.add('show');

  if (job.error) {
    result.className = 'card result show reject';
    result.innerHTML = '<div class="verdict red">Run failed</div><div class="muted">PatchProof could not complete the verification run.</div><div class="plain"><b>What happened:</b> ' + esc(job.error) + '</div>';
    return;
  }

  var report = job.report;
  if (!report) {
    result.className = 'card result show';
    result.innerHTML = '<div class="verdict blue">' + esc(job.status || 'Running') + '</div><div class="muted">The agent is working. This page will update automatically.</div>';
    return;
  }

  var a = evidence(report, 'patch-application');
  var t = evidence(report, 'tests');
  var pf = evidence(report, 'protected-files');
  var h = evidence(report, 'file-hashes');
  var av = a && a.value ? a.value : {};
  var tv = t && t.value ? t.value : {};
  var pv = pf && pf.value ? pf.value : {};
  var hv = h && h.value ? h.value : {};
  var patchOk = a ? (av.applied_matches_proposal === true || av.matches_proposed === true) : null;
  var testsOk = t ? (tv.exit_code === 0 && tv.failed === 0) : null;
  var protectedOk = pf ? pv.unchanged === true : null;
  var hashOk = h ? Object.keys(hv.before || {}).length > 0 : null;
  var anchor = report.ethereum_anchor;

  result.className = 'card result show ' + (report.accepted ? 'accept' : 'reject');
  var html = '<div class="verdict ' + (report.accepted ? 'green' : 'red') + '">' + (report.accepted ? 'Verified' : 'Rejected') + '</div>';
  html += '<div class="muted">' + (report.accepted ? 'The repository produced enough independent evidence to accept the result.' : 'PatchProof could not prove the requested result.') + '</div>';
  html += '<div class="plain"><b>In plain English:</b> ' + (report.accepted ? 'The proposed change matches what was actually applied, protected files stayed unchanged, and the independent tests passed.' : 'At least one independent check disagreed with the requested result. Rejection means the evidence was insufficient or contradictory; the model does not get to decide the verdict.') + '</div>';
  html += '<div class="checks">';
  html += check(!!a, 'The proposed patch was observed', 'PatchProof recorded the change the agent asked to make.');
  html += check(hashOk, 'The repository state was measured', 'Before/after file hashes provide an independent record of what changed.');
  html += check(protectedOk, 'Protected files stayed unchanged', 'Tests and protected runtime/toolchain paths were not modified.');
  html += check(patchOk, 'The applied files match the proposal', 'The actual filesystem state matches the model\'s proposed content.');
  html += check(testsOk, 'The tests passed independently', 'The test command was run against the resulting repository.', t ? 'Exit code: ' + (tv.exit_code ?? 'unknown') + '; passed: ' + (tv.passed ?? 'unknown') + '; failed: ' + (tv.failed ?? 'unknown') : '');
  html += '</div>';

  if (anchor) {
    var anchorFailed = anchor.status === 'failed' || !anchor.transaction_hash;
    html += '<div class="anchor"><h4>Ethereum proof anchor</h4><p>This transaction records the SHA-256 commitment of this proof package on Ethereum. The blockchain is a timestamped notary here; it does not decide whether the code is correct.</p>';
    if (!anchorFailed) {
      html += '<p><b>Confirmed on ' + esc(anchor.network || 'Ethereum') + '</b>' + (anchor.block_number != null ? ' in block ' + esc(anchor.block_number) : '') + '.</p>';
      html += '<code>' + esc(anchor.transaction_hash) + '</code>';
      if (anchor.explorer_url) html += '<a href="' + esc(anchor.explorer_url) + '" target="_blank" rel="noreferrer">View transaction ↗</a>';
    } else {
      html += '<p>Anchoring failed: ' + esc(anchor.error || 'unknown Ethereum error') + '</p>';
    }
    html += '</div>';
  } else {
    html += '<div class="anchor"><h4>Ethereum proof anchor</h4><p>Not configured. Verification still works locally. Configure the Ethereum RPC, signer, and deployed PatchProofAnchor contract to publish commitments.</p></div>';
  }

  html += '<div class="evidence"><h4>Evidence details</h4>';
  (report.evidence || []).forEach(function (item) {
    html += '<details><summary>' + esc(item.kind) + '</summary><pre>' + esc(JSON.stringify(item.value, null, 2)) + '</pre></details>';
  });
  html += '</div>';
  result.innerHTML = html;
}

async function poll(id) {
  for (var i = 0; i < 180; i++) {
    var response = await fetch(API + '/jobs/' + encodeURIComponent(id));
    var job = await response.json();
    render(job);
    if (job.status === 'accepted' || job.status === 'rejected' || job.status === 'failed') return;
    await new Promise(function (resolve) { setTimeout(resolve, 1000); });
  }
}

async function startRun() {
  var run = document.getElementById('run');
  var task = document.getElementById('task').value.trim();
  var repo = document.getElementById('repo').value.trim();
  if (!task || !repo) return;
  run.disabled = true;
  run.textContent = 'Running…';
  render({status: 'running'});
  try {
    var createdResponse = await fetch(API + '/jobs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({task:task, repo:repo})});
    if (!createdResponse.ok) throw new Error('Could not create job (' + createdResponse.status + ')');
    var job = await createdResponse.json();
    var startResponse = await fetch(API + '/jobs/' + encodeURIComponent(job.id) + '/run', {method:'POST'});
    if (!startResponse.ok) throw new Error('Could not start job (' + startResponse.status + ')');
    await poll(job.id);
  } catch (error) {
    render({error:error.message || String(error)});
  } finally {
    run.disabled = false;
    run.textContent = 'Run verification';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  var run = document.getElementById('run');
  if (!run) return;
  run.addEventListener('click', startRun);
});
