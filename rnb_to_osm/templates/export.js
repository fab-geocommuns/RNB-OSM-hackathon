
let currentExportId = null;

async function triggerBBoxExport() {
    const map = window.map;
    const bbox = map.getBounds().toBBoxString().split(',').map(Number);
    await triggerExport({ bbox: bbox });
}

async function triggerCityExport() {
    const citySelect = document.getElementById('citySelect');
    const codeInsee = citySelect.value;
    await triggerExport({ code_insee: codeInsee });
}

function handleResponseError(data) {
    if (data.message && typeof(data.message) === "string") {
        showStatus(data.message, 'error');
        return;
    }

    console.error(data);
    showStatus('Une erreur est survenue', 'error');
}

async function triggerExport(exportParams) {
    const exportButtons = document.getElementsByClassName('exportBtn');

    Array.from(exportButtons).forEach(btn => {
        btn.disabled = true;
        btn.textContent = 'En cours...';
    });
    hideStatus();

    try {
        const response = await fetch('/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(exportParams)
        });

        const data = await response.json();

        if (response.ok) {
            currentExportId = data.export_id;
            pollStatus();
        } else {
            handleResponseError(data);
            resetButton();
        }

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        resetButton();
    }
}

async function pollStatus() {
    const response = await fetch(`/export/${currentExportId}`);
    const data = await response.json();
    if (data.status === 'finished') {
        downloadFile(data);
        resetButton();
        return;
    }

    if (data.status === 'failed') {
        showStatus(`Error: ${data.message}`, 'error');
        resetButton();
        return;
    }

    setTimeout(pollStatus, 5000);
}


function resetButton() {
    const exportButtons = document.getElementsByClassName('exportBtn');
    Array.from(exportButtons).forEach(btn => {
        btn.disabled = false;
        btn.textContent = 'Exporter';
    });
}

function downloadFile({ filename, content }) {
    const blob = new Blob([content], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}

function hideStatus() {
    const statusEls = document.getElementsByClassName('status');
    Array.from(statusEls).forEach(status => {
        status.style.display = 'none';
    });
}

function showStatus(message, type) {
    const statusEls = document.getElementsByClassName('status');
    Array.from(statusEls).forEach(status => {
        status.textContent = message;
        status.className = `status-${type}`;
        status.style.display = 'block';
    });
}