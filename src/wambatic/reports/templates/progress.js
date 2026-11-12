(function () {
  'use strict';
  const data = JSON.parse(document.getElementById('progress-data').textContent);

  // The addresses are built here from the job id and this page's own query, so nothing in the
  // embedded data can send the page elsewhere.
  const jobId = String(data.job);
  const jobQuery =
    'query($id: ID!) { job(id: $id) { state reposListed reposPending reposDone rowsWritten error status } }';
  const query = new URLSearchParams(location.search);
  query.set('job', jobId);
  const reloadPath = '/report?' + query.toString();
  const stateElement = document.getElementById('state');
  const countsElement = document.getElementById('counts');
  const errorElement = document.getElementById('error');
  const retryElement = document.getElementById('retry');
  const labels = {
    QUEUED: 'Waiting for another sync to finish',
    LISTING: 'Listing repositories',
    SYNCING: 'Syncing repositories',
    DONE: 'Done, loading the report',
    FAILED: 'The sync failed',
  };

  function fail(message) {
    errorElement.textContent = message;
    errorElement.hidden = false;
    retryElement.hidden = false;
  }

  function show(job) {
    stateElement.textContent = labels[job.state] || job.state;
    if (job.reposPending !== null) {
      const rows = job.rowsWritten === null ? 0 : job.rowsWritten;
      countsElement.textContent =
        job.reposDone + ' of ' + job.reposPending + ' repositories synced of ' +
        job.reposListed + ' listed, ' + rows + ' rows written';
    } else if (job.reposListed !== null) {
      countsElement.textContent = job.reposListed + ' repositories listed';
    }
  }

  async function poll() {
    try {
      const response = await fetch('/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
        body: JSON.stringify({ query: jobQuery, variables: { id: jobId } }),
      });
      const body = await response.json();
      if (!response.ok || body.errors || !body.data || body.data.job === null) {
        stateElement.textContent = 'The sync cannot be followed';
        const first = body.errors && body.errors[0];
        fail((first && first.message) || body.error || 'no such job');
        return;
      }
      const job = body.data.job;
      show(job);
      if (job.state === 'DONE') {
        location.replace(reloadPath);
        return;
      }
      if (job.state === 'FAILED') {
        fail(job.error);
        return;
      }
    } catch (error) {
      stateElement.textContent = 'Cannot reach the server, trying again';
    }
    setTimeout(poll, 1000);
  }

  poll();
})();
